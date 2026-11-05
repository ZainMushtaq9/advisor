"""Tests for the Cloudflare + Hugging Face LLM providers.

All HTTP is mocked (monkeypatched urllib.request.urlopen): no
test ever touches a real provider, a real token, or the network.
Live behaviour is measured only by the one-off live test in
docs/news-intelligence/llm_providers.md, never here.
"""

from __future__ import annotations

import io
import json
import urllib.error

import pytest

from app.services.news_intelligence.llm_adapter import ModelUnavailable
from app.services.news_intelligence.providers import (
    CLOUDFLARE_EMBEDDING_DIMENSIONS,
    CloudflareAdapter,
    HuggingFaceAdapter,
    build_embedding_provider,
    build_llm_adapter,
)
from app.services.rag.retrieval import embed_texts


class _FakeResponse:
    """Minimal context-manager stand-in for urlopen's response."""

    def __init__(self, payload: dict | str):
        if isinstance(payload, str):
            self._raw = payload.encode("utf-8")
        else:
            self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _install_fake_urlopen(monkeypatch, handler):
    """handler(request) -> _FakeResponse, or raises HTTPError/OSError."""
    import urllib.request

    def fake_urlopen(request, timeout=None):
        return handler(request)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)


def _chat_reply(content: str) -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


def test_cloudflare_chat_posts_to_account_url_with_bearer(monkeypatch):
    seen: dict = {}

    def handler(request):
        seen["url"] = request.full_url
        seen["auth"] = request.get_header("Authorization")
        seen["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(_chat_reply('{"summary": "ok"}'))

    _install_fake_urlopen(monkeypatch, handler)
    adapter = CloudflareAdapter(api_token="cf-test-token", account_id="acct-123")
    assert adapter.model_name == "cloudflare-workers-ai"
    assert adapter.model_version == "@cf/meta/llama-4-scout-17b-16e-instruct"
    out = adapter.process("some article text", "Summarise.")
    assert out == '{"summary": "ok"}'
    assert seen["url"] == (
        "https://api.cloudflare.com/client/v4/accounts/"
        "acct-123/ai/v1/chat/completions"
    )
    assert seen["auth"] == "Bearer cf-test-token"
    assert seen["body"]["model"] == "@cf/meta/llama-4-scout-17b-16e-instruct"
    assert seen["body"]["messages"][1]["content"] == "some article text"


def test_huggingface_chat_posts_to_router_with_gpt_oss(monkeypatch):
    seen: dict = {}

    def handler(request):
        seen["url"] = request.full_url
        seen["auth"] = request.get_header("Authorization")
        seen["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(_chat_reply("hello"))

    _install_fake_urlopen(monkeypatch, handler)
    adapter = HuggingFaceAdapter(api_token="hf-test-token")
    assert adapter.model_name == "huggingface-router"
    assert adapter.model_version == "openai/gpt-oss-120b"
    assert adapter.process("text", "Do it.") == "hello"
    assert seen["url"] == "https://router.huggingface.co/v1/chat/completions"
    assert seen["auth"] == "Bearer hf-test-token"
    assert seen["body"]["model"] == "openai/gpt-oss-120b"


def test_huggingface_fallback_model_is_qwen3_8b(monkeypatch):
    seen: dict = {}

    def handler(request):
        seen["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(_chat_reply("hi"))

    _install_fake_urlopen(monkeypatch, handler)
    adapter = HuggingFaceAdapter(api_token="hf-test-token", model="Qwen/Qwen3-8B")
    adapter.process("text", "Do it.")
    assert seen["body"]["model"] == "Qwen/Qwen3-8B"


def test_provider_http_402_becomes_model_unavailable_with_status(monkeypatch):
    def handler(request):
        raise urllib.error.HTTPError(
            request.full_url,
            402,
            "Payment Required",
            {},
            io.BytesIO(b'{"error": "Add credits to continue"}'),
        )

    _install_fake_urlopen(monkeypatch, handler)
    adapter = HuggingFaceAdapter(api_token="hf-test-token")
    with pytest.raises(ModelUnavailable) as excinfo:
        adapter.process("text", "Do it.")
    assert "402" in str(excinfo.value)
    assert "Add credits" in str(excinfo.value)


def test_provider_reply_without_choices_is_unavailable(monkeypatch):
    _install_fake_urlopen(monkeypatch, lambda request: _FakeResponse({}))
    adapter = CloudflareAdapter(api_token="cf-test-token", account_id="acct-1")
    with pytest.raises(ModelUnavailable, match="no choices"):
        adapter.process("text", "Do it.")


def test_provider_non_json_reply_is_unavailable(monkeypatch):
    _install_fake_urlopen(
        monkeypatch, lambda request: _FakeResponse("not json at all")
    )
    adapter = HuggingFaceAdapter(api_token="hf-test-token")
    with pytest.raises(ModelUnavailable, match="not JSON"):
        adapter.process("text", "Do it.")


def test_provider_unreachable_is_unavailable(monkeypatch):
    def handler(request):
        raise OSError("network down")

    _install_fake_urlopen(monkeypatch, handler)
    adapter = CloudflareAdapter(api_token="cf-test-token", account_id="acct-1")
    with pytest.raises(ModelUnavailable, match="unreachable"):
        adapter.process("text", "Do it.")


def test_cloudflare_embed_returns_1024_dim_vectors(monkeypatch):
    seen: dict = {}

    def handler(request):
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(
            {
                "data": [
                    {"embedding": [0.1] * CLOUDFLARE_EMBEDDING_DIMENSIONS},
                    {"embedding": [0.2] * CLOUDFLARE_EMBEDDING_DIMENSIONS},
                ]
            }
        )

    _install_fake_urlopen(monkeypatch, handler)
    adapter = CloudflareAdapter(api_token="cf-test-token", account_id="acct-9")
    vectors = adapter.embed(["first text", "second text"])
    assert len(vectors) == 2
    assert all(len(v) == 1024 for v in vectors)
    assert vectors[0][0] == pytest.approx(0.1)
    assert seen["url"].endswith("/ai/v1/embeddings")
    assert seen["body"]["model"] == "@cf/baai/bge-m3"
    assert seen["body"]["input"] == ["first text", "second text"]


def test_cloudflare_embed_wrong_dimensions_is_unavailable(monkeypatch):
    def handler(request):
        return _FakeResponse({"data": [{"embedding": [0.1] * 768}]})

    _install_fake_urlopen(monkeypatch, handler)
    adapter = CloudflareAdapter(api_token="cf-test-token", account_id="acct-9")
    with pytest.raises(ModelUnavailable, match="1024"):
        adapter.embed(["text"])


def test_cloudflare_embed_empty_input_returns_empty(monkeypatch):
    adapter = CloudflareAdapter(api_token="cf-test-token", account_id="acct-9")
    assert adapter.embed([]) == []


def test_factory_none_when_unconfigured():
    assert build_llm_adapter({}) is None
    assert build_llm_adapter({"LLM_PROVIDER": "none"}) is None
    # Cloudflare without token or without account id degrades to None.
    assert build_llm_adapter({"LLM_PROVIDER": "cloudflare"}) is None
    assert (
        build_llm_adapter(
            {"LLM_PROVIDER": "cloudflare", "CLOUDFLARE_API_TOKEN": "tok"}
        )
        is None
    )
    assert (
        build_llm_adapter(
            {"LLM_PROVIDER": "cloudflare", "CLOUDFLARE_ACCOUNT_ID": "acct"}
        )
        is None
    )
    # Blank credentials count as missing.
    assert (
        build_llm_adapter(
            {
                "LLM_PROVIDER": "cloudflare",
                "CLOUDFLARE_API_TOKEN": "   ",
                "CLOUDFLARE_ACCOUNT_ID": "acct",
            }
        )
        is None
    )
    # Hugging Face without a token degrades to None.
    assert build_llm_adapter({"LLM_PROVIDER": "huggingface"}) is None


def test_factory_builds_each_provider_when_configured():
    cf = build_llm_adapter(
        {
            "LLM_PROVIDER": "cloudflare",
            "CLOUDFLARE_API_TOKEN": "tok",
            "CLOUDFLARE_ACCOUNT_ID": "acct",
        }
    )
    assert isinstance(cf, CloudflareAdapter)
    hf = build_llm_adapter(
        {"LLM_PROVIDER": "huggingface", "HF_API_TOKEN": "tok"}
    )
    assert isinstance(hf, HuggingFaceAdapter)
    ollama = build_llm_adapter({"LLM_PROVIDER": "ollama"})
    assert ollama.model_name == "ollama"


def test_factory_unknown_provider_is_a_configuration_error():
    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        build_llm_adapter({"LLM_PROVIDER": "gemini"})


def test_embedding_provider_none_when_unconfigured():
    assert build_embedding_provider({}) is None
    assert (
        build_embedding_provider({"CLOUDFLARE_API_TOKEN": "tok"}) is None
    )
    provider = build_embedding_provider(
        {"CLOUDFLARE_API_TOKEN": "tok", "CLOUDFLARE_ACCOUNT_ID": "acct"}
    )
    assert isinstance(provider, CloudflareAdapter)


def test_embed_texts_returns_none_without_provider():
    assert embed_texts(["a", "b"], provider=None) is None


def test_processing_with_llm_adapter_labels_llm(monkeypatch):
    from app.services.news_intelligence.processing import process_article

    class StubAdapter:
        model_name = "stub"
        model_version = "stub-1"

        def process(self, article_text, instruction):
            return json.dumps(
                {
                    "article_id": "a1",
                    "title": "HUBC profit rises",
                    "source": "test",
                    "canonical_url": "https://example.invalid/x",
                    "published_at": "2026-11-03T00:00:00+05:00",
                    "retrieved_at": "2026-11-03T00:00:00+05:00",
                    "language": "en",
                    "company_names": [],
                    "ticker_symbols": [],
                    "sector_names": [],
                    "event_category": "earnings",
                    "sentiment": "positive",
                    "relevance_score": 0.5,
                    "impact_score": 0.5,
                    "confidence_score": 0.5,
                    "potential_impact_horizon": "unknown",
                    "extracted_facts": ["HUBC profit rises"],
                    "supporting_evidence": [],
                    "uncertainty_notes": [],
                    "risk_factors": [],
                    "summary": "HUBC profit rises",
                    "model_name": "stub",
                    "model_version": "stub-1",
                    "processing_timestamp": "2026-11-03T00:00:00+05:00",
                    "processor": "LLM",
                    "ambiguous_entity": False,
                }
            )

    article = {
        "article_id": "a1",
        "title": "HUBC profit rises",
        "source": "test",
        "canonical_url": "https://example.invalid/x",
        "published_at": "2026-11-03T00:00:00+05:00",
        "retrieved_at": "2026-11-03T00:00:00+05:00",
        "text": "HUBC profit rises",
    }
    result = process_article(article, {}, set(), {}, adapter=StubAdapter())
    assert result["processor"] == "LLM"
    assert result["record"]["processor"] == "LLM"


def test_config_reports_provider_names_only(monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "cloudflare")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "cf-secret-never-shown")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "acct-secret-never-shown")
    monkeypatch.setenv("HF_API_TOKEN", "hf-secret-never-shown")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.LLM_PROVIDER == "cloudflare"
        status = {e["name"]: e for e in settings.config_status()}
        for name in (
            "LLM_PROVIDER",
            "CLOUDFLARE_API_TOKEN",
            "CLOUDFLARE_ACCOUNT_ID",
            "HF_API_TOKEN",
        ):
            assert status[name]["status"] == "SET"
            assert status[name]["source"] == "environment"
        # Redaction: no token value anywhere in the status payload.
        assert "cf-secret-never-shown" not in json.dumps(status)
        assert "hf-secret-never-shown" not in json.dumps(status)
        assert "acct-secret-never-shown" not in json.dumps(status)
    finally:
        get_settings.cache_clear()


def test_config_blank_provider_token_counts_as_missing(monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("HF_API_TOKEN", "   ")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.HF_API_TOKEN is None
        status = {e["name"]: e for e in settings.config_status()}
        assert status["HF_API_TOKEN"]["status"] == "MISSING"
    finally:
        get_settings.cache_clear()


def test_vector_registry_still_not_implemented():
    from app.services.rag import RETRIEVAL_METHODS

    assert RETRIEVAL_METHODS["vector"]["implemented"] is False
    assert RETRIEVAL_METHODS["full_text"]["implemented"] is True
