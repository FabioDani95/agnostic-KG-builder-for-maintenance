#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

export KG_RELOAD="${KG_RELOAD:-1}"
exec node scripts/dev_server.mjs
