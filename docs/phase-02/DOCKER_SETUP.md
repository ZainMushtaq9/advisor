# PSX Intelligence AI — Docker Setup (Phase 2, Team E)

> Status: **DEFINITION ONLY — NOT VERIFIED RUNNING.** The Docker Engine
> daemon runs on this VM, but no image has been pulled, built, or started
> here (blocker D-05 below). Nothing in this document claims a container
> ran. The verified path today is `scripts/dev.sh` (no Docker) — see
> `LOCAL_DEVELOPMENT_GUIDE.md`.
>
> Phase 1 basis: `docs/phase-01/DEPLOYMENT_ARCHITECTURE.md` §4 Configs B/C
> and `docs/phase-01/ADR/ADR-009-deployment-and-local-dev.md` — Docker
> Engine (Linux) + Compose is the packaging definition; local dev retains
> a no-Docker path because Docker was not installed.

## 1. Docker Engine on this VM — installed, daemon running, pulls blocked

| Item | Evidence (2026-11-04) |
|---|---|
| Engine package | Ubuntu `docker.io` 29.1.3-0ubuntu3~24.04.2, `docker-compose-v2` 2.40.3+ds1-0ubuntu1~24.04.1, installed via apt (free, no subscription). `docker --version` → `Docker version 29.1.3`; `docker compose version` → `2.40.3`. |
| Engine licence | Apache-2.0 — `/usr/share/doc/docker.io/copyright`, `Files: * / License: Apache-2.0` (upstream moby/moby). This is **Docker Engine on Linux**, not Docker Desktop: Desktop's licence terms are a different product and are not assumed or relied on here. |
| Daemon start | systemd start was denied (`invoke-rc.d: policy-rc.d denied execution of start`, same as Redis). The daemon was started manually: `dockerd --iptables=false --bridge=none` (background). `docker info` then reported `Server Version: 29.1.3`, `Storage Driver: overlayfs`, 0 containers, 0 images. Warnings recorded, not hidden: no memory/swap/cpu cgroup limit support, IPv4 forwarding disabled, ip6tables chains could not be created (permission). Those limits mean container resource limits and bridge networking cannot be relied on in this VM until the host configuration changes. |
| Image pulls | **BLOCKED (D-05).** `docker pull hello-world`, `docker pull redis:7.0-alpine`, and `docker build` from `python:3.12-slim` all fail the same way: `failed to do request: Head "https://registry-1.docker.io/..."` / blob fetch → `net/http: TLS handshake timeout`. The registry host itself is reachable from this shell (curl to `https://registry-1.docker.io/v2/` returns HTTP 401, the registry's normal unauthenticated answer), so this is a daemon-to-registry TLS path failure in this VM, not proof the registry is down and not a reason to retry blindly. `docker images` remains empty. |

**Consequence, stated plainly:** Compose and the Dockerfiles below are
written, YAML-validated, and config-validated — but **no container has
been built or run from them on this VM**, and no Docker-based health
check, port, or volume claim is verified. Anyone re-running this on a
machine with working registry access must run §5 and record the result
before calling Compose verified.

## 2. Files (Team E scope only — other teams' files untouched)

| File | Role |
|---|---|
| `deployment/docker-compose.yml` | Five services: frontend, backend, postgres, redis, worker. See §3. |
| `deployment/Dockerfile.backend` | Python 3.12-slim; installs from `backend/requirements.txt` (Team C's verified pins — no second pin list); runs `uvicorn app.main:app` on 8000; health check via stdlib urllib on `/health`; runs as non-root `appuser` (uid 10001). |
| `deployment/Dockerfile.frontend` | Node 24-slim (matches local Node v24.22.1); `npm ci` from Team B's `package.json`/`package-lock.json`, `npm run build`, `npm start` on 3000; health check via Node stdlib http; runs as `node`. |
| `deployment/Dockerfile.worker` | Python 3.12-slim; installs from `workers/requirements.txt`; runs `celery -A workers.celery_app worker`; health check via `celery inspect ping`; non-root `appuser`. Probe tasks only. |
| `deployment/.env.example` | Placeholders only (`POSTGRES_PASSWORD=changeme-dev-only`, etc.). Copy to `deployment/.env` and change before any non-local use. Never commit a real `.env`. |

Base-image tags are **choices, not verified pulls**: `python:3.12-slim`,
`node:24-slim`, `postgres:16-alpine`, `redis:7.0-alpine`. Postgres 16
matches the database team's verified cluster (PostgreSQL 16.15, port
5432, database `psx_intelligence` — `database/schemas/phase2-scope.md`);
Redis 7.0 matches the apt install (7.0.15, BSD era). Pin digests at the
first successful pull; do not copy a digest from a web page.

**MinIO is absent on purpose:** Phase 1 gate G-07 — OPTIONAL/NOT ADOPTED.
No MinIO service, image, or volume appears in Compose.

## 3. Compose design

- **Services / ports (loopback-only in dev):** frontend `127.0.0.1:3000`,
  backend `127.0.0.1:8000`, postgres `127.0.0.1:5432`, redis
  `127.0.0.1:6379`. Worker publishes no port.
- **Network separation:** `app_net` = frontend, backend, worker;
  `data_net` = postgres, redis, backend, worker. The frontend is not on
  `data_net`, so it cannot reach postgres/redis directly. Backend and
  worker sit on both networks (API + data plane).
- **Dependencies with health gates:** backend waits for postgres + redis
  `service_healthy`; worker waits for redis `service_healthy` and backend
  `service_started`; frontend waits for backend `service_healthy`.
- **Health checks (using only tools present in each image):**
  postgres `pg_isready`; redis `redis-cli ping`; backend stdlib urllib
  `GET /health`; frontend Node stdlib http `GET /`; worker
  `celery inspect ping`.
- **Restart policies:** `unless-stopped` on all five services.
- **Persistent volumes:** `pgdata` → postgres data dir; `redisdata` →
  redis `/data` (with `--appendonly yes`); `psx_storage` → `/data` on
  backend + worker, reserved for future Parquet/raw storage use — the
  Phase 2 backend does not yet read that path, so the mount reserves the
  location only and claims no integration.
- **Environment wiring (matches the other teams' actual files):**
  backend `DATABASE_URL=postgresql+psycopg://<user>:<password>@postgres:5432/psx_intelligence`
  (database name/port from Team D; `postgresql+psycopg` matches the
  backend's psycopg driver), `CORS_ORIGINS` for `:3000` (from
  `backend/.env.example`), `CELERY_BROKER_URL` /
  `CELERY_RESULT_BACKEND=redis://redis:6379/1` (service name, not
  loopback, inside Compose; DB numbers per Team A contract).
  Frontend `NEXT_PUBLIC_API_URL`
  points at the host backend (`http://localhost:8000`) for local dev.

## 4. Validation actually performed (and its limits)

- `docker compose config --quiet` → **valid**; rendered config lists all
  five services, both networks, all three volumes.
- YAML parsed independently (PyYAML): services, networks, volumes as in §3.
- `docker build -f deployment/Dockerfile.worker` → **failed at Step 1/10
  (`FROM python:3.12-slim`)** with the D-05 TLS timeout while fetching
  the image blob; build context sent was 1.016 GB (see D-04). Zero images
  exist afterwards. This failure is evidence for D-05, not a build pass.

## 5. To verify Compose on a machine with registry access (not done here)

```bash
cp deployment/.env.example deployment/.env   # then change POSTGRES_PASSWORD
cd deployment
docker compose up -d --build
docker compose ps                            # all five (healthy) required
docker compose exec redis redis-cli ping     # PONG
docker compose exec postgres pg_isready      # accepting connections
curl http://127.0.0.1:8000/health            # {"status":"ok",...}
curl http://127.0.0.1:3000/                  # 200
docker compose exec worker celery -A workers.celery_app inspect ping
docker compose down -v   # only with -v if wiping volumes is intended
```

Until that run is recorded, Compose stays "definition only".

## 6. Defects / blockers (for DEFECT_REGISTER.md)

| ID / severity | Issue | Root cause / evidence | Fix or next step | Retest |
|---|---|---|---|---|
| D-05 / High (blocker, environment) | No Docker image can be pulled or built on this VM; therefore no container has run. | Daemon-to-registry TLS handshake timeout on every pull (`hello-world`, `redis:7.0-alpine`, `python:3.12-slim` blob), while shell curl to the registry returns 401 (host reachable). Daemon runs with proxy env present, so this is not a missing-proxy case. | Do NOT claim Docker verified. Retry on a machine/network with working registry access, or fix the daemon TLS/proxy path with host-admin help, then run §5. Do not work around by copying an image from an untrusted source. | Re-run §5; record `docker compose ps` + all health outputs. |
| D-04 / Medium (build performance, not a run failure) | `docker build` sent a 1.016 GB context (repo contains `frontend/node_modules`, `backend/.venv`, `.next`, etc.). | No `.dockerignore` at the repo root; Docker reads it from the context root only, and the context root is outside Team E's assigned directories, so Team E did not create one (scope rule) and instead records the fix here. | Coordinator / repo owner: add a repo-root `.dockerignore` excluding `node_modules`, `.venv`, `.next`, `.git`, `storage/**` data, `*.db`, and `deployment/.env` before the first real build. | First successful build should show a context of a few MB, not ~1 GB. |
| (Environment note, not a defect) | systemd does not start redis/docker services on this VM (`policy-rc.d` denial); daemon warnings on cgroups/iptables/forwarding. | VM image policy, not project code. | Manual daemon starts are documented in `REDIS_SETUP.md` and §1 above; a host with systemd enabled would use `systemctl enable --now`. | N/A — revisit if the VM image changes. |

## 7. Live preview / external workspace note

The supplied `https://cuddly-system-jj7j95xv97x7fjv7.github.dev/` URL
returns only a GitHub sign-in page on text fetch. It is **not** an
operational terminal or filesystem for this work, was **not** used as a
runtime, no GitHub password was asked for or entered, and it is **not**
the application preview URL. The runtime remains this VM
(`~/workspace/psx-intelligence-ai/`). Any live preview that cannot be
opened from here is **UNVERIFIED** for that reason — no preview pass is
claimed anywhere in Phase 2 Team E work.
