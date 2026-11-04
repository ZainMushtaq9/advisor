# PSX Intelligence AI — Phase 2 Environment Audit (Team A)

**Date:** 2026-11-04 (Asia/Karachi, PKT). **Method:** commands actually run on
this machine by Team A; outputs below are copied from those runs, not from the
Phase 1 starting condition. Where this audit disagrees with Phase 1 or with the
task brief, the disagreement is stated, not smoothed over.

**Scope rule:** Team A installed nothing. Every "present" item below was either
already on the machine or was installed by concurrent work outside Team A (see
§6). Installing PostgreSQL / Redis / Docker is NOT Team A's job.

## 1. Operating system, CPU, memory, disk

Commands: `uname -a`, `cat /etc/os-release`, `nproc`, `uname -m`,
`grep -m1 'model name' /proc/cpuinfo`, `grep -c processor /proc/cpuinfo`,
`free -h`, `df -h`, `/proc/meminfo`, `uptime`, `whoami`.

```text
Linux htch-runtime 7.0.0-39-generic #1 SMP PREEMPT_DYNAMIC Thu Sep 24 08:42:15 UTC 2026 x86_64
PRETTY_NAME="Ubuntu 24.04.5 LTS"  (VERSION_CODENAME=noble, IMAGE_VERSION=0.1.46)
CPU: AMD EPYC 9D25 126-Core Processor (host CPU model; 4 vCPUs visible here)
CPUs visible: 4   Architecture: x86_64   Swap: 0B (no swap)
Mem: total 7.7Gi, used ~7.0Gi, free ~160-175Mi, buff/cache ~1.0Gi, available ~737-851Mi
MemTotal: 8124908 kB, MemFree: ~184576 kB, MemAvailable: ~851220 kB (at re-check)
Disk /home/hatch: 150G total, 2.7G used, 147G available (2%)
Disk / (overlay): 7.5G total, 73M used, 7.5G available — do NOT store project data on /;
  project data lives under /home/hatch/workspace (147G free).
Uptime at audit: 43 min, load average 3.36 / 1.76 / 0.82 (load near CPU count)
User: root (uid=0)
```

**Reading:** the brief's "7.7 GiB RAM" is confirmed as total RAM, but the
usable headroom at audit time was only ~0.8 GiB available with no swap. That
distinction drives the inference limits in `COMPATIBILITY_REPORT.md`.

## 2. Runtimes and developer tools (verified present)

| Tool | Version (actual output) | Source |
|---|---|---|
| Python | 3.12.3 (`Python 3.12.3`) | `python3 --version` |
| pip | 24.0 from `/usr/lib/python3/dist-packages/pip` (python 3.12) | `pip3 --version` |
| venv module | available | `python3 -m venv --help` |
| Node.js | v24.22.1 (`/usr/bin/node`) | `node --version` |
| npm | 10.9.4 (`/opt/hatch-image/bin/npm`) | `npm --version` |
| Git | 2.43.0 (`/usr/bin/git`) | `git --version` |
| curl | 8.5.0 (OpenSSL/3.0.13) | `curl --version` |
| wget | GNU Wget 1.21.4 | `wget --version` |
| make | GNU Make 4.3 | `make --version` |
| gcc / g++ | 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1) | `gcc --version` |
| tar | 1.35 | `tar --version` |
| jq | 1.7 | `jq --version` |
| OpenSSL | 3.0.13 (30 Jan 2024) | `openssl version` |
| OpenSSH | OpenSSH_9.6p1 Ubuntu-3ubuntu13.20 | `ssh -V` |
| apt-get | apt 2.8.3 (amd64) | `apt-get --version` |
| unzip / zip | present (Info-ZIP) | `unzip` / `zip` banners |
| Python LICENSE file | `/usr/lib/python3.12/LICENSE.txt` present (PSF licence history section read) | local file |

**System Python packages (OS-packaged, NOT project-installed, NOT pinned by
Team A):** `pip list` shows, among others, numpy 1.26.4 and pandas
2.1.4+dfsg, matplotlib 3.6.3, pillow 10.2.0. These are Ubuntu packages for the
system Python. The project must use its own `.venv` with a backend-team
requirements file + lockfile; system packages must never be treated as the
project's pinned versions.

**Frontend packages actually installed (by the frontend team, read from
`frontend/node_modules/*/package.json` — Team A installed none of these):**
next 16.4.5 (MIT), react 19.3.0 (MIT), react-dom 19.3.0 (MIT),
typescript 5.9.3 (Apache-2.0), tailwindcss 4.3.4 (MIT),
@tailwindcss/turbopack 4.3.4 (MIT), eslint 9.39.5 (MIT),
eslint-config-next 16.4.5 (MIT). `frontend/node_modules` contains 288 entries.
`frontend/package.json` declares next 16.4.5, react/react-dom 19.3.0,
tailwindcss ^4, typescript ^5 — the installed typescript 5.9.3 and tailwindcss
4.3.4 resolve those ranges.

## 3. GPU evidence (for local-inference limits)

```text
nvidia-smi: command not found
ls /dev/nvidia*: No such file or directory
lspci: not installed (cannot enumerate PCI devices this way)
```

**Finding: no GPU evidence on this machine.** Local AI inference, if any, is
CPU-only. See `COMPATIBILITY_REPORT.md` §2 for the consequences. This is a
limit statement, not a failure: the Phase 1 stack is designed to work fully
with Ollama absent or with no model downloaded.

## 4. Services — status at two check times (read §6 before quoting this table)

| Service | First check (2026-11-04 ~11:34 PKT) | Re-check (~11:37 PKT) | Evidence at re-check |
|---|---|---|---|
| Docker Engine | NOT installed (`docker: command not found`) | still NOT installed | `command -v docker` empty |
| PostgreSQL client (`psql`) | NOT installed | PRESENT, 16.15 | `psql (PostgreSQL) 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)` |
| PostgreSQL server | not checked | INSTALLED + ACCEPTING | `pg_isready` → `/var/run/postgresql:5432 - accepting connections`; dpkg: `postgresql-16 16.15-0ubuntu0.24.04.1` |
| Redis client (`redis-cli`) | NOT installed | PRESENT, 7.0.15 | `redis-cli 7.0.15` |
| Redis server | not checked | INSTALLED + RESPONDING | `redis-cli ping` → `PONG`; dpkg: `redis-server 5:7.0.15-1ubuntu0.24.04.5` |
| Ollama | NOT installed | still NOT installed | `command -v ollama` empty |
| Tesseract OCR | not checked in first pass | NOT installed | `command -v tesseract` empty |

**What this table does NOT prove:** client/server presence does not prove a
project database, project Redis namespace, user, password, or any
configuration exists. Team A probed service liveness only (`pg_isready`,
`redis-cli ping`) and did not inspect, create, or modify any database, key,
user, or configuration — that belongs to the database/backend teams.

## 5. Missing tools and their FREE installation methods (documented, not performed)

Team A performed none of these installs. Each method is PKR 0 (no payment
step, no paid tier, no account). Installing teams must re-read the shipped
LICENSE file and update `LICENSE_REGISTER.md` at install time.

| Missing tool | Free install method (Ubuntu 24.04) | Notes / gate |
|---|---|---|
| Docker Engine (Linux) | Official Docker Engine apt path: add Docker's apt repository and install `docker-ce docker-ce-cli containerd.io docker-compose-plugin` (free, open-source runtime). Do NOT substitute Docker Desktop licence terms — Desktop is a different product and its terms are UNVERIFIED here. | Phase 2 packaging path; local dev does NOT require Docker. Verify Engine licence at install. |
| Ollama (local runtime only) | Official Ollama Linux install (free download, MIT runtime per Phase 1 public-page read). Run on the host for local inference. | Local-only boundary: NO Ollama Cloud, NO `:cloud` models, NO cloud web search, NO account/key. No model is downloaded in this skeleton; a model needs the ADR-007 gate + its own licence check first. |
| Tesseract OCR | `sudo apt-get install tesseract-ocr` (+ language data packages as needed, e.g. `tesseract-ocr-eng`) — OS packages, no payment step. | Scanned-PDF pages only; a different role from text extraction, not a duplicate. Confirm licence at install. |
| `lspci` (diagnostic only) | `sudo apt-get install pciutils` — only needed if PCI/GPU enumeration is ever required. | Not a project dependency. |
| Playwright browsers (frontend E2E, later) | Installed by the frontend team via Playwright's own browser install when E2E suites exist; browsers are free builds — confirm at install, do not assume a vendor browser licence. | E2E runs against local dev only. |
| GitHub Free / Actions | No install; web account + repo. Free-tier limits are UNVERIFIED — confirm current limits at setup and keep CI inside them. | No permanent free hosting assumed; fallback is local git + local test runs. **No remote is configured by Team A and no push is made by Team A** — pushing waits for Phase 2 acceptance (user decision 2026-11-04). |

## 6. Concurrent-change warning (why two check times differ)

Between Team A's first tool check (~11:34 PKT, Docker/psql/redis-cli absent)
and the re-check minutes later, PostgreSQL 16 and Redis 7.0.15 appeared with
servers responding. Team A installed nothing in that window (its only installs
were zero: no apt, pip, or npm install was run by Team A at any point). The
only consistent reading is that a concurrent worker (another Phase 2 team or
environment setup) installed them mid-audit. Consequences:

- Quote service status WITH its check time; never quote the 11:34 "absent"
  row without the 11:37 correction, and never quote the 11:37 "present" row
  as Team A's work.
- PostgreSQL/Redis configuration, databases, and users are owned by whoever
  installed them — Team A documents their presence only.
- Any future audit must re-run `bash scripts/check_env.sh` rather than copy
  this file.

## 7. Reproducing this audit

```bash
bash scripts/check_env.sh   # report only; installs nothing
```

Rerun it before relying on any row above. If a row changes, update this file
in the same commit that notices the change, with the new check time.
