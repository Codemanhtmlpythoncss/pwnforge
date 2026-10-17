#!/usr/bin/env bash
# Thin wrapper around `hacklab doctor` for operators.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
[ -d .venv ] && . .venv/bin/activate
exec hacklab doctor
