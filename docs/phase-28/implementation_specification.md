# Phase 28 — Implementation Specification

## Brief (playbook lines 1974–2031)

Deployment, Local Operations, Backup and Disaster Recovery. Objective:
package the system for repeatable operation using free/self-hosted
infrastructure and documented runtime limits. Required deliverables:
deployment package and runbooks; secure configuration and environment
templates; backup/restore scripts and drill report; fresh-environment
deployment test. Acceptance gate: system starts from clean documented
setup; backup restore is proven; no hidden paid dependency exists;
operational uptime limitations are explicit.

## Design decisions (with reasons)

1. **Process-based, not container-based.** The user decision of 2026-11-04
   bans Docker anywhere in this project. The Phase 2 `deployment/`
   Dockerfiles and `docker-compose.yml` therefore stay in the repo as
   history but are NOT part of the deployment package: nothing in `ops/`
   invokes Docker (enforced by `test_deployment_phase28.py`), and the
   deployment guide marks them superseded. Deleting them was considered
   and rejected: deletion is destructive and needs its own authorization;
   documenting them as not-used is honest and reversible.
2. **No daemon, no hosted scheduler.** Phase 25 deliberately replaced
   Redis/Celery with a DB-backed, operator-invoked job framework (the
   database itself is the queue; a broker/worker pair is exactly what a
   VM replacement kills). The production stack therefore has no worker
   process: `ops/start.sh` prints the `run-due` reminder instead of
   starting one, and `scripts/dev.sh` (Redis/Celery) is documented as
   dev-only. A host cron running `run-due` is the operator's option,
   not something this phase installs (installing a cron is a persistent
   operator decision, not taken here).
3. **Loopback only, no TLS termination in the project.** Backend binds
   127.0.0.1:8000, frontend 127.0.0.1:3000, PostgreSQL 127.0.0.1:5432.
   No firewall rule is needed for loopback. If the system is ever
   exposed beyond loopback, a TLS reverse proxy is REQUIRED first, and
   that proxy is NOT configured here — the limitation is explicit, not
   hidden behind a claim of secure remote access.
4. **Backup manifest carries full counts (Phase 28 extension).** The
   Phase 2 manifest recorded only `phase2_probe`, which cannot prove a
   real restore. `database/backup.sh` now records 40 key-table counts
   (authoritative state only; audit/log tables excluded on purpose —
   they grow on every run and would false-fail the gate). A table
   missing at backup time is recorded as null, never zero.
5. **Encryption is opt-in, never by default, and never with a
   project-created key.** `BACKUP_GPG_RECIPIENT` unset = plaintext
   backups (current default, unchanged). Set = both outputs encrypted
   with GPG and plaintext removed after successful encryption; the
   manifest keeps both hash sets. No key is created by this project:
   key creation, storage, and passphrase custody are operator decisions
   (documented in the retention policy). The round-trip is proven with
   an ephemeral test key (see restore_drill.md), not with a persistent key.
6. **No new database migration.** Phase 28 needs no new tables:
   manifests live on disk, run evidence lives in the Phase 25/26/27
   tables. Migration head stays 20261104_0023.
7. **No live auth accounts.** The Phase 24 decision stands: auth tables
   stay 0/0/0 until a parent/user decision creates the first admin.
   Production boot with `AUTH_ENFORCEMENT=on` and zero accounts is
   fail-closed (401), which the deployment guide states plainly.

## What was built

| File | Purpose |
|---|---|
| `ops/start.sh` | Start postgres (if down) + backend + frontend (production build only). |
| `ops/stop.sh` | Stop backend + frontend started by start.sh. Never touches postgres. |
| `ops/status.sh` | Read-only: health + job status + latest backup. |
| `ops/healthcheck.sh` | Production health: postgres, backend `/health`, frontend `/`, migration match. |
| `ops/update.sh` | Safe update: dirty-tree refusal → backup → `git pull --ff-only` → `alembic upgrade head` → restart → health gate. Never restores over live by itself. |
| `ops/install.sh` | Instantiate systemd units (default: validate into a temp dir only; `--install` writes to /etc/systemd/system, root, explicit operator decision). |
| `ops/systemd/psx-backend.service`, `psx-frontend.service` | Service definitions; secrets via `EnvironmentFile` (database/.env), never embedded. |
| `ops/env.production.example` | Production env template (placeholders only). |
| `ops/prune_backups.sh` | Retention pruning: dry-run default, `--confirm` deletes. |
| `ops/README.md` | Package overview + uptime limitations. |
| `database/backup.sh` (extended) | Full-counts manifest + optional GPG encryption. |
| `database/restore.sh` (extended) | Decrypt pre-step for `.gpg` backups; otherwise unchanged (restore-test default, live refusal). |
| `database/verify_restore.sh` (new) | Restore gate: manifest hashes + restored-vs-manifest counts + alembic revision. Never mutates the backup dir (decrypts to temp). |
| `backend/tests/test_deployment_phase28.py` (new) | Dependency allowlist gate, template secret scan, Docker-ban enforcement, systemd unit validation, backup-script markers. |

## What is NOT_CALCULABLE / not delivered (with reasons)

- **No encrypted production backup exists yet.** The mechanism is
  delivered and round-trip proven with an ephemeral key, but no
  persistent operator key exists, so no production backup is encrypted.
  Unblocker: operator creates a GPG keypair and sets
  `BACKUP_GPG_RECIPIENT` (exact steps in backup_retention_policy.md).
- **No system-wide service installation.** Units are validated into a
  temp dir, not installed into /etc/systemd/system: installing is a
  persistent operator decision (`ops/install.sh --install` + enable).
- **No host cron for jobs.** `run-due` stays operator-invoked (Phase 25
  design). A cron is the operator's option, not installed here.
- **No TLS, no public hosting, no 24/7 availability.** Loopback only;
  everything stops when the computer is off (see operations_handover.md).
- **No backup schedule.** Backups are operator-invoked; RPO is therefore
  "time since the last operator backup", not a guaranteed window.
  The policy recommends daily backups and a pre-migration backup.
- **No Windows service definitions.** Windows is dev-only for this
  project; the production target is Linux (this VM). Windows differences
  are documented, not implemented.

## Security finding fixed during this run (not hidden)

`database/.env.example` (a COMMITTED template) contained two
credential-looking values: the password inside its `DATABASE_URL` and
its `PGPASSWORD` line (both 9 characters, same dummy value). Hash
comparison against the real `database/.env` password proved they do NOT
match the live credential — no live leak — but a committed template
must never carry a credential-looking value. Both were replaced with
the explicit placeholder `CHANGEME`. The new template-scan test fails
any future template that carries a non-placeholder secret value.
The real `database/.env` was not touched, and no password value is
printed anywhere in this phase's outputs.
