# ADR-007 — LLM: Ollama local-only runtime + own tool loop; no model pinned; no external API

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04
- **Supersedes:** The first draft's LiteLLM abstraction and "external API
  opt-in" positions, both withdrawn under the revised brief (PKR 0 absolute,
  local inference only).

## Context

The project wants AI assistance for research drafting, with tool-calling
(search stored data, fetch a stored document, run a named deterministic
calculation, draft research text). The revised brief fixes Ollama with
compatible open-weight models for LOCAL inference only, at PKR 0 absolute.
Ollama is a runtime, not a model, and each model carries its own licence.

## Decision

- **Runtime:** Ollama, local inference only, on the team's own machine.
  Ollama is MIT-licensed and its local runtime is free with no account or
  subscription required (VERIFIED by public page reads).
- **Prohibited, explicitly:** Ollama Cloud (reported paid tiers — excluded),
  any `:cloud` model, any cloud web-search API requiring Ollama sign-in, and
  any external provider API or key. A later prompt, config, or doc referencing
  any of these is a defect against this stack.
- **Abstraction:** none beyond Ollama's own local API. LiteLLM is removed:
  it abstracts over external providers, and this stack has none.
  LangChain/LlamaIndex agent frameworks are not used (see below).
- **Orchestration:** an own small tool-calling loop over a fixed, auditable
  tool list (see ADR-010). The loop owns tool definitions, logging, and audit.
- **Model:** NO SPECIFIC MODEL IS PINNED in Phase 1. A model becomes primary
  only by passing the evaluation gate below, with its licence read first.

## Evaluation gate (a model must pass ALL of these before adoption)

1. Licence check: the model's own licence (and any acceptable-use terms) read
   and recorded; it must permit this project's use (including any commercial
   use contemplated) at PKR 0.
2. Local fit: it runs on the team's actual hardware (CPU, or a GPU if one is
   separately available — none is budgeted) within acceptable latency for
   research drafting; no benchmark is claimed until this is measured.
3. Tool-calling accuracy: on a fixed set of PSX research tasks, it calls the
   correct tool with valid arguments at a rate the team records and accepts;
   failures are logged, not hidden.
4. Auditability: every model call, tool call, argument, and result is logged
   per ADR-010, and the model never produces a number except by calling a
   deterministic calculation tool.
5. Offline operation: with the model downloaded, research drafting works with
   no internet and no account.

## Consequences

- Positive: PKR 0 by construction; prompts and data stay on the team's machine;
  no vendor lock-in, no per-token bill, no key to leak.
- Negative: capability is bounded by local hardware (a stated limit);
  model quality is UNVERIFIED until the gate runs; the team owns prompt and
  tool maintenance.
- Constraint: the entire stack works with Ollama absent or with no model
  downloaded. LLM features are an optional research-draft layer; core features
  (data, indicators, computed reports) never depend on them.

## Alternatives considered

- LiteLLM — removed (above).
- LangChain / LlamaIndex agents — rejected: large, fast-changing frameworks
  whose agent behaviour would make the ADR-010 audit trail harder to guarantee.
- A hard-coded single-provider SDK — rejected and prohibited (external API).
- A locally hosted model chosen without evaluation — rejected: naming one now
  would be invented; hence "no primary justified" is stated plainly in the
  comparison document (§12).

## Verification / open checks

- [ ] Phase 2: run the evaluation gate; record the chosen model's name,
  version/quantisation, licence, and gate results before it becomes primary.
  Until then, this ADR's model decision remains "none pinned".
