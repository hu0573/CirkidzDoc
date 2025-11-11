#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="${RENDER_OUTPUT_DIR:-/workspace/output}"
TMP_DIR="${RENDER_TMP_DIR:-/workspace/tmp}"

mkdir -p "${OUTPUT_DIR}" "${TMP_DIR}"

echo "[render-sample] Using output directory ${OUTPUT_DIR}"

python3.11 /opt/scripts/render_sample.py

echo "[render-sample] Generated results:"
ls -lh "${OUTPUT_DIR}"

