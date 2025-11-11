## docassemble Capability Decomposition Research Report

### 1. Research Goals
1. Identify the core dependencies and runtime requirements needed to extract document template rendering and format-conversion capabilities from docassemble.
2. Define a reusable image build strategy so the new service matches the original docassemble environment in functionality and version alignment.
3. Summarize common debugging scenarios and troubleshooting approaches to guide engineering and operations.

### 2. Dependency Landscape
| Area | Dependencies/Tools | Recommended Versions | Notes |
| --- | --- | --- | --- |
| DOCX Rendering | `docxtpl`, `python-docx`, `docxcompose`, `jinja2`, `Pillow` | Align with docassemble 1.8.18 (`docxtpl`==0.20.1) | Supports images, sub-templates, and conditional logic. |
| PDF Filling | `xfdfgen`, `pdftk`, `pikepdf`, `qpdf`, `ghostscript` | `pikepdf` ≥ 9.0, `qpdf` ≥ 11.0 | `pdftk` handles form fill/flattening, `pikepdf` writes fields, `ghostscript` produces PDF/A. |
| Format Conversion | LibreOffice (`soffice`), Pandoc, `unoconv`, ImageMagick | LibreOffice 7.5+, Pandoc 3.x | DOCX → PDF → HTML/RTF/Markdown; ImageMagick pre-processes images. |
| Runtime & Tooling | Python 3.11, `pip`, `uv`, `make`, `just`, Node.js 20 | - | `uv` locks dependencies; Makefile/justfile orchestrate tasks. |
| Storage | Postgres / SQLite, Redis (optional) | - | Persist task metadata and queue state. |

### 3. Image Build Strategy
1. **Base Image**: Ubuntu 22.04 LTS with system packages (`libreoffice`, `pandoc`, `ghostscript`, `imagemagick`, `qpdf`, `pdftk`, `poppler-utils`).
2. **Multi-stage Build**:  
   - **Stage 1 (deps-builder)**: Install heavy system deps and Python packages, producing an offline wheel cache.  
   - **Stage 2 (runtime)**: Copy wheels, node_modules cache, and config; install Python deps via `uv pip sync`; create a non-root user.  
3. **Alignment with docassemble**: Compare against `ReferenceProjects/docassemble/Dockerfile` and related `pyproject.toml` files, aligning `apt` and `pip` versions (baseline docassemble 1.8.18). Record differences in ADRs.  
4. **Build Validation**: Run `pandoc --version`, `soffice --headless --version`, `qpdf --version` inside the image and execute `make render-sample` to validate the pipeline.

### 4. Runtime & Debugging Guidance
- **Logging**: Use structured logging (`structlog` / `loguru`) and capture stdout/stderr from external commands in per-task logs.
- **Command Execution**: Control timeouts and resource usage via `asyncio.subprocess` or `anyio.run_process`; provide clear error-code mapping.
- **Health Checks**: Load template metadata on startup, verify required files, and periodically run dependency probes (`pandoc --version`, etc.).
- **Local Development**: Provide `docker-compose.yml` with FastAPI, optional Redis, and the LibreOffice/Pandoc toolkit; align environments via VS Code Dev Container.
- **Regression Testing**: Maintain a sample template suite (e.g., 3 DOCX, 1 PDF) and write Pytest integration tests with snapshot comparisons.

### 5. Version Alignment Strategy
1. **Dependency Locking**: Generate `uv.lock` using `uv pip compile`, enforce with `uv pip sync --locked` in CI.
2. **Diff Tooling**: Script comparisons against `ReferenceProjects/docassemble/docassemble_base/pyproject.toml` to surface version differences.
3. **Upgrade Process**: Update dependencies on a dev branch, run `make healthcheck` plus integration tests, then merge to main.

### 6. Common Issues & Diagnostics
- **LibreOffice fails to start**: Check `/tmp` permissions and fonts; install `fonts-noto-cjk` if necessary.
- **PDF flattening failures**: Often caused by incompatible `ghostscript` versions—try `-dCompatibilityLevel=1.7`.
- **Pandoc styling loss**: Provide reference style files (CSL/templates) or run `docxcompose` to refresh references before conversion.
- **Task timeouts**: Apply 120s command timeouts and record timing metrics; move large jobs into async queues.

### 7. Future Research Topics
- Evaluate alternatives such as `borb`, `pdfplumber`, and `docx2pdf`, weighing performance versus compatibility.
- Consider replacing BackgroundTasks with `Celery + Redis` or `RQ`.
- Investigate storing templates and sample data in object storage (S3/MinIO) to support multi-node deployments.


