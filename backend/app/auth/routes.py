"""
Entra ID SSO auth routes for ActureAdvisor.
Mirrors @acture/auth (Node.js) flow using MSAL Python.
"""
import secrets
import httpx
import msal
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Group-to-role mapping (matches @acture/auth DEFAULT_GROUP_ROLE_MAP)
GROUP_ROLE_MAP = {
    "55f59d18-d5ef-4995-988c-ef07a89c606f": "platform:admin",
    "8319bdbe-e61f-4c3a-ad1f-2698e2962a20": "platform:manager",
    "c39fcfb3-ac91-4c01-8ba1-b6b83e7e96cf": "platform:user",
}

ROLE_HIERARCHY = {
    "platform:admin": 3,
    "platform:manager": 2,
    "platform:user": 1,
}

SCOPES = ["User.Read"]


def _get_msal_app() -> msal.ConfidentialClientApplication:
    authority = f"https://login.microsoftonline.com/{settings.AZURE_AD_TENANT_ID}"
    return msal.ConfidentialClientApplication(
        client_id=settings.PLATFORM_CLIENT_ID,
        client_credential=settings.PLATFORM_CLIENT_SECRET,
        authority=authority,
    )


def _map_groups_to_role(groups: list[str]) -> str:
    if not groups:
        return "platform:user"
    highest_role = "platform:user"
    highest_level = 1
    for group_id in groups:
        role = GROUP_ROLE_MAP.get(group_id)
        if role and ROLE_HIERARCHY.get(role, 0) > highest_level:
            highest_level = ROLE_HIERARCHY[role]
            highest_role = role
    return highest_role


@router.get("/login")
async def login(request: Request, returnTo: str = "/"):
    """Redirect to Entra ID authorize endpoint."""
    msal_app = _get_msal_app()
    state = secrets.token_hex(16)
    request.session["auth_state"] = state
    request.session["return_to"] = returnTo

    flow = msal_app.initiate_auth_code_flow(
        scopes=SCOPES,
        redirect_uri=settings.PLATFORM_REDIRECT_URI,
        state=state,
    )
    request.session["auth_flow"] = flow
    return RedirectResponse(url=flow["auth_uri"])


@router.get("/callback")
async def callback(request: Request):
    """Exchange code for tokens, establish session, upsert user profile."""
    flow = request.session.get("auth_flow")
    if not flow:
        return RedirectResponse(url="/auth/login")

    msal_app = _get_msal_app()
    result = msal_app.acquire_token_by_auth_code_flow(
        flow,
        dict(request.query_params),
    )

    if "error" in result:
        return RedirectResponse(url="/auth/login")

    id_token_claims = result.get("id_token_claims", {})

    # Extract groups (or fetch from Graph if overage)
    groups = id_token_claims.get("groups", [])
    has_overage = "_claim_names" in id_token_claims and "groups" in id_token_claims.get("_claim_names", {})

    if has_overage and "access_token" in result:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://graph.microsoft.com/v1.0/me/memberOf",
                    headers={"Authorization": f"Bearer {result['access_token']}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    groups = [
                        item["id"]
                        for item in data.get("value", [])
                        if item.get("@odata.type") == "#microsoft.graph.group"
                    ]
        except Exception:
            groups = []

    platform_role = _map_groups_to_role(groups)

    user_profile = {
        "entra_id": id_token_claims.get("oid") or id_token_claims.get("sub"),
        "email": id_token_claims.get("preferred_username") or id_token_claims.get("email"),
        "display_name": id_token_claims.get("name", ""),
        "platform_role": platform_role,
        "groups": groups,
    }

    # Upsert user via User Profile Service
    if settings.USER_PROFILE_SERVICE_URL:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.USER_PROFILE_SERVICE_URL}/api/users/upsert",
                    json=user_profile,
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    full_profile = resp.json()
                    user_profile.update(full_profile)
        except Exception:
            pass  # Non-fatal: user can still use the app

    # Set session
    request.session["user"] = user_profile
    # Clean up auth flow data
    request.session.pop("auth_flow", None)
    request.session.pop("auth_state", None)

    return_to = request.session.pop("return_to", "/")
    return RedirectResponse(url=return_to)


@router.get("/logout")
async def logout(request: Request):
    """Destroy session and redirect to Entra ID logout."""
    request.session.clear()
    post_logout_uri = f"https://advisor.acture.ai"
    logout_url = (
        f"https://login.microsoftonline.com/{settings.AZURE_AD_TENANT_ID}"
        f"/oauth2/v2.0/logout?post_logout_redirect_uri={post_logout_uri}"
    )
    return RedirectResponse(url=logout_url)


@router.get("/me")
async def me(request: Request):
    """Return current user profile from session."""
    user = request.session.get("user")
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}
