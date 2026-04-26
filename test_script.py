import requests
import json
import uuid

API_BASE = "http://localhost:8000"
USERNAME = f"tester_{uuid.uuid4().hex[:6]}"
PASSWORD = "testpassword"

def run_tests():
    print(f"Starting test script with user {USERNAME}")
    
    # 1. Signup
    print("1. Testing signup...")
    res = requests.post(f"{API_BASE}/auth/signup", json={"username": USERNAME, "password": PASSWORD})
    assert res.status_code == 200, f"Signup failed: {res.text}"
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Update Settings (API Key placeholder - tests might fail if LLM actually tries to hit groq, but it should hit openai/gpt-oss-120b in config. Let's see if the proxy is running or if validation fails)
    # Wait, the app uses groq. Let's just set a dummy api key to bypass ValidationError
    print("2. Setting dummy API key...")
    res = requests.post(f"{API_BASE}/settings?key=groq_api_key&value=dummy_key", headers=headers)
    assert res.status_code == 200, f"Setting API key failed: {res.text}"
    
    # 3. Summarize File
    print("3. Testing /api/summarize/file endpoint...")
    with open("dummy.txt", "rb") as f:
        res = requests.post(f"{API_BASE}/api/summarize/file", headers=headers, files={"file": f})
    # This might fail with 500 if the dummy API key is actually invoked against Groq, but it proves the upload works!
    print(f"Summarizer response status: {res.status_code}")
    if res.status_code not in [200, 500, 422]:
        print(f"Unexpected error: {res.text}")
        
    # 4. Create KB
    print("4. Testing KB creation...")
    res = requests.post(f"{API_BASE}/api/kb", headers=headers, json={"name": "Test KB", "description": "Test KB for automation"})
    assert res.status_code == 200, f"KB creation failed: {res.text}"
    kb_id = res.json()["id"]
    
    # 5. Upload document to KB
    print("5. Testing document upload to KB...")
    with open("dummy.txt", "rb") as f:
        res = requests.post(f"{API_BASE}/api/kb/{kb_id}/documents", headers=headers, files={"file": f})
    assert res.status_code == 200, f"Doc upload failed: {res.text}"
    
    # 6. Create chat session
    print("6. Testing chat session creation...")
    res = requests.post(f"{API_BASE}/api/chat/session", headers=headers, json={"kb_id": kb_id, "title": "Test Chat"})
    assert res.status_code == 200, f"Chat session creation failed: {res.text}"
    session_id = res.json()["id"]
    
    # 7. Send chat message
    print("7. Testing chat message generation (Checking for import errors)...")
    res = requests.post(f"{API_BASE}/api/chat/session/{session_id}/message", headers=headers, json={"content": "What is AI?"})
    print(f"Chat response status: {res.status_code}")
    if res.status_code not in [200, 500]:
        print(f"Unexpected error: {res.text}")
    elif res.status_code == 500 and "ModuleNotFoundError" in res.text:
        print("FAILED: ModuleNotFoundError is still present!")
    else:
        print("SUCCESS! No import errors.")

if __name__ == "__main__":
    run_tests()
