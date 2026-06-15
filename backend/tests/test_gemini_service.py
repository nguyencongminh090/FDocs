"""Unit test cho gemini_service — chunking (pure) + parsing output Gemini (mock model).

Mock _make_client để không gọi mạng; tập trung verify logic strip ```json fence
và parse JSON — phần dễ vỡ nhất khi LLM trả về text bọc markdown.
"""
import pytest

from app.services import gemini_service


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModel:
    def __init__(self, text):
        self._text = text

    async def generate_content_async(self, prompt, **kwargs):
        return _FakeResponse(self._text)


class TestChunkText:
    def test_short_text_single_chunk(self):
        chunks = gemini_service.chunk_text("Một đoạn văn bản ngắn.")
        assert len(chunks) == 1

    def test_long_text_multiple_chunks(self):
        long_text = "Linear algebra studies vector spaces. " * 200
        chunks = gemini_service.chunk_text(long_text)
        assert len(chunks) > 1
        assert all(isinstance(c, str) and c for c in chunks)

    def test_empty_text(self):
        assert gemini_service.chunk_text("") == []


class TestExtractKeywords:
    async def test_parses_plain_json_array(self, monkeypatch):
        monkeypatch.setattr(
            gemini_service, "_make_client", lambda key: _FakeModel('["algebra", "vector", "matrix"]')
        )
        result = await gemini_service.extract_keywords("doc text", "key")
        assert result == ["algebra", "vector", "matrix"]

    async def test_strips_json_code_fence(self, monkeypatch):
        fenced = '```json\n["algebra", "vector"]\n```'
        monkeypatch.setattr(gemini_service, "_make_client", lambda key: _FakeModel(fenced))
        result = await gemini_service.extract_keywords("doc text", "key")
        assert result == ["algebra", "vector"]

    async def test_strips_bare_code_fence(self, monkeypatch):
        fenced = '```\n["a", "b"]\n```'
        monkeypatch.setattr(gemini_service, "_make_client", lambda key: _FakeModel(fenced))
        result = await gemini_service.extract_keywords("doc text", "key")
        assert result == ["a", "b"]


class TestScoreRelevance:
    async def test_parses_and_rounds_score(self, monkeypatch):
        payload = '{"score": 0.82345, "explanation": "Phù hợp cao."}'
        monkeypatch.setattr(gemini_service, "_make_client", lambda key: _FakeModel(payload))
        result = await gemini_service.score_relevance("text", "goal", ["k1"], "topic", "key")
        assert result["relevance_score"] == 0.823
        assert result["explanation"] == "Phù hợp cao."

    async def test_handles_fenced_json(self, monkeypatch):
        payload = '```json\n{"score": 0.5, "explanation": "Trung bình."}\n```'
        monkeypatch.setattr(gemini_service, "_make_client", lambda key: _FakeModel(payload))
        result = await gemini_service.score_relevance("text", "goal", [], "topic", "key")
        assert result["relevance_score"] == 0.5


class TestAnswerQuestionStream:
    async def test_yields_only_nonempty_tokens(self, monkeypatch):
        class _StreamChunk:
            def __init__(self, text):
                self.text = text

        class _StreamResp:
            def __aiter__(self):
                async def gen():
                    for t in ["Hello", "", " world", None]:
                        yield _StreamChunk(t)
                return gen()

        class _StreamModel:
            async def generate_content_async(self, prompt, stream=False):
                return _StreamResp()

        monkeypatch.setattr(gemini_service, "_make_client", lambda key: _StreamModel())
        tokens = [t async for t in gemini_service.answer_question_stream("q", ["ctx"], "key")]
        assert tokens == ["Hello", " world"]
