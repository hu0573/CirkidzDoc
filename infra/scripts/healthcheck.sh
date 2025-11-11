#!/usr/bin/env bash
set -euo pipefail

echo "[healthcheck] Starting dependency checks..."

# Preconfigure paths for unoconv/pyuno to avoid missing dist-packages on Python 3.11.
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
    echo "[healthcheck] Command not found: ${name}" >&2
    exit 1
  fi
done

# pdftk-java writes --version to stderr, handle separately.
if command -v pdftk >/dev/null 2>&1; then
  if pdftk --version >/tmp/pdftk.log 2>&1; then
    echo "[healthcheck] pdftk ✓"
  else
    cat /tmp/pdftk.log >&2 || true
    echo "[healthcheck] pdftk ✗" >&2
    exit 1
  fi
else
  echo "[healthcheck] Command not found: pdftk" >&2
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
        print(f"[healthcheck] Failed to import Python package: {pkg}: {err}", flush=True)
    raise SystemExit(1)
else:
    print("[healthcheck] All Python package imports succeeded")
PY

echo "[healthcheck] All dependency checks passed ✅"

