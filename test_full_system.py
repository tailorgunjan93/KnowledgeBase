import requests
import uuid
import time
import os

API_BASE = "http://localhost:8000"
USERNAME = f"testuser_{uuid.uuid4().hex[:6]}"
PASSWORD = "password123"

def test_full_flow():
    print(f"--- Starting Full System Test for User: {USERNAME} ---")
    
    # 1. Signup / Login
    print("\n1. Testing Authentication...")
    res = requests.post(f"{API_BASE}/auth/signup", json={"username": USERNAME, "password": PASSWORD})
    if res.status_code != 200:
        # print(f"Signup failed, trying login: {res.text}")
        res = requests.post(f"{API_BASE}/auth/login", json={"username": USERNAME, "password": PASSWORD})
    
    assert res.status_code == 200, f"Auth failed: {res.text}"
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("SUCCESS: Authenticated.")

    # 1.5 Set API Key in Settings (bypass potential .env issues)
    print("\n1.5 Setting API Key in user settings...")
    # Get API key from current environment if available
    env_api_key = os.getenv("GROQ_API_KEY", "")
    if not env_api_key:
        print("WARNING: GROQ_API_KEY not found in environment. Tests may fail.")
    requests.post(f"{API_BASE}/settings?key=groq_api_key&value={env_api_key}", headers=headers)
    print("SUCCESS: API Key set.")

    # 2. Chat Test (Simplified Chat)
    print("\n2. Testing Simple Chat...")
    # Hit the /api/chat endpoint
    chat_payload = {
        "message": "Hello, who are you? Please reply in one sentence.",
        "enable_web_search": False
    }
    res = requests.post(f"{API_BASE}/api/chat", headers=headers, json=chat_payload)
    
    if res.status_code == 200:
        print(f"SUCCESS: Chat responded with: {res.json().get('response')[:100]}...")
    else:
        print(f"FAILED: Chat error ({res.status_code}): {res.text}")
        # If it says No module named 'src.core.services.groq_service', it failed our previous fix check.

    # 3. Knowledge Base Test
    print("\n3. Testing Knowledge Base...")
    # Create KB
    res = requests.post(f"{API_BASE}/api/kb", headers=headers, json={"name": "Test KB", "description": "Testing uploads"})
    assert res.status_code == 200, f"KB Creation failed: {res.text}"
    kb_id = res.json()["id"]
    print(f"SUCCESS: KB Created (ID: {kb_id})")

    # Upload Document to KB
    print("4. Testing KB Document Upload...")
    with open("dummy.txt", "w") as f:
        f.write("This is a document about the capital of France. Paris is the capital of France.")
    
    with open("dummy.txt", "rb") as f:
        files = {"file": ("dummy.txt", f, "text/plain")}
        res = requests.post(f"{API_BASE}/api/kb/{kb_id}/documents", headers=headers, files=files)
    
    assert res.status_code == 200, f"KB Upload failed: {res.text}"
    print(f"SUCCESS: Document uploaded to KB.")

    # 4. Summarizer Test
    print("\n5. Testing Summarizer (Text)...")
    summary_text = "Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation. Its language constructs and object-oriented approach aim to help programmers write clear, logical code for small and large-scale projects."
    res = requests.post(f"{API_BASE}/api/summarize", headers=headers, json={"text": summary_text})
    if res.status_code == 200:
        print(f"SUCCESS: Text Summarized: {res.json().get('summary')[:100]}...")
    else:
        print(f"FAILED: Text Summarize failed ({res.status_code}): {res.text}")

    print("\n6. Testing Summarizer (File)...")
    with open("dummy.txt", "rb") as f:
        files = {"file": ("dummy.txt", f, "text/plain")}
        # max_length is passed as Form data in the endpoint
        res = requests.post(f"{API_BASE}/api/summarize/file", headers=headers, files=files, data={"max_length": 100})
    
    if res.status_code == 200:
        print(f"SUCCESS: File Summarized: {res.json().get('summary')[:100]}...")
    else:
        print(f"FAILED: File Summarize failed ({res.status_code}): {res.text}")

    print("\n--- System Test Complete ---")

if __name__ == "__main__":
    # Ensure dummy file exists
    with open("dummy.txt", "w") as f:
        f.write("Test content")
    test_full_flow()
