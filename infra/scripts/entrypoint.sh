#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  exec /bin/bash
else
  exec "$@"
fi

