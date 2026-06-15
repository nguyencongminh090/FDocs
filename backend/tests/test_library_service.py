"""Unit test cho LibraryService — cosine similarity + dựng similarity map.

Không chạm DB: chunk_repo được thay bằng fake trả centroid dựng sẵn.
"""
import math

import pytest

from app.services.library_service import SIMILARITY_THRESHOLD, LibraryService, _cosine_similarity


class TestCosineSimilarity:
    def test_identical_vectors_return_one(self):
        v = [0.1, 0.2, 0.3, 0.4]
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors_return_zero(self):
        assert _cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)

    def test_opposite_vectors_return_minus_one(self):
        assert _cosine_similarity([1, 2, 3], [-1, -2, -3]) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero_not_nan(self):
        # Bảo vệ chống chia 0 → tránh NaN làm hỏng filter threshold
        result = _cosine_similarity([0, 0, 0], [1, 2, 3])
        assert result == 0.0
        assert not math.isnan(result)

    def test_known_value(self):
        # cos giữa [1,1] và [1,0] = 1/sqrt(2)
        assert _cosine_similarity([1, 1], [1, 0]) == pytest.approx(1 / math.sqrt(2))


class _FakeChunkRepo:
    def __init__(self, docs):
        self._docs = docs

    async def get_all_doc_centroids(self, user_id):
        return self._docs


def _make_service(docs):
    service = LibraryService(db=None)
    service.chunk_repo = _FakeChunkRepo(docs)
    return service


class TestSimilarityMap:
    async def test_edge_only_above_threshold(self):
        docs = [
            {"id": "a", "title": "A", "word_count": 100, "file_type": "pdf", "centroid": [1.0, 0.0]},
            {"id": "b", "title": "B", "word_count": 200, "file_type": "pdf", "centroid": [1.0, 0.0]},  # sim=1.0
            {"id": "c", "title": "C", "word_count": 50, "file_type": "docx", "centroid": [0.0, 1.0]},  # sim=0 với A,B
        ]
        result = await _make_service(docs).get_similarity_map(user_id="u")

        assert len(result["nodes"]) == 3
        # Chỉ cặp A-B (sim=1.0) vượt threshold; A-C và B-C (sim=0) bị loại
        assert len(result["edges"]) == 1
        edge = result["edges"][0]
        assert {edge["source"], edge["target"]} == {"a", "b"}
        assert edge["similarity"] == 1.0

    async def test_node_without_centroid_excluded(self):
        docs = [
            {"id": "a", "title": "A", "word_count": 100, "file_type": "pdf", "centroid": [1.0, 0.0]},
            {"id": "b", "title": "B", "word_count": 200, "file_type": "pdf", "centroid": None},  # chưa embed
        ]
        result = await _make_service(docs).get_similarity_map(user_id="u")

        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["id"] == "a"
        assert result["edges"] == []

    async def test_empty_library(self):
        result = await _make_service([]).get_similarity_map(user_id="u")
        assert result == {"nodes": [], "edges": []}

    async def test_similarity_rounded_to_4_decimals(self):
        docs = [
            {"id": "a", "title": "A", "word_count": 1, "file_type": "pdf", "centroid": [1.0, 1.0]},
            {"id": "b", "title": "B", "word_count": 1, "file_type": "pdf", "centroid": [1.0, 0.9]},
        ]
        result = await _make_service(docs).get_similarity_map(user_id="u")
        assert len(result["edges"]) == 1
        sim = result["edges"][0]["similarity"]
        assert sim == round(sim, 4)

    def test_threshold_constant(self):
        assert SIMILARITY_THRESHOLD == 0.65
