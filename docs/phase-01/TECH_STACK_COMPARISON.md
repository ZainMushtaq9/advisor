# PSX Intelligence AI — Technology Stack Comparison (Phase 1, REVISED)

> Companion to `TECH_STACK_DECISIONS.md`. This file compares; that file decides.
> Same marking convention: **VERIFIED** (starting condition 2026-11-04, scaffold,
> this machine's tool check, or a public page read for this task),
> **ESTIMATE** (reasoned judgement, no benchmark measured here),
> **UNVERIFIED** (not yet checked; the check needed is named).
>
> No version is pinned in Phase 1. No benchmark in this file was measured in this
> workspace. "PKR 0" means PKR 0 in licence/subscription cost; local hardware,
> electricity, and internet are external operating expenses, disclosed in
> `TECH_STACK_DECISIONS.md` §5 and in `ZERO_COST_REGISTER.md`, and never called
> free. No permanent free hosting is assumed.
>
> The eight comparison dimensions, in every table:
> **Cost · Open-source status · Performance · Complexity · Scalability ·
> Maintenance · Compatibility · Deployment requirements.**

## 1. Frontend framework + language

| Option | Cost | Open-source | Performance | Complexity | Scalability | Maintenance | Compatibility | Deployment | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **Next.js + React + TypeScript (PRIMARY)** | PKR 0; MIT (VERIFIED) | Open source, MIT (VERIFIED) | ESTIMATE: server rendering + static generation suit dashboard pages; no benchmark run | Medium — one framework, file routing, typed code | Good — self-host on any Node host; scales by adding hosts | Active upstream; team owns app code | React ecosystem; Tailwind; shadcn/ui; Node 24 present (VERIFIED) | Node host; Docker optional | **PRIMARY** |
| Plain React + Vite | PKR 0 (UNVERIFIED licence detail — confirm at install) | Open source (general knowledge, licence UNVERIFIED here) | ESTIMATE: client-rendered; slower first paint than SSR for content pages | Lower framework, but routing/build chosen by hand | Good | Active | React ecosystem | Node host / static host | Rejected — loses SSR/static without a Phase 1 gain |
| Vue + Nuxt | PKR 0 (UNVERIFIED licence detail) | Open source (licence UNVERIFIED here) | ESTIMATE: comparable for this workload; no benchmark run | Medium — a second component model for this team | Good | Active | Vue ecosystem, not React | Node host | Rejected — splits component model against the fixed React direction |
| Angular | PKR 0 (UNVERIFIED licence detail) | Open source (licence UNVERIFIED here) | ESTIMATE: comparable; heavier framework for a dashboard | Higher — opinionated, larger API surface | Good | Active | Angular ecosystem | Node host | Rejected — heavier than needed; not the fixed direction |
| Streamlit (as product UI) | PKR 0 (UNVERIFIED licence detail) | Open source (licence UNVERIFIED here) | ESTIMATE: fine for prototypes; weak for a multi-page product UI | Low to start, high to productise | Poor as product UI — couples UI to one Python process | Active | Python only | Python host | Rejected as product UI — prototype tool, not the product |

## 2. Styling + UI components

| Option | Cost | Open-source | Performance | Complexity | Scalability | Maintenance | Compatibility | Deployment | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **Tailwind CSS + shadcn/ui (PRIMARY)** | PKR 0; both MIT (VERIFIED) | Open source, MIT (VERIFIED); shadcn/ui is copied source, not a runtime dependency (VERIFIED) | ESTIMATE: purged utility CSS keeps bundles small | Low–medium; components owned in-repo | Good — no runtime version lock for components | Team owns copied components; upstream is a source of new copies, not a forced upgrade | Next.js/React; confirm primitive (Radix vs Base UI, reported July 2026 switch) at setup — UNVERIFIED until then | Bundled with the app; nothing extra | **PRIMARY** |
| MUI core | PKR 0 core, MIT (reported; licence UNVERIFIED here) | Open source core | ESTIMATE: heavier runtime + CSS-in-JS cost | Medium | Good | Active | React | Bundled | Rejected — heavier runtime + own styling system; X Pro/Premium are commercial (excluded by PKR 0) |
| Ant Design / Mantine | PKR 0 core (UNVERIFIED licence detail) | Open source (licence UNVERIFIED here) | ESTIMATE: comparable | Medium | Good | Active | React | Bundled | Rejected — a second design system on top of Tailwind |
| Tailwind Plus / Tailwind UI | Paid kit | Commercial | n/a | n/a | n/a | Vendor | Tailwind | n/a | **Excluded — paid, violates PKR 0** |
| Hand-rolled CSS only | PKR 0 | n/a | ESTIMATE: small CSS, but accessible components must be built by hand | High for accessible dialogs/tables | Good | All on the team | Any | Bundled | Rejected — reinvents accessible components |

## 3. Financial charting

| Option | Cost | Open-source | Performance | Complexity | Scalability | Maintenance | Compatibility | Deployment | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **TradingView Lightweight Charts (PRIMARY)** | PKR 0; Apache-2.0 (VERIFIED) | Open source, Apache-2.0 (VERIFIED) | ESTIMATE: canvas renderer built for long financial series; no benchmark run | Low — series API; indicators computed in Python, not in the chart | Good — client-side; server only serves series data | Active; pin major version at setup (v4/v5 API differs — reported) | Any frontend via npm; requires TradingView attribution + tradingview.com link on chart pages (VERIFIED duty) | Bundled with frontend | **PRIMARY** |
| Recharts | PKR 0 (UNVERIFIED licence detail) | Open source (licence UNVERIFIED here) | ESTIMATE: SVG; degrades sooner on long histories — judgement, no benchmark | Low for simple charts | Moderate client-side | Active | React-native | Bundled | Rejected — wrong renderer class for long candlestick histories |
| Apache ECharts | PKR 0 (UNVERIFIED licence detail) | Open source (licence UNVERIFIED here) | ESTIMATE: strong, canvas/SVG; larger system | Medium — larger API surface | Good | Active | Any frontend | Bundled | Rejected — more general system than needed for finance-first rendering |
| Highcharts / TradingView Advanced Charts | Commercial / proprietary | Proprietary | n/a | n/a | n/a | Vendor | n/a | Licence-gated | **Excluded — paid/proprietary, violates PKR 0** |
| Hand-rolled canvas chart | PKR 0 | n/a | ESTIMATE: only as good as the team's chart code | High — zoom, pan, crosshair, time axis all hand-built | Poor | All on the team | Any | Bundled | Rejected — reinvents the renderer |

## 4. Backend framework + validation

| Option | Cost | Open-source | Performance | Complexity | Scalability | Maintenance | Compatibility | Deployment | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **Python 3.12 + FastAPI + Pydantic v2 + Uvicorn (PRIMARY)** | PKR 0; FastAPI MIT (VERIFIED); Python 3.12.3 present (VERIFIED) | Open source (FastAPI MIT VERIFIED; Pydantic/Uvicorn licences UNVERIFIED here — confirm at install) | ESTIMATE: ASGI + typed validation is among the faster Python API stacks; no benchmark run | Low–medium; OpenAPI generated from type hints | Good — stateless API processes behind any host | Active | SQLAlchemy, Celery, pandas stack — all Python | Any Python host; Docker optional | **PRIMARY** |
| Django | PKR 0 (UNVERIFIED licence detail) | Open source (licence UNVERIFIED here) | ESTIMATE: comparable for an API; heavier per request than a thin API framework (no benchmark) | Higher — full product framework | Good | Active | Own ORM (would duplicate SQLAlchemy) | Python host | Rejected — more than an API needs; second ORM |
| Flask | PKR 0 (UNVERIFIED licence detail) | Open source (licence UNVERIFIED here) | ESTIMATE: synchronous WSGI by default; slower under concurrent I/O (no benchmark) | Low, but validation/OpenAPI rebuilt by hand | Good with ASGI wrappers | Active | Python | Python host | Rejected — team would rebuild FastAPI's typed validation + docs |
| Node/Express or NestJS backend | PKR 0 (UNVERIFIED licence detail) | Open source (licence UNVERIFIED here) | ESTIMATE: fast for I/O; analytics libraries are Python, so data work would cross languages | Medium — second language for the backend | Good | Active | Node ecosystem, not the Python analytics stack | Node host | Rejected — splits analytics across languages |

## 5. Database, ORM, migrations, bulk + object storage

| Option | Cost | Open-source | Performance | Complexity | Scalability | Maintenance | Compatibility | Deployment | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **PostgreSQL + SQLAlchemy + Alembic (PRIMARY, production)** | PKR 0; PostgreSQL liberal BSD-style licence, free incl. commercial use (VERIFIED); SQLAlchemy/Alembic licences UNVERIFIED here | Open source | ESTIMATE: strong for relational + transactional financial data; no benchmark run | Medium — typed models + versioned migrations | Good — one host to managed instance (managed instance itself NOT assumed/budgeted) | Active; migrations reviewable | Python/SQLAlchemy; Parquet exports derived from it | Self-hosted; Docker or native install (Phase 2 setup) | **PRIMARY (production)** |
| SQLite (dev only) | PKR 0 (licence UNVERIFIED here) | Public-domain-style (UNVERIFIED here — confirm at install) | ESTIMATE: ample for one developer; single-writer | Low — zero services | Poor — not a production server story | Minimal | Same SQLAlchemy models; dialect divergences must be tested (§7 of Decisions) | File on disk; nothing to install | **Dev-only, explicit — never production** |
| MySQL / MariaDB | PKR 0 (UNVERIFIED licence detail) | Open source (licence UNVERIFIED here) | ESTIMATE: comparable for this workload | Medium — second dialect to test | Good | Active | SQLAlchemy supports it | Self-hosted | Rejected — no Phase 1 feature requires a second dialect |
| MongoDB / document store | PKR 0 self-hosted community terms (UNVERIFIED licence detail — SSPL terms must be read before any use) | Source-available, not permissive (UNVERIFIED here) | ESTIMATE: strong for documents; weak for typed relational constraints | Medium | Good | Active | Not the natural model for prices/audit | Self-hosted | Rejected — trades away relational constraints Phase 1 needs |
| TimescaleDB | PKR 0 for the extension's community terms (UNVERIFIED — read licence before any use) | Extension of PostgreSQL (licence UNVERIFIED here) | ESTIMATE: better for very large time-series volumes; no measured need now | Medium — an extension to operate | Good | Active | PostgreSQL | Self-hosted | Deferred — only on a measured OHLCV bottleneck |
| **Local filesystem + Apache Parquet via PyArrow (PRIMARY, bulk)** | PKR 0; Parquet + PyArrow Apache-2.0 (VERIFIED) | Open source, Apache-2.0 (VERIFIED) | ESTIMATE: columnar + compressed; column pruning beats CSV for analytics reads | Low — files + recorded provenance | Good for bulk exports/snapshots; not a query server | Active (Apache Arrow) | pandas/PyArrow; regenerated from PostgreSQL | Local disk; nothing extra | **PRIMARY (bulk/derived)** |
| CSV-only bulk storage | PKR 0 | n/a | ESTIMATE: no types, no compression, full scans | Low | Poor for large frames | None | Universal, but lossy | Local disk | Rejected — Parquet dominates it for analytics |
| **Self-hosted MinIO (OPTIONAL ONLY, NOT ADOPTED)** | PKR 0 licence fee for archived AGPLv3 community build; vendor AIStor Free is proprietary single-server with a licence key (VERIFIED in outline — see warning) | AGPLv3 community build reported archived/read-only April 2026, no upstream fixes (reported, VERIFIED in outline); AIStor is proprietary, not open source | ESTIMATE: S3-compatible, fast on local disks | Medium — a server to operate + licence-key flow for AIStor | Good in principle; single-server for the free tier | **At risk — community build unmaintained (reported)** | S3 API; local disks | Self-hosted server | **OPTIONAL ONLY, NOT ADOPTED — see Decisions §2.6. No paid tier, no Docker ELS.** |
| Managed cloud bucket (S3/R2/GCS) | Usage-priced | Vendor service | ESTIMATE: strong, but metered | Low to start | Excellent | Vendor | S3 APIs | Vendor account | **Excluded — paid + assumes hosted service; violates PKR 0** |

## 6. Background processing

| Option | Cost | Open-source | Performance | Complexity | Scalability | Maintenance | Compatibility | Deployment | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **Celery + Redis, both self-hosted (PRIMARY, FIXED)** | PKR 0 licence fee; Celery BSD-3-Clause (noted in public pages); Redis 8 tri-licensed RSALv2/SSPLv1/AGPLv3 (VERIFIED) — record the option operated under at setup; no managed service | Celery open source; Redis source-available/open under the chosen option — **not permissive BSD for current versions** (VERIFIED) | ESTIMATE: durable tasks, retries, multi-worker; no benchmark run | Medium — broker + workers to operate | Good — add workers/hosts | Active (both); PSX adapter churn is the real maintenance load | Python; FastAPI enqueues; Redis as broker + result backend | Self-hosted Redis + worker processes; Docker or native install (Phase 2 setup). Redis NOT installed on this machine (VERIFIED) — setup step, not assumed present | **PRIMARY** |
| APScheduler (in-process) | PKR 0 (UNVERIFIED licence detail) | Open source (licence UNVERIFIED here) | ESTIMATE: fine for one process | Low — no broker | Poor — no durable retries across restarts, no multi-worker | Active | Python; in-process only | Nothing extra | Rejected as primary — withdrawn under the revised brief; a second scheduler alongside Celery would duplicate the role |
| RQ / Dramatiq / arq | PKR 0 (UNVERIFIED licence detail each) | Open source (licence UNVERIFIED here) | ESTIMATE: comparable for queue work | Low–medium; still need a broker | Good with Redis | Active | Python + Redis (or other broker) | Self-hosted broker | Rejected — each needs a broker anyway, and none is the fixed-stack choice |
| cron + shell scripts | PKR 0 | OS tooling | ESTIMATE: adequate for trivial schedules | Low, but no retries/state/visibility | Poor | OS | Any | Host cron | Rejected — no job state, retries, or API visibility |
| Valkey (as broker, alternative) | PKR 0; BSD-3-Clause (VERIFIED in outline) | Open source, BSD-3-Clause, Linux Foundation fork of Redis 7.2.4 (VERIFIED in outline) | ESTIMATE: Redis-compatible for Celery's broker use | Low swap cost for broker use | Good | Active | Celery speaks the Redis protocol | Self-hosted | **Noted licence-risk alternative only — NOT the primary**, because the fixed stack names Redis. A swap is a new decision, not a silent change (see ADR-004) |

## 7. Financial analytics

| Option | Cost | Open-source | Performance | Complexity | Scalability | Maintenance | Compatibility | Deployment | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **pandas + NumPy (PRIMARY, dataframes/numerics)** | PKR 0 (licences UNVERIFIED here — confirm at install) | Open source (licence UNVERIFIED here) | ESTIMATE: vectorised; ample for PSX EOD + indicator workloads; no benchmark run | Low–medium | Good for Phase 1 volumes; revisit on a measured bottleneck | Active | scikit-learn, statsmodels, PyArrow | Python env | **PRIMARY** |
| **scikit-learn (PRIMARY, general ML)** | PKR 0 (licence UNVERIFIED here) | Open source (licence UNVERIFIED here) | ESTIMATE: strong for tabular models | Low–medium; pipelines + cross-validation built in | Good for Phase 1 | Active | pandas/NumPy | Python env | **PRIMARY** |
| **statsmodels (PRIMARY, econometrics/time series)** | PKR 0 (licence UNVERIFIED here) | Open source (licence UNVERIFIED here) | ESTIMATE: the ARIMA/diagnostics layer scikit-learn does not specialise in | Medium | Good for Phase 1 | Active | pandas/NumPy | Python env | **PRIMARY** |
| **PyTorch (CONDITIONAL only, where justified)** | PKR 0 as distributed (licence UNVERIFIED here — record LICENSE at install) | Open source (licence UNVERIFIED here) | ESTIMATE: needed only for sequence/deep models; heavy for tabular work | High — large dependency, device/CPU/GPU considerations | Good, but weight unjustified without a task | Active | Python; NumPy interop | Python env (+ optional GPU — none budgeted) | **CONDITIONAL — only on a written justification + a task classical models demonstrably cannot do** |
| Polars | PKR 0 (licence UNVERIFIED here) | Open source (licence UNVERIFIED here) | ESTIMATE: faster than pandas on large frames (no benchmark run here) | Medium — second dataframe API | Good | Active | Python; not pandas-identical | Python env | Rejected as primary — would split dataframe code across two APIs |
| TensorFlow | PKR 0 (licence UNVERIFIED here) | Open source (licence UNVERIFIED here) | ESTIMATE: strong for deep learning; unnecessary weight for Phase 1 | High | Good | Active | Python | Python env | Rejected — a second deep-learning framework alongside conditional PyTorch; never both |
| Hand-rolled loops for indicators | PKR 0 | n/a | ESTIMATE: slower and buggier than vectorised libraries | High to get right | Poor | All on the team | Any | n/a | Rejected |

## 8. PDF extraction + OCR

| Option | Cost | Open-source | Performance | Complexity | Scalability | Maintenance | Compatibility | Deployment | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **PyMuPDF (PRIMARY, text layer)** | PKR 0 (licence UNVERIFIED here — PyMuPDF's licence terms must be read at install; do not assume) | Open source (licence UNVERIFIED here) | ESTIMATE: fast text extraction for report/announcement PDFs | Low | Good — per-document jobs via Celery | Active | Python; PDF text layer | Python env | **PRIMARY (text)** |
| **pypdf (FALLBACK ONLY)** | PKR 0 (licence UNVERIFIED here) | Open source (licence UNVERIFIED here) | ESTIMATE: adequate as a fallback; not chosen for speed | Low | Good as fallback | Active | Python | Python env | **FALLBACK ONLY — invoked only on PyMuPDF failure; method logged. Not a parallel primary.** |
| **Tesseract OCR (PRIMARY, scanned pages only)** | PKR 0 (licence UNVERIFIED here) | Open source (licence UNVERIFIED here) | ESTIMATE: slower than text extraction; acceptable for scanned pages via Celery jobs | Medium — binary + language data must be present | Good via workers | Active | Python via wrapper; binary install is a setup step — binary presence UNVERIFIED on this machine | Python env + Tesseract binary + language data (check at setup) | **PRIMARY (OCR only — different role, not a duplicate extractor)** |
| pdfplumber / Camelot / Tabula (as primaries) | PKR 0 (UNVERIFIED licence detail each) | Open source (licence UNVERIFIED here) | ESTIMATE: strong for tables specifically | Medium | Good | Active | Python/Java (Tabula) | Extra runtimes for Tabula | Rejected as primaries — table extraction is a later per-document problem, not the general job |
| Paid PDF API | Paid | Vendor service | n/a | n/a | n/a | Vendor | API | Account + key | **Excluded — paid, violates PKR 0** |
| LLM "reads the PDF" as extractor of record | PKR 0 locally, but see ADR-010 | n/a | ESTIMATE: unreliable for exact financial numbers | High to audit | Poor auditability | n/a | n/a | n/a | **Prohibited as extractor of record — ADR-010** |

## 9. AI: runtime, models, orchestration

| Option | Cost | Open-source | Performance | Complexity | Scalability | Maintenance | Compatibility | Deployment | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **Ollama, LOCAL inference only (PRIMARY runtime)** | PKR 0 local; MIT (VERIFIED); paid Cloud tiers exist and are **excluded** | Open source, MIT (VERIFIED) for the runtime; **each model carries its own licence** (VERIFIED — check before download) | ESTIMATE: local CPU/GPU-bound; small models usable on CPU, larger need GPU (no benchmark run; no GPU budgeted) | Low — single binary + local API | Limited by local hardware — a stated limit, not a hidden one | Active | Local HTTP API; own tool loop | Team's own machine; no account, no key, no `:cloud` model, no web-search API | **PRIMARY (runtime)** |
| Open-weight model (specific) | PKR 0 download (model licence varies) | Varies per model — **UNVERIFIED until a model is named and its licence read** | UNVERIFIED — no model benchmarked here | n/a | Local-hardware-bound | Upstream per model | Ollama | Local disk + RAM/VRAM | **NO PRIMARY JUSTIFIED in Phase 1 — gated by ADR-007 evaluation. Naming one now would be invented.** |
| LiteLLM (abstraction) | PKR 0 (licence UNVERIFIED here) | Open source (licence UNVERIFIED here) | ESTIMATE: thin abstraction overhead | Low, but dead weight with no external provider | n/a | Active | Providers | Python env | Rejected — abstracts over external providers; this stack has none |
| LangChain / LlamaIndex agents | PKR 0 (UNVERIFIED licence detail each) | Open source (licence UNVERIFIED here) | ESTIMATE: capable, but agent behaviour is harder to audit | High — large, fast-changing frameworks | Good | High churn | Python | Python env | Rejected — own tool loop gives the audit trail ADR-010 requires, with less churn |
| **Own small tool-calling loop (PRIMARY orchestration)** | PKR 0 | Project code | ESTIMATE: trivial overhead; tools are the cost, not the loop | Low — fixed tool list | Good for the defined tool set | Team-owned; small surface | Ollama local API; deterministic Python tools | In the backend | **PRIMARY** |
| External AI API (any provider) | Usage-priced / subscription | Vendor service | n/a | n/a | n/a | Vendor | API + key | Account + key | **Prohibited in this stack — violates PKR 0 absolute + local-only rule** |
| Ollama Cloud / `:cloud` models / cloud web search | Reported paid tiers from $20/month (public pages read) | Vendor service | n/a | n/a | n/a | Vendor | Account + sign-in | Cloud | **Prohibited — same reason; local runtime stays free, cloud is a separate paid product** |

## 10. PSX data libraries

| Option | Cost | Open-source | Performance | Complexity | Scalability | Maintenance | Compatibility | Deployment | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **psx-dps (PRIMARY market data)** | PKR 0; MIT, no API key (VERIFIED) | Open source, MIT (VERIFIED) | ESTIMATE: whole-market snapshot in one request (per README claim); 1 req/s cross-process limit claimed | Low — zero dependencies; multi-node 404 quirk must be preserved, never hard-coded around | Good for snapshot/EOD/today's ticks; not a historical intraday archive | Unofficial, unaffiliated; endpoints can change without notice (VERIFIED) — adapter isolation required | Python; collector's provenance/PKT/stale/conflict rules | Python env; no key | **PRIMARY** |
| **psxdata (BACKUP market/EOD)** | PKR 0; MIT, PyPI (VERIFIED) | Open source, MIT (VERIFIED) | ESTIMATE: daily OHLCV + live snapshots; historical cached, live 15 min (per README claim) | Low–medium; alpha APIs may change | Good for daily history | Alpha 0.1.0a1 (VERIFIED) — APIs may change before 1.0 | Python 3.11+ (per README claim); pin at setup | Python env; no key | **BACKUP — daily OHLCV + live snapshots ONLY; no historical intraday archive (VERIFIED limit)** |
| Eulerpool / any vendor API | Free tier claimed, paid tiers beyond; no PSX coverage stated | Vendor | n/a | n/a | n/a | Vendor | n/a | Account | **Excluded — no PSX coverage stated, no paid API approved** |
| Official PSX API | None exists publicly (per psx-dps FAQ, VERIFIED in outline) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | Not available — hence unofficial libraries + mandatory fallback |
| SECP/SBP/PBS/Finance Division/World Bank/IMF/FRED machine-use | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | **Not in the stack — no library/endpoint invented for them** |

## 11. Infrastructure, testing, logging, monitoring

| Option | Cost | Open-source | Performance | Complexity | Scalability | Maintenance | Compatibility | Deployment | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **Git + GitHub Free + GitHub Actions within free limits (PRIMARY)** | PKR 0 for the Free tier (exact limits UNVERIFIED — confirm at setup; no permanent free hosting assumed) | Git open source; GitHub is a vendor free tier, not open source | ESTIMATE: ample for Phase 1 CI | Low | Good within free limits; local git + local runs are the fallback | Vendor (tier terms can change — hence the fallback) | git everywhere | Vendor-hosted + local fallback | **PRIMARY, with the free-limits check as a setup step** |
| **Docker Engine + Dockerfile/Compose (PRIMARY packaging)** | PKR 0 for Engine on Linux (Docker Desktop terms UNVERIFIED — different product, do not assume) | Engine open source (licence UNVERIFIED here — confirm at install) | ESTIMATE: container overhead negligible for this workload | Medium — Compose for postgres/redis/ollama | Good — same artefacts from laptop to host | Active | All stack components | Linux host; Engine install is a Phase 2 setup step (NOT installed on this machine — VERIFIED) | **PRIMARY (packaging); local dev also has a no-Docker path** |
| **pytest (PRIMARY backend testing)** | PKR 0 (licence UNVERIFIED here) | Open source (licence UNVERIFIED here) | ESTIMATE: fast for offline unit tests | Low | Good | Active | Python; offline-first pattern from the scaffold | Python env | **PRIMARY — strategy defined, no passing suite claimed for this app yet** |
| **Playwright (PRIMARY frontend E2E)** | PKR 0 as distributed (licence UNVERIFIED here — confirm at install, incl. downloaded browsers) | Open source (licence UNVERIFIED here) | ESTIMATE: real-browser tests are slower than unit tests; run against local dev only | Medium | Good for E2E scope | Active | Browsers; Next.js dev server | Local dev only | **PRIMARY (E2E)** |
| Python stdlib JSON logging + `/health` + CI gate (PRIMARY observability) | PKR 0 | Stdlib | ESTIMATE: sufficient for one host | Low | Poor beyond one host — accepted for Phase 1 | Minimal | Everywhere | Nothing extra | **PRIMARY (Phase 1)** |
| Prometheus + Grafana | PKR 0 self-hosted (licences UNVERIFIED here) | Open source (licence UNVERIFIED here) | ESTIMATE: strong, but two more services | Medium | Good | Active | Any | Self-hosted servers | Deferred — only once SLIs are defined |
| Paid APM / hosted logging | Paid | Vendor service | n/a | n/a | n/a | Vendor | n/a | Account | **Excluded — paid, violates PKR 0** |
| Kubernetes | PKR 0 self-hosted (licence UNVERIFIED here) | Open source (licence UNVERIFIED here) | ESTIMATE: strong at scale; heavy for one host | High | Excellent | High | Containers | Cluster | Rejected — orchestration for a scale Phase 1 does not have |

## 12. Items where no primary could be justified (stated plainly)

1. **A specific open-weight model.** No model was benchmarked, no GPU is budgeted,
   and model licences vary per model. Ollama (runtime) is primary; the model is
   not. See ADR-007 for the evaluation gate.
2. **A managed host / managed PostgreSQL / managed Redis.** No provider, price,
   or free tier is assumed permanent. Self-hosting on the team's own machine is
   the plan; any paid host is a new decision.
3. **SECP / SBP / PBS / Finance Division / World Bank / IMF / FRED machine
   interfaces.** UNVERIFIED — no library or endpoint is claimed for them.
4. **Exact library versions.** Nothing is pinned in Phase 1; pinning happens at
   Phase 2 setup with the LICENSE file actually shipped recorded.
5. **Any performance ranking beyond ESTIMATE.** No benchmark was run in this
   workspace; every performance cell above that is not a quoted page claim is
   judgement, and is marked ESTIMATE.
