#!/usr/bin/env bash
set -euo pipefail

echo "[healthcheck] 开始依赖探测..."

# 为 unoconv/pyuno 预设路径，避免 Python 3.11 缺少 dist-packages
export PYTHONPATH="/usr/lib/python3/dist-packages:${PYTHONPATH:-}"
export UNO_PATH="${UNO_PATH:-/usr/lib/libreoffice/program}"

declare -a CHECKS=(
  "python3.11 --version"
  "pandoc --version"
  "soffice --headless --version"
  "qpdf --version"
  "unoconv --version"
  "convert --version"
)

for check in "${CHECKS[@]}"; do
  name="${check%% *}"
  if command -v "${check%% *}" >/dev/null 2>&1; then
    if eval "${check} >/tmp/${name}.log 2>&1"; then
      echo "[healthcheck] ${name} ✓"
    else
      cat "/tmp/${name}.log" >&2 || true
      echo "[healthcheck] ${name} ✗" >&2
      exit 1
    fi
  else
    echo "[healthcheck] 未找到命令：${name}" >&2
    exit 1
  fi
done

# pdftk-java 的 --version 输出到 stderr，单独处理
if command -v pdftk >/dev/null 2>&1; then
  if pdftk --version >/tmp/pdftk.log 2>&1; then
    echo "[healthcheck] pdftk ✓"
  else
    cat /tmp/pdftk.log >&2 || true
    echo "[healthcheck] pdftk ✗" >&2
    exit 1
  fi
else
  echo "[healthcheck] 未找到命令：pdftk" >&2
  exit 1
fi

python3.11 - <<'PY'
import importlib
packages = [
    "docxtpl",
    "docxcompose",
    "docx",
    "jinja2",
    "PIL",
    "pikepdf",
    "xfdfgen",
]
missing = []
for pkg in packages:
    try:
        importlib.import_module(pkg)
    except Exception as exc:  # pragma: no cover
        missing.append((pkg, str(exc)))

if missing:
    for pkg, err in missing:
        print(f"[healthcheck] Python 包加载失败: {pkg}: {err}", flush=True)
    raise SystemExit(1)
else:
    print("[healthcheck] Python 包加载全部通过")
PY

echo "[healthcheck] 所有依赖探测通过 ✅"

