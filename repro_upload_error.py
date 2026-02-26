
import requests
import os

SPACE_ID = "354b37582ce64096b0fb9ff558b8e556"
FILE_PATH = "backend/uploads/354b37582ce64096b0fb9ff558b8e556_网安复习课.pdf" # This might already exist or I need a new one

def test_upload():
    # If file doesn't exist, we can't test directly this way, 
    # but we can try to see if the server fails on a small PDF first.
    url = f"http://127.0.0.1:8000/spaces/{SPACE_ID}/upload"
    
    # Create a dummy PDF if needed or use existing
    dummy_pdf = "test_debug.pdf"
    with open(dummy_pdf, "wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<< /Title (Test) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF")
    
    files = {'file': open(dummy_pdf, 'rb')}
    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_upload()
