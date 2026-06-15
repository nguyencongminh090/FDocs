"""Integration test cho GET /api/library/similarity-map."""
import uuid

import pytest

from app.database import get_db
from app.main import app
from app.middlewares.auth import get_current_user_id
from app.services import library_service
from tests.conftest import TEST_USER_ID, _fake_get_db


def _mock_centroids(monkeypatch, docs):
    class FakeChunkRepo:
        def __init__(self, db=None):
            pass

        async def get_all_doc_centroids(self, user_id):
            return docs

    monkeypatch.setattr(library_service, "ChunkRepository", FakeChunkRepo)


@pytest.fixture(autouse=True)
def _clear():
    yield
    app.dependency_overrides.clear()


class TestSimilarityMapAPI:
    async def test_returns_nodes_and_edges(self, client, monkeypatch):
        _mock_centroids(monkeypatch, [
            {"id": "a", "title": "A", "word_count": 100, "file_type": "pdf", "centroid": [1.0, 0.0]},
            {"id": "b", "title": "B", "word_count": 200, "file_type": "pdf", "centroid": [1.0, 0.0]},
        ])
        app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
        app.dependency_overrides[get_db] = _fake_get_db

        resp = await client.get("/api/library/similarity-map")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["nodes"]) == 2
        assert len(body["edges"]) == 1
        assert body["edges"][0]["similarity"] == 1.0

    async def test_empty_library(self, client, monkeypatch):
        _mock_centroids(monkeypatch, [])
        app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
        app.dependency_overrides[get_db] = _fake_get_db

        resp = await client.get("/api/library/similarity-map")
        assert resp.status_code == 200
        assert resp.json() == {"nodes": [], "edges": []}

    async def test_requires_auth_403(self, client):
        resp = await client.get("/api/library/similarity-map")
        assert resp.status_code == 403
