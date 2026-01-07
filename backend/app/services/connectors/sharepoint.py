from typing import List, BinaryIO, AsyncGenerator
from datetime import datetime
import io
import os
import httpx
from azure.identity import ClientSecretCredential
from .base import DocumentConnector, DocumentMetadata

class SharePointConnector(DocumentConnector):
    def __init__(self):
        self.client_id = os.getenv("AZURE_AD_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_AD_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_AD_TENANT_ID")
        self.site_url = os.getenv("SHAREPOINT_SITE_URL")
        self.token = None

    async def _get_token(self):
        if not self.token:
            cred = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            # Scope for Graph API
            token_obj = cred.get_token("https://graph.microsoft.com/.default")
            self.token = token_obj.token
        return self.token

    async def _get_site_id(self, client: httpx.AsyncClient):
        # site_url format: https://domain.sharepoint.com/sites/SiteName
        # Graph API: GET /sites/{hostname}:/{server-relative-path}
        if not self.site_url:
            raise ValueError("SharePoint Site URL is missing")
        
        parts = self.site_url.replace("https://", "").split("/")
        hostname = parts[0]
        site_path = "/".join(parts[1:])
        
        url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:/{site_path}"
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()["id"]

    async def list_documents(self) -> AsyncGenerator[DocumentMetadata, None]:
        if not self.client_id or not self.client_secret or not self.site_url:
            print("SharePoint credentials incomplete.")
            return

        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            async with httpx.AsyncClient(headers=headers) as client:
                site_id = await self._get_site_id(client)
                
                # Get ALL Drives (Document Libraries)
                drives_resp = await client.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives")
                drives_resp.raise_for_status()
                drives = drives_resp.json().get("value", [])
                
                print(f"Found {len(drives)} drives/libraries in site.")
                
                for drive in drives:
                    drive_id = drive["id"]
                    drive_name = drive["name"]
                    print(f"Scanning Drive: {drive_name} ({drive_id})")
                    
                    folders_to_scan = [("root", f"/{drive_name}/")]
                    
                    while folders_to_scan:
                        current_id, current_path = folders_to_scan.pop(0)
                        
                        if current_id == "root":
                            endpoint = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
                        else:
                            endpoint = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{current_id}/children"
                        
                        resp = await client.get(endpoint)
                        if resp.status_code != 200:
                             print(f"Error scanning folder {current_path}: {resp.status_code}")
                             continue
                             
                        items = resp.json().get("value", [])
                        print(f"Scanned {current_path}: {len(items)} items found.")
                        
                        for item in items:
                            if "folder" in item:
                                print(f"Found folder: {item['name']}")
                                folders_to_scan.append((item["id"], f"{current_path}{item['name']}/"))
                            elif "file" in item:
                                 print(f"Found file: {item['name']}")
                                 yield DocumentMetadata(
                                    source_id=f"{drive_id}:{item['id']}",
                                    title=item["name"],
                                    source_url=item["webUrl"],
                                    created_at=datetime.strptime(item["createdDateTime"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f") if "." in item["createdDateTime"] else datetime.strptime(item["createdDateTime"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S"),
                                    updated_at=datetime.strptime(item["lastModifiedDateTime"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f") if "." in item["lastModifiedDateTime"] else datetime.strptime(item["lastModifiedDateTime"].replace("Z", ""), "%Y-%m-%dT%H:%M:%S"),
                                    file_type=self._map_mime_type(item["file"]["mimeType"])
                                )

        except Exception as e:
            print(f"Error listing SharePoint documents: {e}")
            return

    def _map_mime_type(self, mime_type: str) -> str:
        mime_map = {
            "application/pdf": "pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "application/msword": "doc",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
            "application/vnd.ms-excel": "xls",
            "text/plain": "txt"
        }
        return mime_map.get(mime_type, "unknown")

    async def get_document_content(self, source_id: str) -> BinaryIO:
        try:
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            # We expect source_id to be "drive_id:item_id"
            if ":" in source_id:
                drive_id, item_id = source_id.split(":", 1)
            else:
                # Fallback for legacy or if format changes (assume default drive? No, unsafe. Just error or try)
                # For safety, let's assume it IS the item_id and try to fetch from default drive (legacy behavior)
                # But better to just fail or we'd need to fetch default drive ID every time.
                # Let's implement the fallback to default drive for robustness
                print(f"Warning: source_id {source_id} does not contain drive_id. Attempting default drive.")
                async with httpx.AsyncClient(headers=headers) as client:
                    site_id = await self._get_site_id(client)
                    drive_resp = await client.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive")
                    drive_id = drive_resp.json()["id"]
                    item_id = source_id
            
            async with httpx.AsyncClient(headers=headers) as client:
                 # Download content
                 # GET /drives/{drive-id}/items/{item-id}/content
                 url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
                 resp = await client.get(url, follow_redirects=True)
                 resp.raise_for_status()
                 
                 return io.BytesIO(resp.content)
                 
        except Exception as e:
            print(f"Error downloading SharePoint document {source_id}: {e}")
            return io.BytesIO(b"")
