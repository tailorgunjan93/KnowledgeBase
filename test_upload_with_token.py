import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=30.0) as ac:
        # 1. Login
        login_resp = await ac.post("/auth/login", json={"username": "admin", "password": "password"})
        if login_resp.status_code != 200:
            # Let's try register if admin doesn't exist
            login_resp = await ac.post("/auth/register", json={"username": "admin", "password": "password"})
            if login_resp.status_code != 200:
                print("Login/Register failed:", login_resp.text)
                return
                
        token = login_resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get KB list
        kb_resp = await ac.get("/api/kb", headers=headers)
        if kb_resp.status_code != 200:
            print("KB list failed:", kb_resp.text)
            return
        
        kbs = kb_resp.json()["items"]
        if not kbs:
            # Create a KB
            create_resp = await ac.post("/api/kb", json={"name": "Test KB", "description": "Test"}, headers=headers)
            kb = create_resp.json()
        else:
            kb = kbs[0]
            
        kb_id = kb["id"]
        print(f"Using KB: {kb_id}")

        # 3. Upload document
        upload_resp = await ac.post(
            f"/api/kb/{kb_id}/documents",
            files={"file": ("test.txt", b"Hello knowledge base. This is a test document.", "text/plain")},
            headers=headers
        )
        print("Upload Response:", upload_resp.status_code, upload_resp.text)

if __name__ == "__main__":
    asyncio.run(main())
