# PSX Intelligence AI — Database Setup (Phase 2, Team D)

Date: 2026-11-04. Status: PROVISIONED AND TESTED on this VM.
Budget: PKR 0 — free/open-source software only (PostgreSQL, SQLAlchemy,
Alembic, psycopg). No paid hosted database, no purchase, no sign-up.
External operating expenses (hardware, electricity, internet) are real
costs to the operator and are never called "free" (Phase 1 rule).

Phase 1 basis: `docs/phase-01/DATABASE_DESIGN.md`,
`TECH_STACK_DECISIONS.md` (PostgreSQL + SQLAlchemy + Alembic, local
filesystem + Parquet, MinIO OPTIONAL / NOT ADOPTED — gate G-07),
`DATA_RETENTION_POLICY.md`. This doc records what was actually done
in Phase 2, with real commands, versions, and outputs — not the design.

## 1. What was provisioned

| Item | Value (verified 2026-11-04) |
|---|---|
| OS | Ubuntu 24.04.5 LTS |
| Python | 3.12.3 (pre-existing) |
| PostgreSQL | 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1), cluster `16/main`, port 5432, data dir `/var/lib/postgresql/16/main`, UTF8, locale C.UTF-8 |
| Database | `psx_intelligence` (owner `postgres`) |
| App role | `psx_app` — LOGIN, NOSUPERUSER, NOCREATEDB, NOCREATEROLE (verified: `rolsuper=f, rolcreatedb=f`) |
| SQLAlchemy | 2.1.8 |
| Alembic | 1.20.1 |
| psycopg (binary) | 3.3.7 |
| Test venv | `database/.venv` (106 MB, gitignored; the DATABASE team's infra venv — the backend team owns `backend/` dependencies separately) |

Privileges granted to `psx_app`: CONNECT on `psx_intelligence`;
USAGE + CREATE on schema `public`; default privileges SELECT/INSERT/
UPDATE/DELETE on future tables and USAGE/SELECT/UPDATE on future
sequences in schema `public`. The role cannot create databases or
other roles and is not a superuser — by design, so a compromised app
credential cannot drop the database or escalate.

## 2. Installation — exact commands and real output

Docker, `psql`, and `redis-cli` were NOT installed at the start of
this task (as Phase 1 recorded). The free route taken was apt, not a
paid service and not a container image pull.

```bash
apt-get update
# First attempt failed with an apt lock held by another process
# (PID 6399, a concurrent apt-get update from a sibling task):
#   E: Could not get lock /var/lib/apt/lists/lock.
#   E: Unable to lock directory /var/lib/apt/lists/
# The lock was NOT broken by force. After that process finished,
# apt-get update succeeded (Ubuntu noble + noble-updates mirrors).
apt-cache policy postgresql
# postgresql: candidate 16+257build1.1 (noble-updates/main)

DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-client
# Setting up postgresql-16 (16.15-0ubuntu0.24.04.1) ...
# Creating new PostgreSQL cluster 16/main ...
#   /usr/lib/postgresql/16/bin/initdb -D /var/lib/postgresql/16/main
#   --auth-local peer --auth-host scram-sha-256
#   locale "C.UTF-8", encoding UTF8, max_connections 100,
#   shared_buffers 128MB, time zone Etc/UTC
#   invoke-rc.d: policy-rc.d denied execution of start.   <-- see §3
psql --version
# psql (PostgreSQL) 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
```

### 3. Starting the server (container quirk — read this on reboot)

This VM's `policy-rc.d` denies service start at install time, so the
cluster was `down` after installation even though the package
installed cleanly. It was started manually:

```bash
pg_ctlcluster 16 main start
pg_lsclusters
# Ver Cluster Port Status Owner    Data directory              Log file
# 16  main    5432 online postgres /var/lib/postgresql/16/main /var/log/postgresql/postgresql-16-main.log
pg_isready
# /var/run/postgresql:5432 - accepting connections
su postgres -c "psql -c 'SELECT version();'"
# PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu ...
```

**Operator note:** on a reboot of this VM, run
`pg_ctlcluster 16 main start` again before anything else. On a real
host with systemd, `systemctl enable --now postgresql` is the normal
route; do not assume the cluster auto-starts here.

### 4. Role, database, and credentials (environment variables only)

```bash
# Password: 32 alphanumeric characters generated with
#   tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32
# (alphanumeric only, deliberately — an earlier base64 password broke
# psql variable quoting; see §8, lesson 2. The value itself is NEVER
# printed in this doc, in any script, or in chat.)
su postgres -c "psql -U postgres -d postgres -c \"CREATE ROLE psx_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '<from-env>';\""
su postgres -c "psql -U postgres -d postgres -c \"CREATE DATABASE psx_intelligence OWNER postgres ENCODING 'UTF8';\""
su postgres -c "psql -U postgres -d psx_intelligence \
  -c 'GRANT CONNECT ON DATABASE psx_intelligence TO psx_app;' \
  -c 'GRANT USAGE, CREATE ON SCHEMA public TO psx_app;' \
  -c 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO psx_app;' \
  -c 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO psx_app;'"
```

Credential storage contract:

- The live password lives ONLY in `database/.env` (file mode 0600,
  listed in `database/.gitignore`). `database/.env.example` contains
  only `CHANGE_ME` placeholders.
- `database/alembic.ini` contains only a `CHANGE_ME` placeholder URL;
  `migrations/env.py` reads the real URL from `DATABASE_URL` and
  refuses to run if it is unset — it never falls back to a guessed
  database.
- No password appears in any migration, script, backup manifest, or
  doc in this project. If `.env` is ever shared or committed by
  mistake, rotate the password (re-run the CREATE ROLE step with a
  new value via `ALTER ROLE psx_app PASSWORD '...'`) and re-issue
  `.env`. No commit was made by Team D in this task (and the project
  directory is not a git repository at the time of writing).
- When running any command below, first load the environment without
  leaking it into superuser commands:

```bash
set -a; source database/.env; set +a   # from the project root
# CAUTION: after sourcing, PGUSER=psx_app is exported. Superuser
# commands (su postgres ...) must clear it, e.g.:
#   env -u PGUSER -u PGPASSWORD -u PGDATABASE su postgres -c "psql -U postgres ..."
# Otherwise psql silently tries to connect as psx_app and fails with
# "password authentication failed for user psx_app" (see §8, lesson 1).
```

Python environment:

```bash
python3 -m venv database/.venv
database/.venv/bin/pip install -q --upgrade pip
database/.venv/bin/pip install 'SQLAlchemy>=2.0' 'alembic>=1.13' 'psycopg[binary]>=3.1'
# Successfully installed Mako-1.4.3 MarkupSafe-3.0.4 SQLAlchemy-2.1.8
#   alembic-1.20.1 psycopg-3.3.7 psycopg-binary-3.3.7 typing-extensions-4.16.0
# Pinned copy: database/requirements.txt
```

## 5. Alembic infrastructure (under `database/`)

| File | Role |
|---|---|
| `database/alembic.ini` | Alembic config; URL placeholder only (env.py overrides it) |
| `database/migrations/env.py` | Offline + online env; URL from `DATABASE_URL` only; `target_metadata` is an empty `MetaData` with a marked hook for the backend team to wire its `Base.metadata` in once `backend/` models exist |
| `database/migrations/script.py.mako` | Standard migration template |
| `database/migrations/versions/20261104_0001_phase2_probe.py` | ONLY migration in Phase 2 (see §6) |
| `database/schemas/phase2-scope.md` | Scope guard: what exists vs. what is Phase 3 |
| `database/schemas/pooling.md` | Pooling contract for the backend team (see §7) |
| `database/scripts/health_check.py` | Health check (exit 0 only on a real query) |
| `database/scripts/probe_test.py` | Insert/retrieve + connection-failure test |
| `database/backup.sh`, `database/restore.sh` | Backup/restore (see §9) |

Coordination notes: `backend/` did not exist at the time of writing,
so no backend file was created, modified, or overwritten by Team D.
Sibling Team A skeleton files (`database/migrations/README.md`,
`database/schemas/README.md`, `database/seeds/README.md`,
`storage/*/README.md`) pre-existed this task and were left untouched;
Team D's files are the ones listed above.

## 6. Scope guard — ONLY a probe table in Phase 2

Migration `20261104_0001` creates exactly one business table:

```sql
-- phase2_probe
id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
probe_label VARCHAR(100) NOT NULL
note        TEXT
created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
-- index idx_phase2_probe_label on (probe_label)
-- plus Alembic's own alembic_version table (version_num = 20261104_0001)
```

This is an infrastructure probe, NOT business data and NOT PSX data.
It must never be presented as market data. Phase 3 entities are
deliberately NOT created here: `companies`, `securities`, `sectors`,
`market_prices`, `live_quotes`, `financial_statements`, `ratios`,
`forecasts`, `recommendations`, `portfolios`, `audit_logs`, and the
rest of the 33-table Phase 1 catalog (full list in
`database/schemas/phase2-scope.md`). Phase 3 must implement them from
the Phase 1 catalog (NUMERIC(19,4) money, TIMESTAMPTZ always,
provenance block, append-only history, RESTRICT on never-deleted
tables). A Phase 2 migration adding a Phase 3 table must be rejected
in review.

Note on timezones: `created_at` is `TIMESTAMPTZ`, so the server stores
an unambiguous instant (server timezone Etc/UTC) and presentation
converts to Asia/Karachi (PKT), exactly as Phase 1 §4.2 requires.
Probe rows therefore display `+00:00` from psql on this server and
`+05:00` when rendered in PKT — that is correct behaviour, not a bug.

## 7. Connection pooling (contract for the backend team)

Team D owns the server/role/database/Alembic side; the backend team
owns `backend/` engine code. The agreed settings (full rationale in
`database/schemas/pooling.md`):

```python
create_engine(os.environ["DATABASE_URL"],
              pool_size=5, max_overflow=10, pool_timeout=30,
              pool_recycle=1800, pool_pre_ping=True)
# Pool total per process <= 15, against PostgreSQL max_connections=100.
# NullPool is used ONLY in migrations/env.py (short-lived, single
# connection). Never raise pool_size to "fix" a slow query.
```

## 8. Test evidence (all run 2026-11-04, PKT = UTC+5)

### 8.1 Migration up

```bash
cd database && alembic upgrade head
# INFO [alembic.runtime.migration] Running upgrade  -> 20261104_0001, Phase 2 probe table only.
alembic current   # 20261104_0001 (head)
alembic history   # <base> -> 20261104_0001 (head), Phase 2 probe table only.
psql -c '\d phase2_probe'
# id bigint, generated always as identity, not null
# probe_label character varying(100), not null
# note text
# created_at timestamp with time zone, not null, default now()
# Indexes: pk_phase2_probe, idx_phase2_probe_label
```

### 8.2 Health check + insert/retrieve + failure handling

```bash
database/.venv/bin/python database/scripts/health_check.py
# HEALTH: connecting to localhost:5432/psx_intelligence ...
# HEALTH: OK — SELECT 1 returned 1, server_version=16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
# HEALTH: public tables: ['alembic_version', 'phase2_probe']
# HEALTH: alembic_version present (migrations tracked)   (exit 0)

database/.venv/bin/python database/scripts/probe_test.py
# PROBE: inserted id=1 created_at=2026-11-04 06:40:00.833771+00:00
# PROBE: retrieved label='phase2-probe-001'
#        note='TEST RECORD — NOT PSX DATA — Phase 2 infrastructure probe only' — MATCH
# PROBE: cleanup ok, probe row removed (count=0)
# PROBE: bad connection 1 correctly raised OperationalError:
#        connection to server at "127.0.0.1", port 59999 failed: Connection refused
# PROBE: bad connection 2 correctly raised OperationalError:
#        FATAL: database "psx_no_such_database" does not exist
# PROBE: ALL PASS   (exit 0)
```

The connection-failure subtest matters: a wrong port and a wrong
database both raise a clear `OperationalError` and the test treats
any unexpected success as a FAILURE. No fake "ok" is possible.

### 8.3 Migration down + fresh re-run (both succeed)

```bash
alembic downgrade base
# Running downgrade 20261104_0001 -> , Phase 2 probe table only.
psql -c '\dt'   # only alembic_version remains; phase2_probe is gone
alembic upgrade head
# Running upgrade  -> 20261104_0001, Phase 2 probe table only.
alembic current  # 20261104_0001 (head)
# probe_test.py re-run: ALL PASS (inserted id=1, retrieved, cleaned up)
```

### 8.4 Lessons from two real failures during setup (kept, not hidden)

1. **PGUSER leak:** sourcing `database/.env` exports `PGUSER=psx_app`,
   so a subsequent `su postgres -c "psql ..."` without `-U postgres`
   tried to authenticate as `psx_app` and failed. Fix: always pass
   `-U postgres` (and clear `PGUSER`/`PGPASSWORD` with `env -u`) for
   superuser commands. The same leak broke the first restore-DB
   creation attempt (§9); the retry with peer auth succeeded.
2. **Password quoting:** the first generated password (base64) broke
   psql `-v` variable quoting (`syntax error at or near ":"`). Fix:
   alphanumeric-only generated passwords for the role, and never
   interpolate a password into a SQL string by hand outside a single
   controlled creation command.
3. **Master-loop audit, 2026-11-04 ~11:42 PKT (after the first backup):**
   independent re-read found `backup.sh` masking tar failures with
   `|| true` + `2>/dev/null` (a failed file-store copy could have been
   reported as a successful backup) and `restore.sh` silently swallowing
   pg_restore's exit code. Fixes: tar now fails loudly under `set -e`
   and the archive is checked non-empty before the manifest is written;
   restore prints a warning on non-zero pg_restore exit and relies on
   the row-count gate as authoritative. Regression re-run after the
   fixes: health OK, probe ALL PASS, storage ALL PASS, new backup
   `2026-11-04T1142-PKT` (dump sha256
   `ee00e384001f23b160dc3c9b64339ae61193ab3e7c3164e67775f8ece93891d8`,
   row count 1) restored to `psx_intelligence_restore_test` and
   VERIFIED (1 = manifest). Full defect table is in the Team D final
   report for entry in `DEFECT_REGISTER.md` by the coordinator.

## 9. Backup and restore — scripts, rules, and tested evidence

Scripts: `database/backup.sh`, `database/restore.sh`
(pg_dump custom format `-Fc` / pg_restore). Credentials come only
from the environment (or `database/.env` sourced by the script);
no credential is written into either script.

### 9.1 Inclusion / exclusion rules

- INCLUDED: `database.dump`, `raw/`, `processed/`,
  `financial_reports/`, `parquet/`, `research_reports/`, `manifests/`.
- EXCLUDED: `backups/` itself (would recurse), `tmp/` (scratch, no
  retention value, freely deletable per retention policy §4.7),
  `quarantine/` (reviewed separately as quality issues, 90-day review).
- Every backup writes `manifest.json` (`backup-manifest-v1`): PKT
  timestamp, PostgreSQL version, Alembic revision, SHA-256 of the dump
  and of the file archive, and row counts. A backup without a verified
  manifest is not a backup.
- **A verified backup MUST exist before any major schema change**
  (a migration touching existing tables, partition changes, or any
  restore). This is a hard rule, not a suggestion.
- Rotation (retention policy §4.6): daily 30 days → weekly 12 weeks →
  monthly 12 months → yearly indefinitely where it holds never-deleted
  classes. Floor: NEVER rotate below 2 verified backups + 1 yearly
  snapshot. Phase 2 has exactly ONE backup (below), so NO rotation
  deletion may happen yet — a rotation job that would breach the
  floor must stop and alert.

### 9.2 Tested backup (2026-11-04, 11:40 PKT)

A fixture row was inserted first so the backup actually contains
something verifiable (label `phase2-backup-probe`, note marked
TEST / NOT PSX DATA; it remains in the live DB as the backup's
evidence row):

```bash
bash database/backup.sh
# backup: database=psx_intelligence host=localhost:5432
#   -> storage/backups/2026-11-04T1140-PKT/
# backup: done. manifest=.../manifest.json
# backup: database.dump sha256=69f773175d8abb96f2222884c3c21775ebb5e670f36ea11fda2aeaf4e5a17125
# database.dump 4.5K, files.tar.gz 1.6K, manifest.json 630 bytes
# manifest: postgres_version "16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)",
#   alembic_revision "20261104_0001", row_counts {"phase2_probe": 1}
# Independent re-hash check: database.dump manifest-match,
#   files.tar.gz manifest-match (files.tar.gz sha256
#   555c5b8f5994c0ad5216942107c908931b16815db41f515dbb48bb8911659ec6)
# files.tar.gz contents include raw/, processed/ (incl. the Phase 2
#   demo file + sidecar), financial_reports/, parquet/,
#   research_reports/, manifests/ — and NOT backups/, tmp/, quarantine/.
```

### 9.3 Tested restore (to a SEPARATE database)

```bash
# Guard test: restoring over live is refused without an explicit flag.
bash database/restore.sh storage/backups/2026-11-04T1140-PKT/ psx_intelligence
# restore: REFUSED — target is the live database. Set ALLOW_LIVE_RESTORE=1
#   only after taking a verified backup of the live database.  (exit 2)

# Target DB created once by the superuser (peer auth), then granted to psx_app:
#   CREATE DATABASE psx_intelligence_restore_test OWNER postgres ENCODING 'UTF8';
#   GRANT CONNECT / USAGE,CREATE + default privileges to psx_app (as in §4)

bash database/restore.sh storage/backups/2026-11-04T1140-PKT/ psx_intelligence_restore_test
# restore: dump hash OK (69f77317...)
# restore: pg_restore into psx_intelligence_restore_test (clean, if-exists)...
# restore: phase2_probe rows restored=1 expected(manifest)=1
# restore: VERIFIED — row count matches manifest.   (exit 0)

psql -d psx_intelligence_restore_test -c 'SELECT id, probe_label, note FROM phase2_probe;'
#  id | probe_label        | note
# ----+--------------------+-----------------------------------------------------
#   2 | phase2-backup-probe | TEST RECORD — NOT PSX DATA — backup/restore fixture
psql -d psx_intelligence_restore_test -c 'SELECT version_num FROM alembic_version;'
#  20261104_0001
```

Known harmless warnings during restore (documented, not hidden):
pg_restore reports 2 errors — `permission denied to change default
privileges` for `ALTER DEFAULT PRIVILEGES FOR ROLE postgres ...` —
because the dump carries the live DB's postgres-owned default
privileges and the restore runs as `psx_app`, which can only change
its own. The tables themselves restore under `psx_app` ownership and
the row-count gate (the authoritative check) passes. Files are NOT
auto-extracted over the live store by `restore.sh`: the archive's
hash is printed and extraction into a staging directory is an
explicit operator step.

### 9.4 How to verify any future backup (operator checklist)

```bash
sha256sum storage/backups/<stamp>-PKT/database.dump   # compare to manifest
sha256sum storage/backups/<stamp>-PKT/files.tar.gz     # compare to manifest
bash database/restore.sh storage/backups/<stamp>-PKT/ psx_intelligence_restore_test
# Must print "VERIFIED — row count matches manifest" and exit 0.
```

## 10. What Phase 2 does NOT do (boundaries)

- No Phase 3 schema, no seed/market data, no PSX dataset download,
  no full-scale collection (probe rows only, labelled as tests).
- No MinIO adoption (gate G-07): no MinIO code path, no paid tier.
- No backend/ code, no frontend change, no git commit.
- No backup rotation automation yet (see §9.1 floor — manual until
  Phase 3, and never below the floor).
- No production hardening beyond this single-host setup: no TLS,
  replication, or PITR is claimed. If Phase 3 needs those, they are
  new, separately documented decisions — not silent additions here.

## 11. Reproduce from scratch (operator quick path)

```bash
pg_ctlcluster 16 main start          # if the cluster is down (§3)
set -a; source database/.env; set +a # gitignored .env, mode 0600
cd database
.venv/bin/alembic upgrade head
.venv/bin/python scripts/health_check.py    # expect HEALTH: OK, exit 0
.venv/bin/python scripts/probe_test.py      # expect PROBE: ALL PASS, exit 0
bash backup.sh                              # expect manifest + hashes
```
