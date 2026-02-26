import requests
import base64
import os

def test_vision():
    # Create a tiny 1x1 black pixel image (PNG)
    pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x00\x00\x00\x00:o\x11\r\x00\x00\x00\nIDATx\x9cc\x00\x00\x00\x02\x00\x01\xe5\x89\xed\xfc\x00\x00\x00\x00IEND\xaeB`\x82'
    b64_img = base64.b64encode(pixel).decode('utf-8')
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen3-vl:4b",
        "prompt": "What's in this image?",
        "images": [b64_img],
        "stream": False
    }
    
    print("Testing qwen3-vl:4b...")
    try:
        resp = requests.post(url, json=payload, timeout=20)
        resp.raise_for_status()
        print("Response:", resp.json().get("response"))
    except Exception as e:
        print(f"Vision test failed: {e}")

if __name__ == "__main__":
    test_vision()
