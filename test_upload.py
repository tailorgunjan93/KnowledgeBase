import asyncio
import httpx
from src.main import app

async def main():
    from src.api.deps import get_current_user
    from src.domain.models import User
    
    app.dependency_overrides[get_current_user] = lambda: User(id=1, username="test")
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/kb/1/documents",
            files={"file": ("test.txt", b"Hello knowledge base", "text/plain")}
        )
        print("Upload Response:", response.status_code, response.text)

if __name__ == "__main__":
    asyncio.run(main())
