import requests
import json

try:
    print("Testing /api/admin/documents...")
    response = requests.get("http://localhost:8000/api/admin/documents", timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        docs = response.json()
        print(f"Count: {len(docs)}")
        if len(docs) > 0:
            print(f"Sample: {json.dumps(docs[0], indent=2)}")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
