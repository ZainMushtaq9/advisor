# ADR-002 — Backend framework: Python 3.12 + FastAPI + Pydantic v2 + Uvicorn

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04

## Context

The backend must serve a typed HTTP API to the Next.js frontend, run the
Python analytics stack (pandas, scikit-learn, statsmodels, conditional PyTorch),
enqueue Celery jobs, and validate LLM tool arguments — all in one language,
at PKR 0. Python 3.12.3 is already installed (VERIFIED).

## Decision

- **Language:** Python 3.12.
- **Framework:** FastAPI (MIT, VERIFIED), served by Uvicorn (ASGI).
- **Validation:** Pydantic v2 — FastAPI's validation layer, reused for API
  payloads, Celery job payloads, and LLM tool arguments, so one schema
  definition serves three boundaries.
- **API contract:** OpenAPI documentation generated from type hints; the
  frontend codes against that contract, not against hand-written docs.

## Consequences

- Positive: one language for API + analytics + jobs; typed validation at every
  boundary; auto-generated docs; PKR 0.
- Negative: Python API throughput is lower than compiled-language frameworks
  (ESTIMATE, no benchmark run) — irrelevant at Phase 1 volumes, and the API is
  stateless so it can scale by adding processes if ever needed.
- Constraint: business logic lives in plain Python modules the API calls, never
  inside route handlers alone, so Celery workers and tests can call the same
  code without HTTP.

## Alternatives considered

- Django — rejected: full product framework; would duplicate SQLAlchemy as a
  second ORM.
- Flask — rejected: synchronous WSGI by default; typed validation and OpenAPI
  would be rebuilt by hand.
- Node/Express or NestJS backend — rejected: splits analytics across two
  languages; the analytics libraries are Python.

## Verification / open checks

- [ ] At Phase 2 setup: pin FastAPI/Pydantic/Uvicorn versions; read and record
  the Pydantic and Uvicorn LICENSE files (UNVERIFIED in Phase 1).
