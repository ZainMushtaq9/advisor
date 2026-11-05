# Phase 30 — Licence and Source Inventory

Checked 2026-11-05. Rule (Phase 1 gate G-02): if any item required
payment, it stops and is replaced. Nothing below required payment, a
subscription, a sign-up, or a credential. Local hardware, electricity,
and internet are external operating expenses — they are not licence
costs and are never described as free.

## Software licences — backend (pinned in `backend/requirements.txt`)

Source: `backend/LICENCES.md` (checked 2026-11-04 from each installed
package's own metadata; Phase 29 defect D-13 fix added the two
extraction packages that had been used unpinned since Phase 7).

| Package | Version | Licence |
|---|---|---|
| fastapi | 0.162.0 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| pydantic | 2.14.2 | MIT |
| pydantic-settings | 2.16.2 | MIT |
| SQLAlchemy | 2.1.8 | MIT |
| alembic | 1.20.1 | MIT |
| psycopg (+ psycopg-binary) | 3.3.7 | LGPL-3.0-only (used unmodified as a library; if the project ever redistributes a combined work, re-check LGPL obligations then) |
| httpx | 0.28.1 | BSD-3-Clause |
| pytest | 9.2.0 | MIT |
| ruff | 0.17.3 | MIT |
| fpdf2 | 2.9.0 | (free, pure Python; Phase 22 PDF report exports) |
| PyMuPDF | 2.1 | Dual: GNU AFFERO GPL 3.0 OR Artifex Commercial License — see review item D-14 below |
| pdfplumber | 0.11.10 | MIT |

Notable transitive: starlette 1.10.0 BSD-3-Clause, anyio 4.16.0 MIT,
Mako 1.4.3 MIT, click 8.5.0 BSD-3-Clause, python-dotenv 1.2.4
BSD-3-Clause. Full detail: `backend/LICENCES.md`.

**Review item D-14 (open, low):** PyMuPDF's AGPL-3.0 option must be
reviewed before any public hosted deployment or redistribution of this
project. This is NOT a current violation claim: the project is local
research, not a distributed network service. Trigger for review: public
hosted distribution or redistribution.

**Deliberately NOT installed (no licence or cost claim made):** pandas,
NumPy, scikit-learn, statsmodels, Celery/Redis clients, Ollama clients,
PyTorch — Phase 1 stack items for later phases/tasks. When a later phase
adds one, its shipped licence must be recorded first, per gate G-02/G-04.
Note: the Phase 2 live proof used system Redis 7.0.15 + Celery; the
Phase 25 job framework deliberately does NOT use Celery/Redis (the
database itself is the queue; a broker/worker pair is exactly what a VM
replacement kills).

## Software licences — frontend (from installed `package.json` files, 2026-11-05)

| Package | Version | Licence |
|---|---|---|
| next | 16.4.5 | MIT |
| react | 19.3.0 | MIT |
| react-dom | 19.3.0 | MIT |
| clsx | 2.1.1 | MIT |
| lightweight-charts | 5.2.1 | Apache-2.0 (renderer only; attribution required — charts render stored data only, never fabricated points) |
| tailwind-merge | 3.7.0 | MIT |
| @playwright/test | 1.64.1 | Apache-2.0 |
| vitest | 3.2.4 | MIT |
| typescript | 5.9.3 | Apache-2.0 |
| eslint / eslint-config-next | 9.39.5 / 16.4.5 | MIT |
| tailwindcss / @tailwindcss/turbopack | 4.3.4 | MIT |
| @types/node / @types/react / @types/react-dom | 20.19.43 / 19.3.0 / 19.3.0 | MIT |
| jsdom | 27.2.0 | MIT |
| prettier | 3.9.10 | MIT |
| @testing-library/react / @testing-library/jest-dom | 16.3.0 / 6.9.1 | MIT |

System packages used (free, apt/npm): PostgreSQL 16.15, Redis 7.0.15
(live proof only, Phase 2), Node v24.22.1, npm 10.9.4, Git 2.43.0.
Docker Engine is NOT used by this project (user decision 2026-11-04);
the Phase 2 Docker definitions are historical only, and the ops scripts
contain no docker invocations (enforced by test scan).

## Data sources — verdicts (what may be used, what may not)

| Source | Verdict | Evidence / limits |
|---|---|---|
| DPS Listing Status snapshot (2026-11-04, Main Board / Normal Counter, 470 rows) | USED, internal analysis only | Gitignored CSV, never committed. All rows UNVERIFIED (single source). GEM (5) + Non-Compliant/Winding-Up (93) NOT captured — Terms-gated. |
| DPS Market Summary (Closing) 2026-11-03 (`closing11.lis`) | USED, internal analysis only, dated-file route | Gitignored mapped CSV. 444 rows committed to market_prices, all UNVERIFIED. Field-9 meaning NOT established, never stored. 564 futures-like rows excluded. Live DPS adapters BLOCKED. |
| DPS company pages | DISCOVERY ONLY | No DPS PDF downloaded; filing-download terms not established. The LUCK FY2026 DPS link is BLOCKED for download use. |
| DPS financials portal | NOT USED | — |
| PSX homepage | NOT SELECTED for prices | — |
| SECP LEAP (public search, no sign-in/fee/CAPTCHA) | USED, sampled only (61 companies) | Evidence rows use `source_key = secp_leap`, deliberately NOT the official `secp` key, so promotion code can never promote from LEAP rows alone. CUIN RECORDED ONLY, never promoted to identifiers. Sample: AGREE 47 / DISAGREE 5 / NOT_FOUND 9. Older eServices route requires a paid Rs. 100 account — DO NOT USE. |
| SECP (official, as a second agreeing source) | NOT YET OBTAINED | Required by rule H1 for any VERIFIED promotion. |
| Issuer IR pages (HUBC, NML, OGDC, HBL annual/interim reports) | ALLOWED, sampled, internal analysis only, no republication | PDFs gitignored, never committed. HBL CY2025 obtained 2026-11-05 via normal browser visit (no challenge, no mirror, no DPS copy). |
| SBP (Monetary Policy Statements, policy rate) | USED, official reads | Policy rate 12.00% eff 2026-10-27. Cross-publisher agreement documented for the 6 VERIFIED macro rows (see caveat in handover report). |
| PBS (CPI, GDP, LSM, SPI releases) | USED, official reads | CPI YoY 10.3% Sep 2026, GDP FY26 3.65% provisional, etc. October CPI YoY NOT stored (needs a live-browser PBS PDF fetch). |
| PSX Terms / Data Legal Notice | GOVERNING CONSTRAINT | Systematic retrieval to create collections/compilations/databases is prohibited except with prior written permission; automated access prohibited except generally available third-party browsers, unless prior written permission; redistribution/republication/dissemination/sale/commercial use of Market Data feed without the respective rights/licence is strictly prohibited. Contact: marketdatarequest@psx.com.pk. Permission email sent 2026-11-04 from 5439 (message `1a1a66ca3ef85eeb`); a reply arrived but was permanently deleted by the user including from trash, so its wording is unverifiable and does NOT clear the gate; no resend sent (user decision 2026-11-04 18:58 PKT). **Terms gate NOT cleared — the single largest blocker.** |
| News/research articles | EXCLUDED | No article bodies stored or served; seed summaries capped at 280 chars. |
| psx-dps, psxdata, third-party price APIs | BLOCKED / NOT SELECTED | See Phase 5 source verdicts. No live adapter exists. |

## What is published in the repository (and what is not)

- PUBLISHED: code, tests, docs, page maps, run reports, manifests
  (hashes + counts, never the underlying rows), the 470-row snapshot is
  NOT published (gitignored; the public API serves metadata/summary
  only, never the CSV).
- NOT PUBLISHED: the 470-row registry CSV, the price-mapping CSV, the
  four issuer PDFs (HUBC, NML, OGDC, HBL), any `.env` file, any
  credential, token, session cookie, or private user data. The Phase 29
  audit verified 0 tracked datasets, 0 tracked secrets, 0 PII columns
  at branch tips; Phase 30 re-verifies (see `run_report.md`).
- The 470-row snapshot stays outside the public repo unless
  redistribution rights are confirmed (playbook rule).
