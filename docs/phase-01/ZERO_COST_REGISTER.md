# PSX Intelligence AI — Zero-Cost Register (Phase 1) — CANONICAL

> **Canonical version.** The root file `~/workspace/psx-intelligence-ai/ZERO_COST_REGISTER.md`
> is a summary that points here. If the two ever disagree, **this file wins**.
>
> Budget rule: **PKR 0 absolute.** Every dependency, tool, and service in the fixed
> Phase 1 stack must appear below with its licence and its cost. Cost means
> licence/subscription cost in PKR. **Local hardware, electricity, and internet are
> EXTERNAL operating expenses: they are listed in §3, disclosed, and never called
> free.** No permanent free hosting is assumed.
>
> Evidence key:
> - **PKR 0 (VERIFIED)** — a public page read for this task, the starting condition
>   (2026-11-04), or the scaffold states the item is free / MIT / Apache-2.0 /
>   BSD-style with no licence fee, and no payment step is involved in obtaining it.
> - **PKR 0 (UNVERIFIED licence)** — the item is distributed free via a public
>   registry (PyPI/npm/OS packages) with no payment step, but its LICENSE file was
>   not read for this task. Phase 2 setup MUST read that LICENSE file and record it
>   here before the item is installed. Until then the licence cell is UNVERIFIED,
>   even though no payment is involved.
> - **UNVERIFIED** — neither cost nor licence has been checked; the item must not be
>   adopted until checked.
> - **EXCLUDED** — a paid or paid-tier item that must not enter the stack.
>
> No version is pinned in Phase 1. "No payment step" was checked against how the
> item is obtained (public registry / free download / self-hosted build), not
> against a price list, because no price list exists for a free item.

## 1. Register — every dependency, tool, and service in the fixed stack

| # | Item | Role | Licence | Cost (PKR) | Evidence / check needed |
|---|---|---|---|---|---|
| 1 | Python 3.12 (runtime; 3.12.3 present, VERIFIED) | Backend language | PSF licence (UNVERIFIED here — read LICENSE at setup) | PKR 0 (no payment step; already installed) | Already on this machine; confirm licence file at setup |
| 2 | Node.js 24 (v24.22.1 present, VERIFIED) + npm (bundled) | Frontend runtime + JS package manager | UNVERIFIED here — read LICENSE at setup | PKR 0 (no payment step; already installed) | Already on this machine; confirm licence file at setup |
| 3 | Next.js + React | Frontend framework | MIT (VERIFIED by public page reads) | PKR 0 (VERIFIED) | MIT, free, self-hostable; no Vercel hosting required or assumed |
| 4 | TypeScript | Frontend language | UNVERIFIED here — read LICENSE at setup | PKR 0 (no payment step via npm) | Confirm licence file at setup |
| 5 | Tailwind CSS | Styling | MIT (VERIFIED by public page reads) | PKR 0 (VERIFIED) | Framework free/MIT; the paid Tailwind Plus kit is EXCLUDED, not this item |
| 6 | shadcn/ui | UI components (copied source) | MIT (VERIFIED by public page reads) | PKR 0 (VERIFIED) | Not a runtime dependency; components copied into the repo |
| 7 | TradingView Lightweight Charts | Financial charting (renderer only) | Apache-2.0 (VERIFIED by public page reads) | PKR 0 (VERIFIED) | Plus a licence duty, not a fee: TradingView attribution + tradingview.com link on chart pages; do not disable `attributionLogo` |
| 8 | FastAPI + Uvicorn | Backend framework + ASGI server | FastAPI MIT (VERIFIED); Uvicorn licence UNVERIFIED here | PKR 0 (no payment step via PyPI) | Confirm Uvicorn LICENSE at setup |
| 9 | Pydantic v2 | Validation / schemas | UNVERIFIED here — read LICENSE at setup | PKR 0 (no payment step via PyPI) | Confirm licence file at setup |
| 10 | PostgreSQL (self-hosted) | Production database | Liberal BSD-style licence, free incl. commercial use (VERIFIED by public page reads) | PKR 0 (VERIFIED) | Self-hosted only; any managed instance is a new, separately approved cost — not in this register |
| 11 | SQLite (dev only) | Local-dev database | UNVERIFIED here — confirm at setup | PKR 0 (no payment step; ships with Python) | Dev-only; never production |
| 12 | SQLAlchemy + Alembic | ORM + migrations | UNVERIFIED here — read LICENSE at setup | PKR 0 (no payment step via PyPI) | Confirm licence files at setup |
| 13 | Local filesystem | Raw payloads, PDFs, working files | n/a (OS facility) | PKR 0 | Disk space is an external expense (§3), not a licence fee |
| 14 | Apache Parquet via PyArrow | Bulk / analytical storage | Apache-2.0 (VERIFIED from Apache documentation pages) | PKR 0 (VERIFIED) | Columnar format + library, both Apache-2.0 |
| 15 | MinIO (self-hosted) | OPTIONAL object storage — **NOT ADOPTED** | AGPLv3 community build, reported archived/read-only April 2026 with no upstream fixes; vendor AIStor Free is proprietary single-server with a licence key (both VERIFIED in outline from public pages) | PKR 0 licence fee for the archived build; AIStor Free PKR 0 fee but proprietary + key-gated | **OPTIONAL ONLY. Do not adopt as a default.** No paid MinIO/AIStor tier and no Docker ELS. Re-verify status before any future adoption (see Decisions §2.6) |
| 16 | Celery | Background task queue | BSD-3-Clause (noted in public pages read) | PKR 0 (no payment step via PyPI) | Confirm LICENSE file at setup |
| 17 | Redis (self-hosted, broker + result backend) | Queue broker | Tri-licensed RSALv2 / SSPLv1 / AGPLv3 for Redis 8; BSD-3-Clause only for ≤ 7.2 (VERIFIED by public pages read) | PKR 0 licence fee under any option for self-hosted use | **Record the licence option operated under at setup.** No managed/paid Redis service. Project does not modify Redis or offer it as a managed service. Valkey (BSD-3-Clause fork) is a noted alternative only, not the primary |
| 18 | pandas + NumPy | Dataframes / numerics | UNVERIFIED here — read LICENSE at setup | PKR 0 (no payment step via PyPI) | Confirm licence files at setup |
| 19 | scikit-learn | General ML | UNVERIFIED here — read LICENSE at setup | PKR 0 (no payment step via PyPI) | Confirm licence file at setup |
| 20 | statsmodels | Econometrics / time series | UNVERIFIED here — read LICENSE at setup | PKR 0 (no payment step via PyPI) | Confirm licence file at setup |
| 21 | PyTorch | Deep learning — **CONDITIONAL only, where justified** | UNVERIFIED here — record LICENSE actually shipped before install | PKR 0 as distributed (no payment step via PyPI) | Install only on a written justification (§2.8 of Decisions); not a default dependency |
| 22 | PyMuPDF | PDF text extraction (primary) | UNVERIFIED here — **read its licence terms at install; do not assume** | PKR 0 (no payment step via PyPI) | Licence check is a setup gate, not an afterthought |
| 23 | pypdf | PDF fallback only | UNVERIFIED here — read LICENSE at setup | PKR 0 (no payment step via PyPI) | Fallback only; confirm licence file at setup |
| 24 | Tesseract OCR (+ language data) | OCR for scanned pages only | UNVERIFIED here — read LICENSE at setup | PKR 0 (no payment step via OS packages) | Binary presence UNVERIFIED on this machine; check at setup |
| 25 | Ollama (local runtime only) | Local LLM runtime | MIT (VERIFIED by public pages read) | PKR 0 local (VERIFIED) | Local use needs no account/subscription. **Ollama Cloud, `:cloud` models, and cloud web search are EXCLUDED (reported paid tiers)** |
| 26 | Open-weight model (specific model — NONE PINNED) | Local inference model | **UNVERIFIED — varies per model; read the chosen model's licence before download** | PKR 0 download (no payment step for open-weight downloads) | No model is adopted in Phase 1. A model becomes primary only via the ADR-007 evaluation gate + licence check |
| 27 | psx-dps | PSX market data (primary) | MIT, no API key (VERIFIED from starting condition) | PKR 0 (VERIFIED) | Library free; PSX data redistribution/commercial licensing must still be verified with PSX before commercial use (scaffold warning) |
| 28 | psxdata | PSX market data (backup) | MIT, PyPI, alpha 0.1.0a1 (VERIFIED from starting condition) | PKR 0 (VERIFIED) | Alpha APIs may change before 1.0; pin at setup |
| 29 | pytest | Backend testing | UNVERIFIED here — read LICENSE at setup | PKR 0 (no payment step via PyPI) | Confirm licence file at setup |
| 30 | Playwright (+ downloaded browsers) | Frontend E2E testing | UNVERIFIED here — read LICENSE at setup, including downloaded browser builds | PKR 0 as distributed (no payment step) | Confirm licence at setup; E2E runs against local dev only |
| 31 | Git | Version control | UNVERIFIED here — read LICENSE at setup | PKR 0 (no payment step) | Already in use in this workspace |
| 32 | GitHub Free + GitHub Actions (within free limits) | Hosting + CI | Vendor free tier (terms UNVERIFIED here — confirm current free-tier limits at setup) | PKR 0 within the Free tier | **No permanent free hosting assumed.** If free-tier limits are exceeded or terms change, the fallback is local git + local test runs — never a paid tier under this budget |
| 33 | Docker Engine (Linux) + Dockerfile / Compose | Container packaging | UNVERIFIED here — read LICENSE at setup (Engine on Linux) | PKR 0 for Engine (no payment step) | Engine NOT installed on this machine (VERIFIED) — install is a Phase 2 setup step. Docker Desktop terms are a different product and are UNVERIFIED — do not assume them |
| 34 | Python standard-library logging | Logging | Stdlib (UNVERIFIED here) | PKR 0 | No extra service |
| 35 | `/health` endpoint + CI test gate | Monitoring (Phase 1) | Project code | PKR 0 | No APM, no hosted logging |

## 2. Confirmation statement

**This register contains no paid dependency.** Every item in §1 is PKR 0 in
licence/subscription cost as evidenced above, or is explicitly marked OPTIONAL /
NOT ADOPTED (MinIO), CONDITIONAL (PyTorch), or NOT PINNED (a specific
open-weight model). No item in §1 requires a purchase, subscription, API key
payment, usage credit, or paid tier to perform its Phase 1 role.

**Items explicitly EXCLUDED from this stack (they must not slip in):**
paid PDF APIs; paid APM / hosted logging; managed databases, queues, buckets,
or hosts (including managed Redis, S3/R2/GCS buckets, and paid hosting);
external AI APIs of any provider; Ollama Cloud, `:cloud` models, and cloud web
search; MinIO/AIStor paid tiers and Docker Extended Lifecycle Support for MinIO;
MUI X Pro/Premium; Tailwind Plus / Tailwind UI; Highcharts / TradingView
Advanced Charts; Eulerpool or any vendor data API (no PSX coverage stated, no
paid API approved); Kubernetes-as-a-service or any other paid managed service.

**Exceptions and qualifications — stated plainly, not hidden:**

1. **MinIO (item 15)** is the one fixed-stack item whose current status is
   adverse: its open-source community build was reported archived/read-only in
   April 2026 with no upstream fixes, and the vendor's current free offering
   (AIStor Free) is proprietary and key-gated. It is therefore OPTIONAL and
   NOT ADOPTED. The project works fully without it. This is a qualification on
   adoption, not a paid dependency in the stack.
2. **Redis (item 17)** is PKR 0 to self-host but is no longer permissive-BSD for
   current versions; its tri-licence (RSALv2/SSPLv1/AGPLv3) must be recorded at
   setup, and no managed service may be used. This is a licence qualification,
   not a fee.
3. **Licences marked UNVERIFIED** (items 1, 2, 4, 8–9, 11–13, 16 in part,
   18–24, 26, 29–34) have no payment step but have not had their LICENSE files
   read for this task. Phase 2 setup must read each one and update this register
   before installation. If any such file turns out to require payment, that item
   stops and is replaced — it does not silently become a paid dependency.
4. **GitHub Free (item 32)** is a vendor free tier, not a permanent guarantee.
   Its limits are UNVERIFIED here; exceeding them never justifies paying under
   this budget — the fallback is local.
5. **PSX data itself (items 27–28):** the libraries are free, but PSX's own data
   redistribution/commercial-use terms are a separate verification with PSX
   before any commercial use or republication. This register covers software
   cost, not data licensing.

## 3. External operating expenses (disclosed, never called free)

These are real costs of running a self-hosted PKR 0 stack. They are the
operator's own existing expenses; no tariff, hardware price, or usage figure was
verified for this task, so none is stated.

- The local machine itself (purchase, wear, disk space for PostgreSQL, Parquet
  files, PDFs, and any downloaded Ollama model).
- Electricity to run that machine, including during Celery workers, Ollama
  inference, and any scheduled collection.
- Internet access to download packages and models, and to reach PSX and other
  public sources. A machine that is off, or offline, collects nothing — that is
  a stated operating limit of this stack, not a defect to be papered over with
  a paid host.
- The operator's time to maintain PSX adapters and PDF formats (the dominant
  Phase 1 cost — see Decisions §5).

## 4. How this register is maintained

- Phase 2 setup updates each UNVERIFIED licence cell with the LICENSE file
  actually shipped, and records the pinned version alongside it.
- Any new dependency proposed later must be added to this register first, with
  licence + cost evidence, before it is installed. A dependency with no register
  row is not installed.
- If any row's cost ceases to be PKR 0 (a licence change, a tier change, a
  vendor reclassification), that row is flagged, the dependent feature stops
  using it until a PKR 0 replacement is decided, and this register is updated —
  the change is never absorbed silently.
