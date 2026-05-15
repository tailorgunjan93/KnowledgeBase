"""Integration tests for the chat API.

TODO: Rewrite using httpx.AsyncClient + pytest-asyncio after the sync→async migration.
      The old TestClient approach is incompatible with the async FastAPI app and the
      RBAC dependency layer added in the RBAC pipeline refactor.
"""
import pytest


@pytest.mark.skip(reason="Needs rewrite for async FastAPI + RBAC (see module docstring)")
def test_chat_endpoint():
    pass


@pytest.mark.skip(reason="Needs rewrite for async FastAPI + RBAC (see module docstring)")
def test_get_sessions():
    pass
