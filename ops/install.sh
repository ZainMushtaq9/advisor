#!/usr/bin/env bash
# PSX Intelligence AI — systemd unit installer (Phase 28).
# Instantiates ops/systemd/*.service with the real install path and service
# user, then validates the result with `systemd-analyze verify`.
#
# SAFETY: by default this writes ONLY to a --dest directory (default: a
# temporary directory) and validates there. It installs into
# /etc/systemd/system ONLY with --install, which requires root and is an
# explicit operator decision (enabling + starting the units afterwards is
# also the operator's step: systemctl daemon-reload && systemctl enable
# --now psx-backend psx-frontend). This script never enables, starts, or
# restarts any service by itself.
#
# The service user defaults to the current user. For a shared machine,
# create a dedicated unprivileged user with read access to the checkout
# and the psx_app database role, and pass --user <name>.
#
# Usage:
#   ops/install.sh [--user NAME] [--dest DIR] [--install]
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_USER="$(whoami)"
DEST=""
INSTALL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --user) SERVICE_USER="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;;
    --install) INSTALL=1; shift ;;
    *) echo "usage: $0 [--user NAME] [--dest DIR] [--install]" >&2; exit 2 ;;
  esac
done
if [ "$INSTALL" -eq 1 ]; then
  DEST="/etc/systemd/system"
  [ "$(id -u)" -eq 0 ] || { echo "install: --install requires root" >&2; exit 2; }
else
  DEST="${DEST:-$(mktemp -d)}"
fi
mkdir -p "$DEST"
for unit in psx-backend psx-frontend; do
  sed -e "s|@INSTALL_PATH@|$ROOT|g" -e "s|@SERVICE_USER@|$SERVICE_USER|g" \
    "$ROOT/ops/systemd/$unit.service" >"$DEST/$unit.service"
  echo "install: wrote $DEST/$unit.service (user=$SERVICE_USER, path=$ROOT)"
done
if command -v systemd-analyze >/dev/null 2>&1; then
  # Verify the instantiated units. systemd-analyze verify prints warnings
  # for unknown users on some versions; a non-zero exit is treated as a
  # failure here, and the operator must resolve it before --install.
  systemd-analyze verify "$DEST/psx-backend.service" "$DEST/psx-frontend.service" \
    && echo "install: systemd-analyze verify PASSED" \
    || { echo "install: systemd-analyze verify FAILED — resolve before installing" >&2; exit 1; }
else
  echo "install: systemd-analyze absent — units written but NOT validated (validate on a systemd host before use)"
fi
if [ "$INSTALL" -eq 1 ]; then
  echo "install: DONE. Next (operator): systemctl daemon-reload && systemctl enable --now psx-backend psx-frontend"
else
  echo "install: validation copy at $DEST (nothing installed system-wide)"
fi
