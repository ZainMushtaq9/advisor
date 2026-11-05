"""Remote LLM providers for the news-intelligence engine.

This module adds hosted providers alongside the local Ollama
adapter in ``llm_adapter.py``. It changes nothing about the
honesty rules: a provider that is unconfigured, unreachable,
or refuses the call raises ``ModelUnavailable`` and the caller
falls back to the deterministic RULE_BASED processor; output
is never labelled as LLM output when the fallback ran.

Providers (free tier only; no paid API is ever called):
- ``CloudflareAdapter`` (PRIMARY): Cloudflare Workers AI over
  its OpenAI-compatible API. Chat model
  ``@cf/meta/llama-4-scout-17b-16e-instruct``; embeddings model
  ``@cf/baai/bge-m3`` (1024-dim). Free allowance is 10,000
  Neurons/day per account, resetting 00:00 UTC (Cloudflare
  pricing docs, last updated 2026-10-20). Needs
  ``CLOUDFLARE_API_TOKEN`` (Workers AI Read + Edit) and
  ``CLOUDFLARE_ACCOUNT_ID``. Live use is UNVERIFIED until a
  token exists and a call is measured: the token does not
  exist yet (2026-11-05), so no live Cloudflare call has been
  made from this codebase.
- ``HuggingFaceAdapter`` (FALLBACK): Hugging Face Inference
  Providers router over its OpenAI-compatible API
  (``https://router.huggingface.co/v1``). Primary model
  ``openai/gpt-oss-120b``; ``Qwen/Qwen3-8B`` is the recorded
  alternate if the primary is unavailable or gated — no gated
  model licence is ever accepted. Needs ``HF_API_TOKEN``.
  Known limitation, verified twice (2026-11-05): the router
  is NOT free — a free account with zero credits cannot call
  it ("Add credits to continue using Inference Providers").
  This adapter exists so the path works the moment credits
  exist; a refused call is reported, never hidden.

Gemini and Groq are NOT wired here (user decision, 2026-11-05).

Selection: ``build_llm_adapter`` reads ``LLM_PROVIDER``
(``none`` / ``cloudflare`` / ``huggingface`` / ``ollama``,
default ``none``). Unset or incomplete credentials degrade
to ``None`` — the caller then runs the deterministic
fallback. An unknown provider name is a configuration error
(ValueError), not a silent fallback.

All HTTP is stdlib urllib (no new dependency). Tokens are
passed as Bearer headers only; they are never logged, stored,
or returned by any function in this module.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Mapping

from app.services.news_intelligence.llm_adapter import (
    ModelUnavailable,
    OllamaAdapter,
)

# ---------------------------------------------------------------------------
# Provider constants (model ids and endpoints are part of the contract).
# ---------------------------------------------------------------------------

CLOUDFLARE_CHAT_MODEL = "@cf/meta/llama-4-scout-17b-16e-instruct"
CLOUDFLARE_EMBEDDING_MODEL = "@cf/baai/bge-m3"
CLOUDFLARE_EMBEDDING_DIMENSIONS = 1024
CLOUDFLARE_FREE_NEURONS_PER_DAY = 10_000

HF_CHAT_MODEL = "openai/gpt-oss-120b"
HF_CHAT_MODEL_FALLBACK = "Qwen/Qwen3-8B"
HF_BASE_URL = "https://router.huggingface.co/v1"

SUPPORTED_PROVIDERS = ("none", "cloudflare", "huggingface", "ollama")

DEFAULT_TIMEOUT_SECONDS = 120


def _post_json(url: str, payload: dict, api_token: str, timeout: int) -> dict:
    """POST a JSON payload with a Bearer token; return parsed JSON.

    Any transport or HTTP failure becomes ModelUnavailable with
    the provider's status and the first 300 characters of its
    error body (never the token). A non-JSON reply is likewise
    ModelUnavailable, never silently trusted.
    """
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
        except OSError:
            detail = ""
        raise ModelUnavailable(
            f"Provider HTTP {exc.code} from {url}: {detail}"
        ) from exc
    except OSError as exc:
        raise ModelUnavailable(f"Provider unreachable at {url}: {exc}") from exc
    try:
        body = json.loads(raw)
    except ValueError as exc:
        raise ModelUnavailable(
            f"Provider reply at {url} was not JSON: {raw[:200]}"
        ) from exc
    if not isinstance(body, dict):
        raise ModelUnavailable(f"Provider reply at {url} was not a JSON object")
    return body


class OpenAICompatibleAdapter:
    """Chat adapter for any OpenAI-compatible /v1/chat/completions API.

    ``process`` returns the assistant message content verbatim;
    the caller (processing.process_article) parses and
    schema-validates it, so a non-JSON reply is rejected
    downstream, never trusted here.
    """

    def __init__(
        self,
        api_token: str,
        model: str,
        base_url: str,
        model_name: str,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.model_name = model_name
        self.model_version = model
        self._api_token = api_token
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def process(self, article_text: str, instruction: str) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": instruction + " Reply with JSON only.",
                },
                {"role": "user", "content": article_text},
            ],
        }
        body = _post_json(
            self._base_url + "/chat/completions",
            payload,
            self._api_token,
            self._timeout,
        )
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelUnavailable(
                "Provider reply carried no choices[0].message.content"
            ) from exc
        if not isinstance(content, str) or not content.strip():
            raise ModelUnavailable("Provider reply carried empty content")
        return content


class CloudflareAdapter(OpenAICompatibleAdapter):
    """Cloudflare Workers AI (PRIMARY provider).

    Chat via the OpenAI-compatible endpoint; embeddings via
    ``/embeddings`` with bge-m3. ``embed`` validates that every
    returned vector has exactly 1024 float components.
    """

    def __init__(
        self,
        api_token: str,
        account_id: str,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            api_token=api_token,
            model=CLOUDFLARE_CHAT_MODEL,
            base_url=(
                "https://api.cloudflare.com/client/v4/accounts/"
                f"{account_id}/ai/v1"
            ),
            model_name="cloudflare-workers-ai",
            timeout_seconds=timeout_seconds,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with @cf/baai/bge-m3 (1024-dim).

        Returns one vector per input, in input order. Any
        provider refusal or malformed reply is ModelUnavailable.
        """
        if not texts:
            return []
        body = _post_json(
            self._base_url + "/embeddings",
            {"model": CLOUDFLARE_EMBEDDING_MODEL, "input": list(texts)},
            self._api_token,
            self._timeout,
        )
        try:
            data = body["data"]
        except (KeyError, TypeError) as exc:
            raise ModelUnavailable(
                "Cloudflare embeddings reply carried no 'data' field"
            ) from exc
        if not isinstance(data, list) or len(data) != len(texts):
            raise ModelUnavailable(
                "Cloudflare embeddings reply did not return one "
                f"vector per input ({len(texts)} requested)"
            )
        vectors: list[list[float]] = []
        for item in data:
            vector = item.get("embedding") if isinstance(item, dict) else None
            if (
                not isinstance(vector, list)
                or len(vector) != CLOUDFLARE_EMBEDDING_DIMENSIONS
                or not all(isinstance(v, (int, float)) for v in vector)
            ):
                raise ModelUnavailable(
                    "Cloudflare embeddings reply carried a vector "
                    "that is not 1024 numeric components"
                )
            vectors.append([float(v) for v in vector])
        return vectors


class HuggingFaceAdapter(OpenAICompatibleAdapter):
    """Hugging Face Inference Providers router (FALLBACK provider).

    Primary model ``openai/gpt-oss-120b`` (non-gated). Pass
    ``model=HF_CHAT_MODEL_FALLBACK`` (``Qwen/Qwen3-8B``) to use
    the recorded alternate. Known limitation: the router needs
    credits — a free account with zero credits is refused with
    a 402/403 ("Add credits to continue using Inference
    Providers"). That refusal surfaces as ModelUnavailable and
    the caller falls back honestly.
    """

    def __init__(
        self,
        api_token: str,
        model: str = HF_CHAT_MODEL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            api_token=api_token,
            model=model,
            base_url=HF_BASE_URL,
            model_name="huggingface-router",
            timeout_seconds=timeout_seconds,
        )


def _credential(env: Mapping[str, str], name: str) -> str | None:
    value = env.get(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def build_llm_adapter(env: Mapping[str, str] | None = None):
    """Build the configured chat adapter, or None to use the fallback.

    ``env`` defaults to ``os.environ``; pass a mapping in tests.
    Returns None when LLM_PROVIDER is unset/"none" or when the
    chosen provider's credentials are absent/incomplete — the
    caller then runs the deterministic RULE_BASED processor.
    Raises ValueError for an unknown LLM_PROVIDER name.
    """
    env = os.environ if env is None else env
    provider = (env.get("LLM_PROVIDER") or "none").strip().lower()
    if provider == "none":
        return None
    if provider == "cloudflare":
        token = _credential(env, "CLOUDFLARE_API_TOKEN")
        account_id = _credential(env, "CLOUDFLARE_ACCOUNT_ID")
        if token is None or account_id is None:
            return None
        return CloudflareAdapter(api_token=token, account_id=account_id)
    if provider == "huggingface":
        token = _credential(env, "HF_API_TOKEN")
        if token is None:
            return None
        return HuggingFaceAdapter(api_token=token)
    if provider == "ollama":
        model = (env.get("OLLAMA_MODEL") or "qwen2.5:1.5b").strip()
        return OllamaAdapter(model=model or "qwen2.5:1.5b")
    raise ValueError(
        f"Unknown LLM_PROVIDER {provider!r}; expected one of "
        f"{', '.join(SUPPORTED_PROVIDERS)}"
    )


def build_embedding_provider(env: Mapping[str, str] | None = None):
    """Build the configured embedding provider, or None.

    Only Cloudflare Workers AI (bge-m3) is wired as an embedding
    provider. Returns None when its token or account id is
    absent — the caller keeps deterministic full-text retrieval.
    """
    env = os.environ if env is None else env
    token = _credential(env, "CLOUDFLARE_API_TOKEN")
    account_id = _credential(env, "CLOUDFLARE_ACCOUNT_ID")
    if token is None or account_id is None:
        return None
    return CloudflareAdapter(api_token=token, account_id=account_id)
