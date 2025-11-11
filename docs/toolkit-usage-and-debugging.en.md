# Toolkit Usage and Debugging Guide

## 1. Background & Goals
This guide explains how to build a document-rendering toolkit image that mirrors docassemble’s dependency stack, and how to run health checks and rendering proofs-of-concept locally or in CI. The image supports backend rendering development while staying aligned with `docassemble` in dependency versions and tooling capability.

## 2. Build Plan & Component List

- **Base image**: `ubuntu:22.04`, enable `deadsnakes/ppa` to install Python 3.11.  
- **Multi-stage layout**:
  1. `base`: Install system dependencies (LibreOffice, Pandoc, ImageMagick, qpdf, pdftk, etc.) and the Python runtime.
  2. `deps-builder`: Use `pip download` to prefetch Python wheels required for rendering.
  3. `runtime`: Build a venv on top of `base`, install Python dependencies offline, copy scripts, and create a non-root user.
- **PoC output**: `make render-sample` produces DOCX/PDF/HTML/Markdown to validate the DOCX rendering and conversion pipeline.

| Category | Component | Version/Source | Purpose |
| --- | --- | --- | --- |
| Python | Python 3.11, `docxtpl`, `python-docx`, `docxcompose`, `pikepdf`, `xfdfgen` | Aligned with `docassemble 1.8.18` | Support DOCX rendering and PDF form filling. |
| Conversion | LibreOffice, Pandoc 3.x, unoconv, qpdf, pdftk-java, ImageMagick, ghostscript | Ubuntu 22.04 repo | DOCX → PDF → {HTML, Markdown} conversions and PDF flattening. |
| Utilities | fonts-dejavu, fonts-noto-cjk, poppler-utils, tesseract-ocr | Ubuntu 22.04 repo | Fonts and PDF/image utilities. |
| Tooling | `pip download`, `make`, Docker Compose | Direct install | Prefetch dependencies, orchestrate tasks, and wrap commands. |

> **Differences vs. ReferenceProjects/docassemble**  
> - Excludes large services (Postgres, Redis, Celery) and keeps only rendering/conversion capabilities.  
> - Ships rendering scripts in `/opt/scripts`, exposing `healthcheck` and `render-sample` via the `Makefile`.  
> - Reserves `/workspace/tmp` and `/workspace/output` for mounting host directories during debugging.

## 3. Project Structure
```
infra/
  Dockerfile               # Multi-stage build
  docker-compose.yml       # Local run config (service name: toolkit)
  python/requirements.txt  # Rendering-related Python deps
  scripts/
    entrypoint.sh          # Unified entry point (bash by default)
    healthcheck.sh         # External tool & Python package detection
    render_sample.sh       # Calls render_sample.py and shows outputs
    render_sample.py       # DOCX rendering + LibreOffice/Pandoc conversions
  output/                  # Host-mounted output directory
  tmp/                     # Temporary files
Makefile                   # Convenience commands (build/healthcheck/render-sample/etc.)
```

## 4. Usage Workflow
1. **Build the image**
   ```bash
   make build
   ```
   - Builds `cirkidzdoc/toolkit:dev` from `infra/Dockerfile`.
   - Check `docker image ls` to confirm timestamps when the image already exists.

2. **Run the health check**
   ```bash
   make healthcheck
   ```
   - Verifies `python3.11`, `pandoc`, `soffice`, `qpdf`, `pdftk`, `unoconv`, and `convert`.
   - Imports Python modules such as `docxtpl` and `pikepdf` to confirm availability.
   - Prints `All dependency checks passed ✅` on success.

3. **Render the sample PoC**
   ```bash
   make render-sample
   ```
   - Generates a DOCX template with placeholders and renders it via `docxtpl`.
   - Converts to PDF with LibreOffice, then to HTML and Markdown with Pandoc.
   - Outputs are stored under `infra/output/` for direct inspection on the host:
     - `sample_rendered.docx`
     - `sample_rendered.pdf`
     - `sample_rendered.html`
     - `sample_rendered.md`

4. **Open an interactive shell**
   ```bash
   make shell
   ```
   - Drops into a non-root (`appuser`) bash session for manual conversion commands.

5. **Clean up**
   ```bash
   make clean
   docker compose -f infra/docker-compose.yml down --remove-orphans
   ```

## 5. Debugging Tips & Common Issues
- **LibreOffice fails to start**: Ensure the host architecture is x86_64. Install extra fonts (e.g., `fonts-noto-serif`) in the Dockerfile if missing fonts trigger errors.
- **ImageMagick policy restrictions**: `convert` ships with restrictive policies by default. Copy a custom `policy.xml` if you need PDF → image conversions.
- **pikepdf dependency missing**: The image installs `libqpdf-dev`. If loading still fails, verify the host kernel/CPU supports AVX2.
- **unoconv cannot find UNO**: The image includes `python3-uno` and presets `PYTHONPATH=/usr/lib/python3/dist-packages` plus `UNO_PATH=/usr/lib/libreoffice/program` in `healthcheck.sh`. Mirror these variables when invoking unoconv manually.
- **Performance validation**: Run `make healthcheck` in CI and treat `render-sample` as a smoke test to confirm the rendering chain end-to-end.

## 6. Future Enhancements
- Expand `infra/docker-compose.yml` into a multi-service stack that includes FastAPI and Redis for upcoming task-orchestration tests.
- Add `convert_pipeline.sh` under `infra/scripts/` to exercise more DOCX → format combinations for integration tests.
- Continuously compare dependency versions with `ReferenceProjects/docassemble`, recording updates in `uv.lock` and ADRs to keep upgrades transparent.

> When the image powers production rendering, pair it with Helm charts or Compose templates under `deploy/` and add health probes/monitoring endpoints.


