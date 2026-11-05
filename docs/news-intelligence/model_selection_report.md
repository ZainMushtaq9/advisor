# LLM Model Selection and Evaluation Report (Deliverable 4)

Status: live local-model inference UNVERIFIED (hardware-bound, see
below). The deterministic fallback is COMPLETE as a fallback and is
what every measured result in this work uses. No LLM output is
claimed anywhere in this work: no local model ran, no summary here
is model output, and no accuracy claim is made for any model.

## Hardware measurements

| Measurement | Phase A (2026-11-05) | Phase B re-measure (2026-11-05) |
|---|---|---|
| CPUs | 4 | 4 |
| RAM total | 7.7 GB | 7.7 GB |
| RAM free | ~0.5 GB (under two-coordinator load) | 151 MB free / 885 MB available |
| GPU | none (`nvidia-smi` not found) | none |
| Ollama installed | no | no |
| `~/.ollama` | absent | absent |
| Disk free (home) | 143 GB (5% used) | 143 GB (5% used) |
| Backend venv | no torch, no transformers, no requests, no feedparser | unchanged |

## Decision

Do NOT start a local model server under current load. A ~1B Q4
model needs ~1 GB plus runtime overhead and risks OOM-killing
concurrent work. The engine therefore uses stdlib only (urllib,
xml.etree, json, re, decimal): no new dependency pins, no licence
changes, no paid API.

## Selected adapter design (implemented, not yet live-verified)

- Provider-independent `LLMAdapter` protocol: the app can change
  its local LLM without redesigning the pipeline.
- `NullAdapter`: always raises `ModelUnavailable` — forces the
  honest UNPROCESSED path instead of fake output.
- `OllamaAdapter`: stdlib HTTP POST to `http://localhost:11434/api/generate`
  (localhost only, never an external host), `format=json`, default
  model `qwen2.5:1.5b`, 120 s timeout, OSError -> `ModelUnavailable`.
  No validation inside the adapter — the caller validates.
- `DeterministicFallback`: rule-based, labelled `processor="RULE_BASED"`,
  `model_name="deterministic-fallback-v1"`,
  `model_version="rule-based-1.0"`. Uses the Phase 11 resolver,
  taxonomy keywords, and a small sentiment lexicon.
- NO OpenAI / Gemini / Groq / Anthropic code path exists anywhere
  in this package, by design (PKR 0 rule).

## Candidate model (not run — recorded for the unblocker)

Qwen2.5 1.5B instruction, Q4 quantized, via Ollama, is the
candidate IF the unblocker is met: it is the smallest plausible
instruction model in the adapter default and fits the no-GPU,
low-RAM constraint better than 7B+ models. This is a candidate,
not a selection: licence, memory, latency, quantization
compatibility, and Urdu/English performance are all UNMEASURED
until a run happens.

## Exact unblocker for live inference

1. Free RAM recovered above ~3 GB (measured, not assumed).
2. Install Ollama, pull a <=1B Q4 open-weight instruction model.
3. Measure latency and memory on the N=20 evaluation set.
4. Record the results here before any production use.

Until then: LLM processing layer = UNVERIFIED, fallback = the
operating path, and every stored row says which one produced it.

## Fallback evaluation (measured, N=20)

See `classification_evaluation.md`: category agreement 10/12 on
synthetic headlines (83.3%), entity precision 91.7% / recall
91.7% combined, sentiment agreement 15/20 strict (75%) for the
rule-based fallback only. These numbers measure the FALLBACK, not
any LLM, and the sample size (20) cannot support a production
accuracy claim.
