# LLM Providers — Cloudflare Workers AI + Hugging Face (2026-11-05)

Branch: `llm-cloudflare-hf-adapters` (from `backend-correction-kpi`
@ `a61da33`). Code: `backend/app/services/news_intelligence/providers.py`;
tests: `backend/tests/test_llm_providers.py` (19 tests, mocked HTTP
only). Full backend suite: 561 passed at the time of writing.

## Providers

| Provider | Role | Chat model | Embeddings | Free tier | Live status |
| --- | --- | --- | --- | --- | --- |
| Cloudflare Workers AI | PRIMARY | `@cf/meta/llama-4-scout-17b-16e-instruct` | `@cf/baai/bge-m3` (1024-dim) | 10,000 Neurons/day, reset 00:00 UTC | PENDING — token does not exist yet |
| Hugging Face Inference Providers router | FALLBACK | `openai/gpt-oss-120b` (alternate `Qwen/Qwen3-8B`, non-gated) | — | NOT free: router needs credits | TESTED ONCE 2026-11-05 — refused (HTTP 403, see below) |

Gemini and Groq are NOT wired (user decision, 2026-11-05).

## Selection and fallback (honesty rules, unchanged)

- `LLM_PROVIDER` env: `none` (default) / `cloudflare` /
  `huggingface` / `ollama`. Unset, or set with missing
  credentials, degrades to `None` and the caller runs the
  deterministic RULE_BASED fallback — output is never labelled
  as LLM output when the fallback ran.
- An unknown `LLM_PROVIDER` value is a configuration error
  (ValueError), not a silent fallback.
- A provider that is unreachable or refuses a call raises
  `ModelUnavailable`; `processing.process_article` then uses
  the fallback and records the refusal in the result errors.
- The CLI (`scripts/run_news_intelligence.py process`) accepts
  `--llm-provider`; `--ollama-model` still selects the local
  adapter for backwards compatibility.
- Config: `LLM_PROVIDER`, `CLOUDFLARE_API_TOKEN`,
  `CLOUDFLARE_ACCOUNT_ID`, `HF_API_TOKEN` are fields on
  `app.config.Settings` and names on `/api/v1/config/status`
  (names only — values are never returned or logged). A blank
  token counts as unset.

## RAG embeddings

- `build_embedding_provider()` returns the Cloudflare adapter
  when its token and account id are set, else None.
- `app.services.rag.retrieval.embed_texts(texts, provider)`
  returns None without a provider, so callers keep the
  deterministic full-text path. Vector retrieval stays
  REGISTERED but NOT IMPLEMENTED in `app/services/rag`
  (`RETRIEVAL_METHODS["vector"]["implemented"] is False`):
  the provider exists in code, but no live embedding call has
  been measured.
- No embedding is computed, stored, or claimed until a token
  is configured and a call is measured.

## Environment variables the deploy will need

- `LLM_PROVIDER=cloudflare` (once the token exists).
- `CLOUDFLARE_API_TOKEN` — custom token, Account → Workers AI
  → Read and Edit. Shown once at creation; never in chat/files.
- `CLOUDFLARE_ACCOUNT_ID` — the Cloudflare account id.
- `HF_API_TOKEN` — already set on the Render advisor service.

## Live tests

### Hugging Face — tested once, 2026-11-05 ~16:30 PKT — REFUSED

- One call only, via the new `HuggingFaceAdapter`, against the
  live seeded event id 4 from the Render API ("SBP Monetary
  Policy Committee decision: policy rate raised to 12%").
  Model `openai/gpt-oss-120b`. Token fetched from the Render
  API in memory only (never printed or written).
- Exact result: `ModelUnavailable: Provider HTTP 403 from
  https://router.huggingface.co/v1/chat/completions:
  {"error": "This authentication method does not have
  sufficient permissions to call Inference Providers on behalf
  of user zainmushtaq54"}`.
- Meaning: the token currently stored as `HF_API_TOKEN` on
  Render does not carry the Inference Providers permission
  (this is a permissions refusal, distinct from the earlier
  "Add credits to continue using Inference Providers" seen
  with a different call). HF is NOT a working fallback with
  the current stored token. Unblocker: a token that carries
  the Inference Providers permission — and then credits, since
  the router is pay-as-you-go for a free account. No further
  live HF call was made in this task (one call, as instructed).

### Cloudflare — PENDING

- No live call attempted: the token does not exist yet (the
  user must still complete the Cloudflare two-factor step).
- To verify when the token lands: set `LLM_PROVIDER=cloudflare`
  with `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` on the
  Render advisor service, then run one chat call and one
  embeddings call against the seeded data and record the
  measured latency, the Neuron usage, and the reply. Do not
  claim Cloudflare works until that measurement exists.
