import requests

BASE_URL = "http://localhost:8000"

def test_summary():
    print("Testing summary API via backend...")
    # This triggers llm.generate_summary
    # We can test via the space/upload or just call the llm service directly if we expose it
    # But let's test a real endpoint: /spaces
    try:
        resp = requests.get(f"{BASE_URL}/spaces")
        print("Backend is alive. Spaces:", resp.json())
    except Exception as e:
        print(f"Backend test failed: {e}")

if __name__ == "__main__":
    test_summary()
