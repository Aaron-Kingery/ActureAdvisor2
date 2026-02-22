"""
Auth dependencies for FastAPI route protection.
"""
from fastapi import Request, HTTPException


async def require_auth(request: Request) -> dict:
    """
    Dependency that checks for an authenticated session.
    Returns the user profile dict or raises 401.
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_role(role: str):
    """
    Factory returning a dependency that checks for a minimum role level.
    """
    ROLE_HIERARCHY = {
        "platform:admin": 3,
        "platform:manager": 2,
        "platform:user": 1,
    }

    async def _check_role(request: Request) -> dict:
        user = request.session.get("user")
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        user_level = ROLE_HIERARCHY.get(user.get("platform_role", ""), 0)
        required_level = ROLE_HIERARCHY.get(role, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {role}",
            )
        return user

    return _check_role
