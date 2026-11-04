# PSX Intelligence AI — Zero-Cost Register (Summary)

> **Phase 2 update (2026-11-04):** No paid dependency was introduced in Phase 2. Actually installed and licence-recorded in Phase 2: PostgreSQL 16.15, Redis 7.0.15 (BSD-3-Clause era), Docker Engine 29.1.3 (Apache-2.0, daemon only), Next.js 16.4.5 / React 19.3.0 / TypeScript 5.9.3 / Tailwind 4.3.4, FastAPI 0.162.0, Celery 5.6.3, SQLAlchemy 2.1.8, Alembic 1.20.1, psycopg 3.3.7, pytest 9.2.0, Vitest 3.2.4, Playwright 1.64.1 (package installed during audit; browser download/E2E outcome — see PHASE_2_TEST_REPORT.md). Full licence table: docs/phase-02/LICENSE_REGISTER.md + backend/LICENCES.md. Paid services introduced in Phase 2: ZERO.

> **This is a summary only. The canonical register is
> `docs/phase-01/ZERO_COST_REGISTER.md` — if the two ever disagree, the docs
> version wins.**
>
> Budget: **PKR 0 absolute** for every dependency, tool, and service in the fixed
> Phase 1 stack (Next.js/React/TypeScript/Tailwind/shadcn; Python/FastAPI/Pydantic;
> PostgreSQL/SQLAlchemy/Alembic; local filesystem + Apache Parquet + optional
> self-hosted MinIO; Celery + Redis, both self-hosted; Ollama local-only;
> pandas/NumPy/scikit-learn/statsmodels/PyTorch-where-justified;
> PyMuPDF/pypdf/Tesseract; pytest/Playwright; Git/GitHub Free/Docker Engine).
>
> **Confirmation:** the canonical register contains **no paid dependency**.
> Every item is PKR 0 in licence/subscription cost as evidenced there, except:
>
> - **MinIO** — OPTIONAL and NOT ADOPTED (community build reported archived in
>   2026; vendor AIStor Free is proprietary/key-gated; no paid tier is used).
> - **PyTorch** — CONDITIONAL only, where justified in writing.
> - **A specific open-weight model** — NONE PINNED in Phase 1 (licence varies per
>   model; gated by ADR-007).
> - Items whose LICENSE files were not read for this task are marked UNVERIFIED
>   in the canonical register and must be licence-checked at Phase 2 setup before
>   installation; if any required payment, it would stop and be replaced.
>
> **Explicitly excluded:** external AI APIs, Ollama Cloud / `:cloud` models,
> managed databases/queues/buckets/hosts, paid PDF/APM/hosting services, paid UI
> or charting kits, vendor data APIs, and MinIO/AIStor paid tiers / Docker ELS.
>
> **External operating expenses (disclosed, never called free):** local hardware,
> electricity, and internet access. No permanent free hosting is assumed. A
> machine that is off collects nothing.
>
> See the canonical register for the full item-by-item table with licences,
> evidence, and maintenance rules:
> [`docs/phase-01/ZERO_COST_REGISTER.md`](docs/phase-01/ZERO_COST_REGISTER.md).
