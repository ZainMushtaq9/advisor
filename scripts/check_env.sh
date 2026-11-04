#!/usr/bin/env bash
# PSX Intelligence AI — environment check (Phase 2, Team A)
# Usage: bash scripts/check_env.sh
# This script ONLY reports. It installs nothing, downloads nothing, touches no
# credentials, and writes no files. A MISSING tool is a finding, not a failure
# of this script: see docs/phase-02/ENVIRONMENT_AUDIT.md for install methods.
set -u
ok()   { printf '  OK        %s\n' "$1"; }
miss() { printf '  MISSING   %s\n' "$1"; }
info() { printf '  INFO      %s\n' "$1"; }

echo "== OS / hardware =="
uname -a
grep -m1 'model name' /proc/cpuinfo || true
echo "CPUs: $(nproc 2>/dev/null || echo unknown)  Arch: $(uname -m)"
free -h 2>/dev/null | head -2 || true
df -h ~ 2>/dev/null | tail -1 || true

echo "== GPU (evidence for local-inference limits) =="
if command -v nvidia-smi >/dev/null 2>&1; then nvidia-smi | head -5; else miss "nvidia-smi (no NVIDIA GPU tooling)"; fi
ls /dev/nvidia* 2>/dev/null || miss "no /dev/nvidia* devices"

echo "== Runtimes & tools =="
for t in python3 node npm git pip3 curl wget make gcc jq; do
  if command -v "$t" >/dev/null 2>&1; then ok "$t: $($t --version 2>&1 | head -1)"; else miss "$t"; fi
done
python3 -m venv --help >/dev/null 2>&1 && ok "python3 venv module" || miss "python3 venv module"

echo "== Services (installed by OTHER teams / later Phase 2 steps, not Team A) =="
for t in docker psql redis-cli ollama tesseract; do
  if command -v "$t" >/dev/null 2>&1; then ok "$t: $($t --version 2>&1 | head -1)"; else miss "$t (see docs/phase-02/ENVIRONMENT_AUDIT.md)"; fi
done

echo "== Project hygiene =="
[ -f .env ] && info ".env EXISTS locally (must never be committed)" || info "no .env file (copy .env.example to create one)"
[ -f .env.example ] && ok ".env.example present" || miss ".env.example"
echo "Done. Full audit: docs/phase-02/ENVIRONMENT_AUDIT.md"
