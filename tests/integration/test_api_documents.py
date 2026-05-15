"""Integration tests for the documents API.

TODO: Rewrite using httpx.AsyncClient + pytest-asyncio after the sync→async migration.
      The old TestClient approach is incompatible with the async FastAPI app and the
      RBAC dependency layer added in the RBAC pipeline refactor.
"""
import pytest


@pytest.mark.skip(reason="Needs rewrite for async FastAPI + RBAC (see module docstring)")
def test_upload_document():
    pass


@pytest.mark.skip(reason="Needs rewrite for async FastAPI + RBAC (see module docstring)")
def test_list_documents():
    pass


@pytest.mark.skip(reason="Needs rewrite for async FastAPI + RBAC (see module docstring)")
def test_delete_document():
    pass
