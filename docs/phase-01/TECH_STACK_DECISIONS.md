# PSX Intelligence AI — Technology Stack Decisions (Phase 1, REVISED)

> Status: Phase 1 decision record only. **STOP AFTER PHASE 1.** No application code is
> written or implied by this document, and no Phase 2 work is started here.
> No sign-ups, installs, purchases, credentials, API keys, broker connections, live
> polling, trading, or posting were done to produce it.
>
> This is the **REVISED** version under the revised brief. It supersedes the first
> draft of this file in full. The changes are: budget is **PKR 0 absolute**; the
> stack is the **fixed stack** in §1 (no paid dependency may slip in); background
> processing is **Celery + Redis** (self-hosted, zero-cost); local inference is
> **Ollama, local only**; storage adds **local filesystem + Apache Parquet +
> optional self-hosted MinIO**; PDF extraction is **PyMuPDF + pypdf (fallback only)
> + Tesseract**; testing is **pytest + Playwright**; PyTorch is included only
> **where justified** (§2.8). Anything in the first draft that contradicts this
> version (notably APScheduler as primary, LiteLLM, and any external AI API) is
> withdrawn — see §10, Corrections.
>
> Marking convention:
> - **VERIFIED** — stated in the task's starting condition (checked 2026-11-04), in
>   the referenced scaffold `~/workspace/psx-data-collection/`, in this machine's
>   tool check (2026-11-04), or in a public page read for this task.
> - **ESTIMATE** — a reasoned judgement, not a measured benchmark. No benchmark in
>   this document was measured in this workspace.
> - **UNVERIFIED** — not yet checked. The check needed is named next to it.
>
> Version policy: **no library version is pinned in Phase 1.** The only versions
> recorded here are the runtimes actually present on this machine (VERIFIED below).
> Every other version is pinned for the first time at Phase 2 setup, in a lockfile,
> and that pinning step must read the package's own LICENSE file and record the
> licence actually shipped. Do not copy a version from a search snippet into a
> requirements file without installing and checking it.
>
> Cost policy (PKR 0 absolute): every dependency, tool, and service in §1 is
> PKR 0 in licence/subscription cost, evidenced in
> `ZERO_COST_REGISTER.md` (canonical) with a root summary at
> `~/workspace/psx-intelligence-ai/ZERO_COST_REGISTER.md`. **Local hardware,
> electricity, and internet are EXTERNAL operating expenses: they are disclosed,
> never called free.** No permanent free hosting is assumed anywhere in this
> document. If a future step would cost anything, it stops and needs a separate,
> explicit approval — it is not covered by this stack.

## 0. Verified starting facts (reused, not re-claimed)

- Project folder `~/workspace/psx-intelligence-ai/` is new; sibling teams may be
  creating sibling files. This team writes only the files listed in §9.
- Referenced, never modified: `~/workspace/psx-data-collection/` — stdlib
  `psx_collector.py` with provenance / PKT (Asia/Karachi) / stale / conflict rules,
  offline tests passing.
- Tools on this machine, checked 2026-11-04 (VERIFIED): Python 3.12.3, Node v24.22.1.
  Docker, `psql`, and `redis-cli` are **NOT installed** — the local-dev path in §7
  must therefore give both a Docker Engine path (Phase 2 setup installs it) and a
  no-Docker path, and must not pretend any of them is already present.
- psx-dps (VERIFIED): MIT, zero dependencies, no API key, ~496 trading symbols vs
  ~1,029 listed instruments, ~5 years EOD, today's ticks, 38 sectors, multi-node
  404 quirk, no official PSX API.
- psxdata (VERIFIED): MIT, PyPI, alpha 0.1.0a1, daily OHLCV + live snapshots ONLY,
  no historical intraday archive.
- Eulerpool: NO PSX coverage stated, vendor only, no paid API approved (VERIFIED).
  It is **not** in this stack.
- SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED machine-use is
  **UNVERIFIED** — no library or endpoint is invented for them anywhere in this stack.

## 1. Primary stack — the FIXED stack, one primary per component

| # | Component | PRIMARY (one only) | Role |
|---|---|---|---|
| 1 | Frontend framework | **Next.js (App Router) + React** | Web UI, routing, server rendering / static pages |
| 2 | Frontend language | **TypeScript** | Typed frontend code; shared API shapes |
| 3 | Styling | **Tailwind CSS** | Utility-first styling |
| 4 | UI components | **shadcn/ui** (components copied into the repo) | Accessible tables, dialogs, forms |
| 5 | Financial charting | **TradingView Lightweight Charts** | Candlestick / bar / line / area / volume rendering only — supplies no market data |
| 6 | Backend language | **Python 3.12** | All backend, analytics, PDF, and agent-tool code |
| 7 | Backend framework | **FastAPI + Uvicorn** | HTTP API; OpenAPI docs from type hints |
| 8 | Validation / schemas | **Pydantic v2** | Request/response models, shared with FastAPI |
| 9 | Production database | **PostgreSQL** (self-hosted) | System of record: prices, fundamentals, PDF metadata, jobs, audit |
| 10 | Local-dev database | **SQLite** (dev-only, see §7 — explicit, not silent) | Lets a developer run without PostgreSQL installed |
| 11 | ORM + migrations | **SQLAlchemy + Alembic** | One model definition; versioned migrations |
| 12 | Bulk / analytical storage | **Local filesystem + Apache Parquet (via PyArrow)** | Columnar files for OHLCV bulk exports, backtest frames, dataset snapshots |
| 13 | Object storage (OPTIONAL) | **Self-hosted MinIO, optional only, never required** | S3-compatible store for raw PDFs / payloads — see the MinIO warning in §2.6 |
| 14 | Background processing | **Celery + Redis (both self-hosted)** | Scheduled collection, PDF jobs, report jobs, retries, multi-worker later |
| 15 | Dataframes / numerics | **pandas + NumPy** | OHLCV frames, indicators, joins |
| 16 | Machine learning | **scikit-learn** | Regression / classification / clustering prototypes |
| 17 | Econometrics / time series | **statsmodels** | ARIMA-family, stationarity, regression diagnostics |
| 18 | Deep learning (CONDITIONAL) | **PyTorch — only where justified (§2.8)** | Not a default dependency; gated on a defined task classical models cannot do |
| 19 | PDF text extraction | **PyMuPDF (primary)** | Text-layer extraction from announcement / report PDFs |
| 20 | PDF fallback | **pypdf (fallback only)** | Invoked only when PyMuPDF fails on a document; failure + method logged |
| 21 | OCR (scanned PDFs only) | **Tesseract OCR** | Image/scanned pages only; a different role from text extraction, not a duplicate |
| 22 | Local LLM runtime | **Ollama — LOCAL inference only** | Runs open-weight models on the team's own machine; no cloud, no account |
| 23 | Open-weight model | **NO SPECIFIC MODEL PINNED in Phase 1** (see §2.9) | A model is chosen only by the ADR-007 evaluation gate, licence checked first |
| 24 | External AI API | **NONE. Prohibited in this stack.** | No provider, no key, no Ollama Cloud, no `:cloud` models, no paid tier |
| 25 | Agent orchestration | **Own small tool-calling loop** (not a framework agent) | Deterministic tool list, auditable calls; see ADR-010 |
| 26 | Testing | **pytest (backend) + Playwright (frontend E2E)** | Offline-first unit tests; browser tests against local dev only |
| 27 | Version control / CI | **Git + GitHub Free + GitHub Actions (within free limits)** | Source, PR checks, test gate; no paid tier, no permanent-free-hosting assumption |
| 28 | Deployment definition | **Docker Engine + Dockerfile / Compose (definition, Phase 2)** | Production packaging; local dev also has a no-Docker path (§7) |
| 29 | Logging (Phase 1) | **Python standard-library logging, JSON-structured** | One log format everywhere; no extra service |
| 30 | Monitoring (Phase 1) | **`/health` endpoint + structured logs + CI test gate** | No paid APM, no extra server |
| 31 | Package management | **pip + venv (Python); npm (Node, bundled with Node 24)** | No new installer assumed; `uv` etc. UNVERIFIED here |

No other library is added for the same role in Phase 1. In particular: no second
charting library, no second ORM, no second scheduler, no LangChain/LlamaIndex agent
framework, no LiteLLM (removed — with local-only Ollama there is no external
provider to abstract over), and no paid service of any kind.

## 2. Decisions and why

### 2.1 Frontend: Next.js + React + TypeScript

Next.js is a React framework, MIT-licensed, free and self-hostable (VERIFIED by
public page reads). React is the component model the task names; Next.js adds
file-based routing, server rendering, and static generation without a separate
backend-for-frontend. TypeScript catches shape mismatches between the FastAPI API
and the UI at build time — the exact class of bug that otherwise surfaces as a
wrong number on a financial screen. Node v24.22.1 is already installed (VERIFIED).

**Rejected:** plain React + Vite (loses server rendering and adds routing/build
choices for no Phase 1 gain); Vue/Nuxt, Angular (competent, but a second component
model against the fixed React direction); Streamlit as product UI (couples
presentation to the Python process; not the product UI asked for).

### 2.2 Styling + components: Tailwind CSS + shadcn/ui

Tailwind CSS is free and MIT-licensed (VERIFIED). shadcn/ui is MIT and is **not a
runtime dependency**: its CLI copies component source into the repo, which the team
then owns (VERIFIED). That removes version-lock-in for UI components.

**Caution (UNVERIFIED at setup — check required):** public pages read for this task
report shadcn/ui's default primitive changed from Radix UI to Base UI in July 2026.
Phase 2 setup must confirm which primitive the installed CLI actually uses and
record it; this document does not assert Radix.

**Rejected:** MUI (MIT core, but a heavy runtime dependency with its own styling
system; MUI X Pro/Premium are commercial — excluded by PKR 0); Ant Design /
Mantine (a second design system on top of Tailwind); Tailwind Plus / Tailwind UI
(paid kit — excluded by PKR 0); hand-rolled CSS only (reinvents accessible
dialogs/tables).

### 2.3 Charting: TradingView Lightweight Charts

The one charting library in the stack. Open source under Apache-2.0 (VERIFIED),
renders candlestick / bar / line / area / histogram (volume) on canvas, and takes
data the backend supplies — it does not fetch market data itself, which matches the
data-provenance rules. Indicators are computed in Python (pandas/NumPy) and handed
to the chart as series, so the chart stays a renderer, never a calculator.

**Licence duty (VERIFIED):** pages using it must carry the TradingView attribution
notice and a link to tradingview.com (the `attributionLogo` option exists for this).
Phase 2 must not disable that attribution.

**Rejected:** Recharts (SVG-based; ESTIMATE: degrades sooner than a canvas renderer
on long histories — judgement, no benchmark run); Apache ECharts (a larger general
charting system than a finance-first renderer for the same candlestick job);
Highcharts / TradingView Advanced Charts (proprietary/commercial — excluded by
PKR 0); a hand-rolled canvas chart (reinvents zoom, pan, crosshair).

### 2.4 Backend: Python 3.12 + FastAPI + Pydantic v2 + Uvicorn

Python 3.12.3 is already installed (VERIFIED). FastAPI is MIT-licensed, free, built
on Pydantic + Starlette (VERIFIED); it generates OpenAPI documentation from type
hints, giving the Next.js frontend a contract to code against. Pydantic v2 is
FastAPI's validation layer, and the same models validate API payloads, Celery job
payloads, and LLM tool arguments. Uvicorn is the ASGI server.

**Rejected:** Django (full product framework; would duplicate SQLAlchemy as a second
ORM); Flask (synchronous WSGI by default, no built-in typed validation/OpenAPI —
the team would rebuild what FastAPI provides); Node/Express or NestJS backend
(splits analytics code across two languages; pandas/scikit-learn/statsmodels are
Python, so the backend stays Python).

### 2.5 Database: PostgreSQL (production) + SQLAlchemy + Alembic; SQLite local-dev only

PostgreSQL is open source under a liberal, BSD-style licence, free for any purpose
including commercial use (VERIFIED). It is the production system of record for
typed, relational financial data with transactional guarantees, and scales from
one self-hosted instance to a managed instance without a data-model rewrite —
but no managed instance is assumed or budgeted in Phase 1; self-hosted is the plan.
SQLAlchemy is the single ORM; Alembic is its migration tool.

**Why SQLite locally — stated explicitly, never silently.** Docker, `psql`, and
`redis-cli` are not installed on this machine (VERIFIED). SQLite via SQLAlchemy
lets a developer run the API, migrations, and tests with zero services. This is a
development convenience with named limits (§7), not a second production database.

**Rejected as production primary:** SQLite itself (single-writer, no server story);
MySQL/MariaDB (no Phase 1 feature requires a second relational dialect);
MongoDB/document store (prices, fundamentals, audit records are naturally relational
and typed); TimescaleDB (a PostgreSQL extension, plausible later for very large
OHLCV volumes, but an added extension, not a Phase 1 requirement — see §8).

### 2.6 Bulk + object storage: local filesystem + Apache Parquet; MinIO optional only

**Parquet (VERIFIED Apache-2.0):** Apache Parquet is a free, open-source columnar
format (Apache-2.0), written/read in Python via PyArrow (Apache-2.0, VERIFIED from
its own documentation pages). Parquet files on the local filesystem are the bulk
layer: OHLCV exports, backtest frames, and dataset snapshots that do not need
row-by-row SQL. PostgreSQL remains the system of record; Parquet never silently
replaces it — a Parquet file is a derived export with its source query, date, and
row count recorded alongside it, and it can always be regenerated from PostgreSQL.

**MinIO — OPTIONAL ONLY, with a plain warning.** The fixed stack lists MinIO as
optional self-hosted object storage, and this document keeps it optional, never
required: the project works fully on local filesystem + PostgreSQL + Parquet
without MinIO. The warning, from public pages read for this task, is:
the open-source MinIO server repository was reported archived/read-only in
April 2026 ("no longer maintained"), with no further upstream fixes; the vendor's
current product is AIStor, whose Free tier is a proprietary single-server licence
requiring a licence key, and whose multi-node and maintained options are paid
(Docker Extended Lifecycle Support for MinIO was also reported as a paid
subscription). Consequences for this project:

- Do **not** adopt MinIO as a default or as a dependency of any core feature.
- Do **not** buy, request a paid tier for, or use Docker ELS for MinIO.
- If a future phase still wants S3-compatible storage, it must re-verify MinIO's
  status at that time, or evaluate a maintained free alternative, and record that
  decision separately. Until then, MinIO appears in the zero-cost register as
  OPTIONAL / NOT ADOPTED, and no MinIO code path is written in Phase 1.
- The safe default for raw PDFs/payloads is the local filesystem, under the same
  provenance rules as the scaffold (raw payloads stored separately from processed
  records).

**Rejected as bulk layer:** CSV-only bulk storage (no types, no compression, no
column pruning — Parquet dominates it on every axis that matters here); a managed
cloud bucket (S3/R2/GCS — usage-priced, excluded by PKR 0 and by the
no-permanent-free-hosting rule); a second columnar format alongside Parquet.

### 2.7 Background processing: Celery + Redis, both self-hosted (FIXED)

Celery is BSD-3-Clause (noted in public pages read). Redis is the broker and
result backend. **Redis licence — read carefully (VERIFIED by public pages read):**
Redis ≤ 7.2 was BSD-3-Clause; from 7.4 it moved to RSALv2 or SSPLv1 (neither
OSI-approved); Redis 8 (May 2025) added AGPLv3 as a third option, so Redis 8 is
tri-licensed RSALv2 / SSPLv1 / AGPLv3. Self-hosting Redis 8 costs PKR 0 in licence
fees under any of those options, but the options are not equivalent: RSALv2
restricts offering Redis as a managed service, SSPLv1 carries broad service-side
source obligations, and AGPLv3 requires publishing modifications if Redis is
modified and served over a network. This project does **not** modify Redis and
does **not** offer it as a managed service, so self-hosted use is PKR 0 — but
Phase 2 setup must record which licence option it is operating under, and must
not pick a managed/paid Redis service. A BSD-licensed fork (Valkey) exists and is
noted in ADR-004 as a licence-risk alternative; it is **not** the fixed-stack
primary, because the fixed stack names Redis, and swapping primaries without a
new decision would break the fixed stack. If the AGPL/RSAL terms ever become a
problem for this project's distribution model, that is a new decision, recorded
then, not a silent swap now.

**Why Celery + Redis, and why the first draft's APScheduler is withdrawn:**
the revised brief fixes Redis and requires a Redis-consistent background choice.
Celery gives durable tasks, retries, and multiple workers — the properties a
collection/PDF pipeline needs once it outgrows one process — and Redis is its
standard broker. The cost of that choice is honest: Redis and Celery are not
installed on this machine (VERIFIED for `redis-cli`; Celery install is a Phase 2
setup step), so §7 gives a Docker Engine path and a native-install path, and
Phase 1 runs no workers at all. APScheduler is demoted to "not used": keeping it
alongside Celery would be a second scheduler for the same jobs.

**Rejected as primary:** APScheduler alone (withdrawn — see above; in-process,
no durable retries across restarts, no multi-worker story); RQ / Dramatiq / arq
(each still needs Redis or another broker, and none is the fixed-stack choice —
Celery is); cron + shell scripts alone (no retries, no job state in the database,
no visibility from the API); a separate Node worker (splits job code across
languages).

### 2.8 Financial analytics: pandas + NumPy, scikit-learn, statsmodels, PyTorch (conditional)

One per sub-role: pandas + NumPy are the dataframe/numeric layer; scikit-learn is
the general ML layer; statsmodels is the econometrics/time-series layer. They are
complementary, not duplicates.

**PyTorch — only where justified.** PyTorch is in the fixed stack with the qualifier
"where justified", and this document enforces that qualifier: PyTorch is **not**
installed as a default Phase 1 dependency. It is added only when a Phase 2
specification names a concrete task (for example, a sequence model over OHLCV or
document embeddings) for which classical models have been tried and shown
insufficient on a defined metric — and that justification, plus its licence check
at install (UNVERIFIED in this document — record the LICENSE file actually
shipped), is written into the task spec before installation. Its licence and
cost are therefore recorded in the zero-cost register as CONDITIONAL, not as an
adopted default. Installing PyTorch "just in case" would add a large dependency
and GPU/CPU weight for no defined job.

**Rules binding all analytics (see ADR-010):** every financial number shown to a
user comes from a deterministic Python function over stored data, with inputs and
version recorded. These libraries compute; they do not narrate, and no LLM output
is ever parsed back into a number.

**Rejected as primary:** Polars (would split dataframe code across two APIs;
revisit only on a measured pandas bottleneck — none claimed); TensorFlow (a second
deep-learning framework alongside conditional PyTorch — never both);
hand-rolled indicator math in plain loops (slower, buggier, untestable against
library behaviour).

### 2.9 AI: Ollama, LOCAL inference only; no model pinned; no external API

**Ollama (VERIFIED MIT, local runtime free):** Ollama is MIT-licensed, free, and
runs open-weight models on the team's own machine with a local API, with no
account or subscription required for local use (VERIFIED by public pages read).
That local runtime is the whole AI story in this stack.

**What is prohibited, explicitly:** Ollama Cloud (reported paid tiers from
$20/month in public pages read — excluded), any `:cloud` model, any web-search
API requiring an Ollama sign-in, any external provider API, and any API key.
If a prompt, config, or doc in a later phase references a cloud model or a key,
it is a defect against this stack, not a feature.

**No specific open-weight model is pinned in Phase 1 — stated plainly.** Ollama
is a runtime, not a model; each model carries its own licence (for example,
public pages note some models ship under Apache-2.0 while others, such as Llama
family models, carry their own community licence and acceptable-use terms).
No model was benchmarked here, no GPU is budgeted, and naming a model (or a
version/quantisation of one) now would be invented. ADR-007 defines the
evaluation gate a model must pass in Phase 2 (PSX research tasks, tool-calling
accuracy, local hardware fit, licence compatibility) before it becomes the
primary. Until then, the stack runs fully without any LLM: every core feature
(data, indicators, computed reports) works with Ollama absent or with no model
downloaded, and LLM text is an optional research-draft layer on top.

**Agent orchestration: own small tool-calling loop.** The agent's tools are few
and auditable: search stored data, fetch a stored document, run a named
deterministic calculation, draft research text. A small loop over that fixed tool
list can log every call, its arguments, and its result — the audit trail ADR-010
requires. LangChain, LlamaIndex, and LiteLLM are **not** in this stack:
LangChain/LlamaIndex are large, fast-changing frameworks whose agent behaviour
would make that audit trail harder to guarantee, and LiteLLM exists to abstract
over external providers — with local-only Ollama there is no external provider to
abstract over, so it would be dead weight.

### 2.10 Infrastructure, testing, logging, monitoring

**Git + GitHub Free + GitHub Actions (within free limits).** Git is already the
version-control reality of this workspace; GitHub Free hosts it and Actions runs
the test gate. Two disclosures: (a) GitHub Free's exact limits (private-repo
collaborators, Actions minutes) are **UNVERIFIED** in this document — Phase 2
setup must confirm the current free tier and keep CI inside it, or run CI
locally; (b) **no permanent free hosting is assumed** — if GitHub's free tier
changed, the fallback is local git + local test runs, not a paid tier.

**Docker Engine + Dockerfile / Compose (definition, Phase 2).** Docker Engine on
Linux is the free, open-source container runtime for packaging the API, worker,
PostgreSQL, Redis, and (optionally) Ollama/MinIO consistently. Docker Desktop's
licence terms for organisations are a different product and are **UNVERIFIED**
here — do not assume Desktop terms; local dev on Linux uses Engine. The
Dockerfile/Compose files are written in Phase 2 as the production packaging
definition, but §7 also gives a no-Docker path, because Docker is not installed
on this machine today.

**Testing: pytest + Playwright.** pytest is the backend test runner (unit,
integration, and the offline-first pattern inherited from the scaffold: fake
clients, no network, no PSX call). Playwright is the frontend browser test runner
(E2E against local dev only). Playwright's licence is **UNVERIFIED** in this
document (record it at install); its cost is PKR 0 as distributed (browsers it
downloads are free builds — confirm at install, do not assume a vendor browser
licence). Testing strategy is **defined, not claimed passed**: no test suite for
this application exists yet, and this document claims no passing tests for it.
The scaffold's own offline tests passing is a property of the scaffold, not of
this project.

**Logging / monitoring (Phase 1).** Python standard-library logging, JSON
structured: one format, zero services. Monitoring is a `/health` endpoint (API
up, database reachable, last collection run timestamp, Celery worker heartbeat
when workers exist) plus those logs plus the CI gate. Rejected/deferred: any paid
APM or hosted logging (excluded by PKR 0); Prometheus + Grafana now (two more
services for metrics Phase 1 does not yet define — deferred to §8).

## 3. Compatibility matrix

"Compatible" means the combination is the normal, documented pairing, or was
verified on this machine. Anything else is marked.

| Pair | Compatible? | Note |
|---|---|---|
| Next.js + React + TypeScript | Yes (VERIFIED) | Next.js is a React framework; TypeScript is first-class |
| Next.js + Tailwind CSS + shadcn/ui | Yes (VERIFIED in outline) | shadcn/ui is built for Tailwind + React/Next.js; confirm primitive at setup (§2.2) |
| Next.js + Lightweight Charts | Yes | Plain npm package, canvas renderer; no server dependency |
| Next.js → FastAPI (HTTP/JSON) | Yes | Frontend calls the API over HTTP; OpenAPI contract from FastAPI |
| Python 3.12 + FastAPI + Pydantic v2 + Uvicorn | Yes (VERIFIED in outline) | FastAPI's documented stack; Python 3.12.3 present |
| FastAPI + SQLAlchemy + Alembic | Yes | Standard pairing; Alembic migrations run against the same models |
| SQLAlchemy + PostgreSQL | Yes | Production dialect; driver variant pinned at setup (UNVERIFIED which variant until then) |
| SQLAlchemy + SQLite | Yes, dev-only | Same models, different dialect; limits in §7 apply |
| FastAPI + Celery + Redis | Yes | API enqueues jobs; workers run the same Python code; Redis is broker + result backend |
| Celery + Redis 8 (tri-licensed) | Yes, with licence note | Record the licence option operated under (§2.7); no managed Redis service |
| pandas + NumPy + scikit-learn + statsmodels (+ PyTorch conditional) | Yes | All operate on NumPy arrays / pandas frames; shared Python 3.12 environment |
| PostgreSQL + Parquet (PyArrow) | Yes, distinct roles | PostgreSQL is system of record; Parquet is derived bulk export, regenerable |
| Local filesystem + (optional) MinIO | Yes, optional | MinIO, if ever used, is an S3-compatible front end over local disks; default is plain filesystem (§2.6 warning applies) |
| PyMuPDF → pypdf fallback → Tesseract (staged) | Yes | Sequential stages, never two extractors on the same page in the same run; method logged |
| Ollama (local API) + own tool loop | Yes | Ollama serves locally on the team's machine; the loop owns tools, logging, audit |
| Ollama + "no model" default | Yes, by design | With no model downloaded, LLM features are disabled, not broken |
| psx-dps / psxdata → collector → PostgreSQL/SQLite/Parquet | Yes, by design | Collector already enforces provenance/PKT/stale/conflict rules; this stack stores, never re-interprets, those fields |
| GitHub Actions + pytest + Playwright | Yes, within free limits | CI runs both suites; confirm free-tier limits at setup (§2.10); local runs are the fallback |
| Docker Engine + all above | Yes, Phase 2 | Compose packages API, worker, PostgreSQL, Redis, Ollama; local dev does not require it (§7) |

**Known incompatibilities / traps (do not work around silently):**

- SQLite ≠ PostgreSQL: type strictness, concurrent writes, and some SQL features
  differ. Any migration or query that passes on SQLite must be re-run against
  PostgreSQL before it is trusted (see §7).
- psxdata alpha 0.1.0a1 APIs may change before 1.0 (VERIFIED) — pin it at setup
  and isolate its calls behind one adapter module, so a breaking change touches
  one file.
- psx-dps multi-node 404 quirk (VERIFIED): a 404 from one DPS node is not "no
  data"; the library's node-probing behaviour must be preserved, never replaced
  with a single hard-coded node URL.
- Lightweight Charts major-version API differences (reported in public pages):
  series creation differs across major versions. Pin the installed major version
  at setup and write chart code against that version only.
- shadcn/ui primitive change (reported July 2026, §2.2): confirm at setup.
- Redis licence options (§2.7) and MinIO maintenance status (§2.6): re-verify at
  any adoption point; neither is a silent default.
- Ollama model licences differ per model (§2.9): check the chosen model's licence
  before download; Ollama's MIT licence does not transfer to the model weights.

## 4. What this stack deliberately does NOT contain (Phase 1)

- No broker connection, trading engine, or order path. Nothing in this stack can
  place an order, and no component is chosen "for trading".
- No real-time streaming stack (WebSockets/Kafka) in Phase 1. Market data arrives
  by scheduled collection with source timestamps; a quote is never labelled
  "real-time" merely because it was fetched recently (scaffold rule, inherited).
- No vector database in Phase 1. Document search, if needed, starts as PostgreSQL
  full-text search over extracted text; a vector store is a Phase 2 decision gated
  on a proven retrieval need, not a Day-1 dependency.
- No paid service of any kind, no external AI API, no managed database/queue/
  hosting, no Ollama Cloud, no MinIO paid tier, no Docker ELS. Every primary above
  is PKR 0 in licence/subscription cost as evidenced in `ZERO_COST_REGISTER.md`.
- No full-scale live data collection in Phase 1 (see §6, stage 4). Phase 1
  inspects data sources read-only and specifies collection; it does not run it.

## 5. Cost summary — PKR 0 absolute, with external expenses disclosed

- Licence/subscription cost of every dependency, tool, and service in §1:
  **PKR 0**, as itemised with evidence or UNVERIFIED marks in
  `ZERO_COST_REGISTER.md`. No item in that register requires payment.
- **EXTERNAL operating expenses (disclosed, never called free):** the local
  machine and its hardware wear, electricity to run it, and internet access to
  download packages/models and reach PSX sources. These are the operator's own
  existing costs; this document does not price them (no tariff or hardware cost
  was verified) and does not claim they are zero. A machine that is off collects
  nothing — that is a stated operating limit of a self-hosted PKR 0 stack.
- LLM spend: **PKR 0 by construction** (local Ollama, no model purchase, no API).
  Model downloads are free files; their cost is disk space, electricity, and
  time — external expenses above, not a licence fee.
- Human cost: the dominant cost in Phase 1 is maintenance of the PSX adapters
  (undocumented DPS endpoints can change without notice — VERIFIED) and of PDF
  formats per company. That maintenance load, not licence fees, is why the stack
  keeps adapters isolated and dependencies few.
- No permanent free hosting is assumed: if a host is ever needed beyond the
  team's own machine, it is a new, separately approved cost — not part of this
  stack, and not promised here.

## 6. Phase 1 workflow record — the 11 stages

This team followed the 11-stage workflow for Phase 1. The record below is what
actually happened, not a claim of work done by other teams.

1. **Brainstorm** — candidate components were listed from the brief (frontend,
   backend, database, queue, analytics, PDF, AI, infrastructure) before any
   selection, so rejected alternatives in the comparison document are real
   candidates, not straw men.
2. **Research** — public page reads only (licences and costs for Next.js, FastAPI,
   PostgreSQL, Celery, Lightweight Charts, shadcn/ui, Tailwind, Redis, Ollama,
   MinIO, Parquet/PyArrow). No benchmark was run; every performance claim that
   is not a page quote is marked ESTIMATE.
3. **Validate** — each primary was checked against the fixed stack, the PKR 0
   rule, and the verified starting facts. Items that failed validation were
   removed or demoted (see §10): APScheduler, LiteLLM, external AI APIs,
   MinIO-as-default, and any paid tier.
4. **Data inspection (read-only only)** — the existing scaffold
   (`~/workspace/psx-data-collection/`, its registry, README, and collector
   rules) was read; public README/portal claims were reused from the verified
   starting condition. **NO full-scale live data collection was performed in
   Phase 1 by this team, and none is authorised by this document.**
5. **Architecture planning** — §1–§3 of this document and the ADRs: one primary
   per component, compatibility matrix, storage tiers, and the deterministic /
   LLM boundary (ADR-010).
6. **Implementation specification** — this document specifies what Phase 2 builds
   (components, roles, interfaces, limits). It is a specification, not code, and
   Phase 2 is not started here.
7. **Documentation** — this file, `TECH_STACK_COMPARISON.md`, the ADRs, and
   `ZERO_COST_REGISTER.md` (+ root summary) are the Phase 1 documentation set.
8. **Testing strategy (defined, not claimed passed)** — pytest (offline-first,
   fake clients, no network) + Playwright (local-dev E2E). No test suite for
   this application exists yet; no passing tests are claimed for it. The
   scaffold's own offline tests passing is a property of the scaffold, not of
   this project.
9. **Independent audit** — after drafting, this team's files were re-read
   against the revised brief: every §1 item checked for a paid dependency, a
   cloud/API-key requirement, or a contradiction with the fixed stack. Findings
   became the corrections in §10. (Audit method: full re-read + keyword scan
   for paid/cloud/key terms; audit does not install or run anything.)
10. **Correction** — §10 lists every correction made after audit, including
    items withdrawn from the first draft. No correction was made silently.
11. **Checkpoint — STOP AFTER PHASE 1.** This document ends Phase 1 for this
    team. No Phase 2 code, setup, install, download, or live collection follows
    from it without a new, explicit instruction.

## 7. Local-dev path — Docker Engine path AND no-Docker path

Docker, `psql`, and `redis-cli` are not installed on this machine (VERIFIED), so
neither path below may be read as "already working". Both are Phase 2 setup
instructions, not actions performed in Phase 1.

**Path A — Docker Engine (primary service path, Phase 2 setup):**

```text
# Phase 2 setup installs Docker Engine (Linux, free/open-source runtime),
# then, from the repo root (Phase 2 layout — illustrative, not executed here):
docker compose up -d postgres redis
# PostgreSQL and Redis run as local containers; the API/worker run on the host
# or in containers per the Phase 2 Compose file. Ollama, if used, runs on the
# host (local inference) or in its own container — never in the cloud.
```

**Path B — no-Docker (fallback, uses only OS packages + venv + npm):**

```text
# Backend (from the repo root, Phase 2 layout — illustrative, not executed here)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt        # pinned at Phase 2 setup; not pinned here
# Native PostgreSQL and Redis installed via the OS package manager (Phase 2
# setup step), OR SQLite dev database (below) + Redis installed natively.
# DATABASE_URL points at a local SQLite file in dev, e.g. sqlite:///./dev.db
# (exact variable name is fixed at Phase 2 setup; the principle is: SQLite in dev only)
python -m uvicorn app.main:app --reload
celery -A app.worker worker --loglevel=info   # only once Redis is running

# Frontend (from the frontend directory, Phase 2 layout)
npm install
npm run dev

# Tests (offline-first, following the scaffold's pattern)
python -m pytest
npx playwright test   # against local dev only
```

**SQLite → PostgreSQL migration — explicit, not silent:**

1. The same SQLAlchemy models serve both dialects; no model is written
   "for SQLite" or "for PostgreSQL" separately.
2. Alembic migrations are authored once and **must be applied to a real
   PostgreSQL instance and pass tests there before any production release**,
   even if they passed on SQLite. A migration that passes only on SQLite is not
   done.
3. Known SQLite divergences the team must test for: weaker type enforcement,
   single-writer concurrency (a Celery worker + API in one process hide contention
   that PostgreSQL would surface), autoincrement/sequence behaviour, and any
   PostgreSQL-specific type or index (e.g. full-text search, JSONB) — which must
   be isolated behind a dialect check or avoided until PostgreSQL is the dev
   database too.
4. The switch itself is a configuration change (`DATABASE_URL`) plus a data
   migration step defined in Phase 2; it is never a silent code edit, and the
   production database is PostgreSQL from the first production deployment, even
   if developers keep SQLite on their laptops.
5. Trigger to make PostgreSQL the dev database too: the first time a developer
   hits a SQLite-only divergence, or when Celery workers run against production
   data — whichever comes first. At that point Docker Engine or a native
   PostgreSQL install becomes a documented dev prerequisite, decided then.

## 8. Migration notes (what changes later, and what triggers it)

| From → To | Trigger (the event that justifies it, not a date) | Notes |
|---|---|---|
| SQLite (dev) → PostgreSQL (dev too) | A SQLite-only divergence, or Celery workers against production data | See §7; production is PostgreSQL from Day 1 regardless |
| Local filesystem → MinIO (if ever) | A proven need for S3-compatible access (not a hypothetical) + fresh licence/status verification | MinIO status must be re-verified then (§2.6); no paid tier, ever, under PKR 0 |
| PostgreSQL full-text → vector store | A proven retrieval failure (not a hypothetical) on document search | Model/embeddings choice gated like ADR-007; local only |
| PostgreSQL → PostgreSQL + TimescaleDB | Measured OHLCV volume/latency problem on plain PostgreSQL | Extension, not a replacement; no benchmark claimed now |
| No model → one evaluated open-weight model (Ollama) | ADR-007 evaluation gate passes, licence checked | LLM features stay optional; core features never depend on them |
| No PyTorch → PyTorch | A specified task classical models demonstrably cannot do (§2.8) | Justification written into the task spec before install |
| psxdata alpha → psxdata stable (or a replacement adapter) | A breaking alpha change, or a verified better source | Adapter isolation (§3) limits the blast radius to one module |
| Stdlib JSON logs → hosted log aggregation | Never under PKR 0 unless a free self-hosted tool is separately justified | No vendor chosen now; grep + files are the Phase 1 answer |
| `/health` + logs → Prometheus + Grafana | The team defines SLIs worth alerting on | Both are free self-hosted tools; adoption is a new decision, not assumed |
| Single self-hosted host → any paid host | **Not part of this stack.** Requires a new budget decision | No provider is pre-selected; no permanent free hosting is assumed |

## 9. Files created by this team (Phase 1, Team 4 only)

- `docs/phase-01/TECH_STACK_DECISIONS.md` (this file)
- `docs/phase-01/TECH_STACK_COMPARISON.md`
- `docs/phase-01/ZERO_COST_REGISTER.md` (canonical zero-cost register)
- `ZERO_COST_REGISTER.md` (root summary, pointing to the docs version as canonical)
- `docs/phase-01/ADR/ADR-001-frontend-framework.md`
- `docs/phase-01/ADR/ADR-002-backend-framework.md`
- `docs/phase-01/ADR/ADR-003-database.md`
- `docs/phase-01/ADR/ADR-004-background-processing.md`
- `docs/phase-01/ADR/ADR-005-financial-analytics-libraries.md`
- `docs/phase-01/ADR/ADR-006-pdf-extraction.md`
- `docs/phase-01/ADR/ADR-007-llm-abstraction-and-open-models.md`
- `docs/phase-01/ADR/ADR-008-psx-data-libraries.md`
- `docs/phase-01/ADR/ADR-009-deployment-and-local-dev.md`
- `docs/phase-01/ADR/ADR-010-deterministic-calculations-vs-llm.md`
- `docs/phase-01/ADR/ADR-011-storage-tiers-parquet-minio.md`
- `docs/phase-01/ADR/ADR-012-testing-strategy.md`

No application code, no Phase 2 work, and no other team's files were created or
modified by this team. The referenced scaffold
(`~/workspace/psx-data-collection/`) was read only.

## 10. Corrections made under the revised brief (audit findings, not silent)

| # | First-draft position | Revised position | Reason |
|---|---|---|---|
| 1 | APScheduler (in-process) as background primary; Celery + Redis as "migration target" | **Celery + Redis (self-hosted) as primary**; APScheduler not used | Revised brief fixes Redis and requires a Redis-consistent choice |
| 2 | LiteLLM as LLM abstraction | **Removed.** Ollama local API directly + own tool loop | Local-only inference has no external provider to abstract over |
| 3 | External AI API "opt-in only" | **Prohibited.** No provider, key, or cloud tier | PKR 0 absolute + fixed local-only stack |
| 4 | Storage was PostgreSQL/SQLite only | **+ local filesystem + Apache Parquet; MinIO optional only** with §2.6 warning | Fixed stack |
| 5 | PDF: PyMuPDF primary, pypdf "not installed" | **PyMuPDF primary + pypdf fallback-only** | Fixed stack lists both; fallback role keeps one-primary-per-run |
| 6 | Testing was pytest + "frontend default runner" | **pytest + Playwright** | Fixed stack |
| 7 | PyTorch absent | **PyTorch conditional, where justified only** (§2.8) | Fixed stack qualifier enforced, not treated as a default |
| 8 | Cost described as "low-budget viable" | **PKR 0 absolute**; hardware/electricity/internet disclosed as external expenses, never called free; no permanent free hosting assumed | Revised brief |
| 9 | MinIO not mentioned | **MinIO optional, NOT ADOPTED, with maintenance warning** (§2.6) | Public pages report the community repo archived in 2026; adopting it silently would hide that risk |
| 10 | Redis described loosely as "the usual broker" | **Redis tri-licence (RSALv2/SSPLv1/AGPLv3) disclosed**; licence option to be recorded at setup; no managed service | Licence verification required by the revised brief |
| 11 | Ollama Cloud / paid tiers not addressed | **Explicitly prohibited**; local-only boundary stated | A paid tier "slipping in" via Ollama Cloud is the exact failure the revised brief forbids |
