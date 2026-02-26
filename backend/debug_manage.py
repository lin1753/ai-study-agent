import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def debug_manage():
    # 1. Create a space
    print("Creating space...")
    try:
        resp = requests.post(f"{BASE_URL}/spaces", json={"name": "To Delete"})
        resp.raise_for_status()
        space_id = resp.json()["id"]
        print(f"Created space: {space_id}")
    except Exception as e:
        print(f"Create failed: {e}")
        return

    # 2. Rename space
    print(f"Renaming space {space_id}...")
    try:
        resp = requests.put(f"{BASE_URL}/spaces/{space_id}", json={"name": "Renamed Space"})
        if resp.status_code == 200:
            print("Rename Success:", resp.json())
        else:
            print(f"Rename Failed: {resp.status_code}, {resp.text}")
    except Exception as e:
        print(f"Rename Request Error: {e}")

    # 3. Delete space
    print(f"Deleting space {space_id}...")
    try:
        resp = requests.delete(f"{BASE_URL}/spaces/{space_id}")
        if resp.status_code == 200:
            print("Delete Success:", resp.json())
        else:
            print(f"Delete Failed: {resp.status_code}, {resp.text}")
    except Exception as e:
        print(f"Delete Request Error: {e}")

if __name__ == "__main__":
    debug_manage()
