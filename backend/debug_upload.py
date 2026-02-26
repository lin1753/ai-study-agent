import requests
import os

BASE_URL = "http://127.0.0.1:8000"

def debug_upload():
    # 1. Create Space
    print("Creating space...")
    try:
        resp = requests.post(f"{BASE_URL}/spaces", json={"name": "DebugSpace"})
        resp.raise_for_status()
        space_id = resp.json()["id"]
        print(f"Space created: {space_id}")
    except Exception as e:
        print(f"Failed to create space: {e}")
        return

    # 2. Create Dummy PDF
    filename = "test_upload.pdf"
    with open(filename, "wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 <<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 100 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000256 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n356\n%%EOF")
    
    # 3. Upload
    print(f"Uploading {filename}...")
    try:
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "application/pdf")}
            resp = requests.post(f"{BASE_URL}/spaces/{space_id}/upload", files=files)
        
        if resp.status_code == 200:
            print("Upload Success:", resp.json())
        else:
            print(f"Upload Failed: {resp.status_code}")
            print("Response:", resp.text)
            
    except Exception as e:
        print(f"Request Error: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    debug_upload()
