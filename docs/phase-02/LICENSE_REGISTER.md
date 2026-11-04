# PSX Intelligence AI — Phase 2 Licence Register (Team A, gate G-02)

**Date:** 2026-11-04. **Purpose:** close Phase 1 gate G-02 as far as a
setup-only team can: record a licence for every planned dependency in the
fixed stack, state exactly how each licence was obtained, and state what
remains for the installing team.

**Method (what Team A actually did):**

1. Read the Phase 1 canonical register (`docs/phase-01/ZERO_COST_REGISTER.md`)
   and carried forward its VERIFIED marks with attribution (not re-claimed
   as Team A checks).
2. Queried the PyPI JSON API (`pypi.org/pypi/<package>/json`) for each Python
   package and read its declared licence / licence expression + latest
   version on 2026-11-04. Registry metadata is the package's declared
   licence, not the shipped LICENSE file — the distinction is kept in the
   table.
3. Read the npm registry `/latest` document for lightweight-charts,
   Playwright, and @playwright/test.
4. Read actually-installed frontend packages in `frontend/node_modules/*/package.json`
   (installed by the frontend team) for version + licence field, and noted
   LICENSE file presence where confirmed.
5. Read the local Python licence file `/usr/lib/python3.12/LICENSE.txt`.
6. Installed nothing (no pip install, no npm install, no apt install by
   Team A). Therefore **no shipped LICENSE file from a Team A install exists
   to quote** — and this register says so, per item, instead of pretending
   otherwise.

**Payment result (the G-02 stop-and-replace test):** NO item in this register
requires payment, a subscription, an API-key purchase, or a paid tier to
perform its Phase 1 role. No replacement was therefore triggered. Two items
need licence-path decisions at install (not payment): PyMuPDF (AGPLv3 option
vs commercial option — see flag F-1) and Redis (version-dependent licence —
see flag F-2). One item needs source verification: psx-dps (see flag F-3).

**Standing rule for installing teams:** before installing any item below,
read its shipped LICENSE file and update this register with the file's exact
licence + version installed. If that file requires payment, STOP: do not
install it, do not work around it, and replace it under a new recorded
decision. Registry metadata in this file never overrides a shipped LICENSE
file that says otherwise.

## Register

"Latest observed" = registry latest on 2026-11-04, for reference only — NOT
a pin, NOT an installed version. "Installed" = present on this machine with
the version read from the installation itself.

| # | Item | Licence recorded 2026-11-04 | How obtained | Cost (PKR) | Status |
|---|---|---|---|---|---|
| 1 | Python 3.12 (runtime, 3.12.3 present) | PSF licence | Local file `/usr/lib/python3.12/LICENSE.txt` read (history section confirms PSF/CWI/CNRI lineage) | 0 | Installed; licence file read locally |
| 2 | Node.js 24 (v24.22.1 present) + npm 10.9.4 | NOT read locally — no Node licence file found on this machine (`/usr/share/doc/nodejs/copyright` absent; Node from `/usr/bin/node`, npm from `/opt/hatch-image/bin/npm`) | Local search only | 0 (no payment step; already installed) | OPEN: installing/setup team must record the Node distribution LICENSE at setup; Phase 1 marked this UNVERIFIED and that mark stands |
| 3 | Next.js 16.4.5 + React 19.3.0 + react-dom 19.3.0 | MIT (all three) | Installed `package.json` licence fields in `frontend/node_modules` (frontend team install); React/react-dom LICENSE files confirmed present | 0 | Installed; no Vercel hosting required or assumed |
| 4 | TypeScript 5.9.3 | Apache-2.0 | Installed `package.json` licence field; `LICENSE.txt` confirmed present | 0 | Installed |
| 5 | Tailwind CSS 4.3.4 (+ @tailwindcss/turbopack 4.3.4) | MIT | Installed `package.json` licence fields; LICENSE files confirmed present | 0 | Installed. Paid Tailwind Plus kit is EXCLUDED, not this item |
| 6 | shadcn/ui | MIT (Phase 1 VERIFIED by public page reads) | Phase 1 record carried forward; not yet installed by any team | 0 | NOT installed. Confirm primitive (Radix vs Base UI) at component install |
| 7 | TradingView Lightweight Charts (latest observed 5.2.1) | Apache-2.0 | npm registry `/latest` document | 0 | NOT installed. Licence duty (not a fee): TradingView attribution + tradingview.com link on chart pages; do not disable `attributionLogo` |
| 8 | FastAPI (latest observed 0.162.0) | MIT | PyPI licence expression | 0 | NOT installed; pin at backend install |
| 9 | Uvicorn (latest observed 0.54.0) | BSD-3-Clause | PyPI licence expression | 0 | NOT installed; pin at backend install |
| 10 | Pydantic v2 (latest observed 2.14.2) | MIT | PyPI licence expression | 0 | NOT installed; pin at backend install |
| 11 | PostgreSQL 16.15 (server present) | PostgreSQL Licence, liberal BSD-style, free incl. commercial use (Phase 1 VERIFIED by public page reads) | Phase 1 record + server presence (dpkg `postgresql-16 16.15-0ubuntu0.24.04.1`, installed by concurrent work) | 0 | Server present; self-hosted only — any managed instance is a new, separately approved cost |
| 12 | SQLite (dev only) | Public domain (project convention; Phase 1 marked UNVERIFIED — this register does NOT upgrade that mark from registry data because SQLite ships with Python, not via PyPI) | Phase 1 record | 0 | Dev-only; never production |
| 13 | SQLAlchemy (latest observed 2.1.8) | MIT | PyPI licence expression | 0 | NOT installed; pin at backend install |
| 14 | Alembic (latest observed 1.20.1) | MIT | PyPI licence expression | 0 | NOT installed; pin at backend install |
| 15 | Local filesystem | n/a (OS facility) | — | 0 | Disk space is an external expense, not a licence fee |
| 16 | Apache Parquet via PyArrow (latest observed 26.0.1) | Apache-2.0 | PyPI licence expression (PyArrow) | 0 | NOT installed; pin at backend install |
| 17 | MinIO (self-hosted) | AGPLv3 community build, reported archived/read-only April 2026 with no upstream fixes; vendor AIStor Free is proprietary single-server with a licence key (Phase 1 VERIFIED in outline) | Phase 1 record carried forward | 0 fee for archived build; AIStor Free 0 fee but proprietary + key-gated | OPTIONAL ONLY, NOT ADOPTED. No paid tier, no Docker ELS. Re-verify before any future adoption |
| 18 | Celery (latest observed 5.6.3) | BSD-3-Clause | PyPI licence field | 0 | NOT installed; pin at worker install |
| 19 | Redis server 7.0.15 (present) + redis-py client (latest observed 8.1.0) | Server 7.0.15: BSD-3-Clause era (≤ 7.2). Client: MIT (PyPI expression). Redis 8 tri-licence RSALv2/SSPLv1/AGPLv3 (Phase 1 VERIFIED) applies only if upgraded to 8.x | dpkg version + PyPI expression + Phase 1 record | 0 licence fee for self-hosted use under any option | Server present (concurrent install). See flag F-2: an upgrade to Redis 8 is a licence event |
| 20 | pandas (latest observed 3.1.0) | BSD-3-Clause | PyPI licence expression | 0 | NOT installed as a project package. System Python carries pandas 2.1.4+dfsg as an OS package — that is NOT the project pin |
| 21 | NumPy (latest observed 2.5.4) | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 (multi-licence expression) | PyPI licence expression | 0 | NOT installed as a project package. System numpy 1.26.4 (OS package) is NOT the project pin |
| 22 | scikit-learn (latest observed 1.9.1) | BSD-3-Clause | PyPI licence expression | 0 | NOT installed; pin at install |
| 23 | statsmodels (latest observed 0.15.0) | BSD-3-Clause | PyPI licence expression | 0 | NOT installed; pin at install |
| 24 | PyTorch | UNVERIFIED here — record the LICENSE actually shipped before install | — | 0 as distributed (no payment step via PyPI) | CONDITIONAL ONLY, where justified in writing (Phase 1 §2.8). Not a default; not installed |
| 25 | PyMuPDF (latest observed 2.1) | **Dual licence: GNU AFFERO GPL 3.0 OR Artifex Commercial License** | PyPI licence field | 0 under the AGPLv3 option; commercial option would require payment — NEVER take it under PKR 0 without separate approval | FLAG F-1 (below). NOT installed. The AGPL path is free but carries obligations |
| 26 | pypdf (latest observed 6.21.4) | BSD-3-Clause | PyPI licence expression | 0 | NOT installed; fallback only; pin at install |
| 27 | Tesseract OCR (+ language data) | UNVERIFIED here — read LICENSE at install | — | 0 (no payment step via OS packages) | NOT installed |
| 28 | Ollama (local runtime only) | MIT (Phase 1 VERIFIED by public page reads) | Phase 1 record carried forward | 0 local | NOT installed. Ollama Cloud, `:cloud` models, cloud web search: EXCLUDED (reported paid tiers) |
| 29 | Open-weight model (specific model — NONE PINNED) | UNVERIFIED — varies per model; read the chosen model's licence before download | — | 0 download for open-weight files | NOT adopted. ADR-007 gate + licence check required; Ollama's MIT licence does not transfer to model weights |
| 30 | psx-dps | MIT, no API key (Phase 1 VERIFIED from starting condition) | Phase 1 record; PyPI lookup FAILED (see flag F-3) | 0 | NOT installed. Library free; PSX data redistribution/commercial terms still gated with PSX |
| 31 | psxdata (latest observed 1.2.0) | MIT (full MIT licence text in PyPI metadata, copyright 2026 Muhammad Tauha) | PyPI licence field (full text) | 0 | NOT installed. Version drift noted: Phase 1 alpha 0.1.0a1 → 1.2.0 observed; pin at install, isolate behind one adapter |
| 32 | pytest (latest observed 9.2.0) | MIT | PyPI licence expression | 0 | NOT installed; pin at install |
| 33 | Playwright + @playwright/test (latest observed 1.64.1) | Apache-2.0 | npm registry `/latest` documents | 0 as distributed | NOT installed; confirm downloaded-browser licences at install; E2E against local dev only |
| 34 | Git 2.43.0 | UNVERIFIED here — Debian copyright file exists locally (`/usr/share/doc/git/copyright`) but was not read line-by-line by Team A; record at setup if needed | Local file existence only | 0 (no payment step) | Installed; licence-file read remains a setup nicety, not a blocker (no payment step exists for Git) |
| 35 | GitHub Free + GitHub Actions | Vendor free tier; terms/limits UNVERIFIED (Phase 1 mark stands) | Phase 1 record | 0 within Free tier | No remote configured by Team A; no push made; push deferred until Phase 2 acceptance (user decision 2026-11-04). Fallback if terms change: local git + local tests, never a paid tier |
| 36 | Docker Engine (Linux) | UNVERIFIED here — read LICENSE at setup (Engine on Linux) | — | 0 for Engine (no payment step) | NOT installed. Docker Desktop terms are a different product — do not assume them |
| 37 | Python stdlib logging | Stdlib (same PSF licence family as item 1) | Local Python licence file | 0 | No extra service |
| 38 | `/health` endpoint + CI test gate | Project code | — | 0 | No APM, no hosted logging |

## Flags requiring a decision at install (not payment triggers)

**F-1 — PyMuPDF is AGPLv3-or-commercial (dual licence).** The AGPLv3 option
costs PKR 0 and is the only option usable under the PKR 0 budget. AGPLv3 is
strong copyleft: if the project serves AGPL-covered code over a network, the
corresponding source must be offered under AGPL §13, and the project must
not combine it with incompatible-licence code in a way that violates the
licence. The installing team must: (a) read the shipped LICENSE file,
(b) record explicitly whether the project proceeds under the AGPLv3 option,
(c) confirm the service/source-offer posture with that decision, and
(d) keep pypdf (BSD-3-Clause, permissive) as the fallback — if the AGPL
posture ever becomes untenable, the fallback is to drop PyMuPDF and use
pypdf, recorded as a new decision, not a silent swap. The commercial option
is never taken without a separate, explicit, paid approval — which the PKR 0
budget does not grant.

**F-2 — Redis licence depends on version.** The installed server 7.0.15 is
in the BSD-3-Clause era (≤ 7.2). Upgrading to Redis 7.4+ or 8.x moves to
RSALv2/SSPLv1 (7.4) or tri-licence RSALv2/SSPLv1/AGPLv3 (8.x). Self-hosted
use remains PKR 0 under any option for this project (it does not modify
Redis or offer it as a managed service), but the licence option operated
under must be re-recorded at upgrade time, and no managed/paid Redis service
may be used. Valkey (BSD-3-Clause fork) remains a noted alternative only,
not the primary — swapping primaries needs a new decision.

**F-3 — psx-dps is not on PyPI under that name.** The PyPI lookup returned
HTTP 404 on 2026-11-04. Do NOT `pip install` any similarly named package
found by guessing — that would risk a wrong or malicious package. Install
psx-dps only from its actual distribution source as documented by the data
team, verify its LICENSE file from that source, and record the source +
licence here. Its Phase 1 MIT claim stands as a starting-condition record
until that check.

## Explicitly excluded (must not slip in)

External AI APIs; Ollama Cloud / `:cloud` models / cloud web search; managed
databases, queues, buckets, hosts (incl. managed Redis, S3/R2/GCS, paid
hosting); paid PDF APIs; paid APM/hosted logging; MinIO/AIStor paid tiers and
Docker ELS; MUI X Pro/Premium; Tailwind Plus / Tailwind UI; Highcharts /
TradingView Advanced Charts; Eulerpool or any vendor data API; PyMuPDF's
commercial licence option; Kubernetes-as-a-service or any paid managed service.

## External operating expenses (disclosed, never called free)

Local hardware, electricity, and internet access. No tariff, hardware price,
or usage figure is stated (none verified). A machine that is off collects
nothing.
