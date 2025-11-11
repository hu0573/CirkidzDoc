#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="${RENDER_OUTPUT_DIR:-/workspace/output}"
TMP_DIR="${RENDER_TMP_DIR:-/workspace/tmp}"

mkdir -p "${OUTPUT_DIR}" "${TMP_DIR}"

echo "[render-sample] 使用输出目录 ${OUTPUT_DIR}"

python3.11 /opt/scripts/render_sample.py

echo "[render-sample] 生成结果："
ls -lh "${OUTPUT_DIR}"

