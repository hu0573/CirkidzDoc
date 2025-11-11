# Document Template Capability Extraction Plan

## Goals
Extract the document template filling capability from docassemble and rebuild it as a decoupled web application:
- **Frontend:** React + TypeScript + Tailwind (already initialized) providing template selection, field entry, output format selection, and result downloads.
- **Backend:** Python stack (FastAPI recommended) delivering template parsing, data filling, and format conversion APIs that operate independently of docassemble.
- **Formats:** Support template types such as `.docx` and `.pdf`, outputting the formats currently provided by docassemble (DOCX, PDF, HTML, RTF, TeX, Markdown, etc.).

## Phase Task Board
- [x] **Phase 1: Documentation & Planning**
  - [x] Summarize docassemble’s template/format capabilities and produce a dependency matrix draft.
  - [x] Define the template metadata schema, field type mapping, and validation rules.
- [x] Write `docs/document-template-requirements.en.md` (Requirements Specification).
- [x] Write `docs/docassemble-capabilities-research.en.md` (Technical Research Report) covering dependency installation, version alignment, and debugging.
- [x] Produce `docs/system-architecture-blueprint.en.md` with the overall architecture and key decisions.
- [x] **Phase 2: Toolkit Build & Environment Alignment**
  - [x] Draft the docassemble-aligned container build plan and component inventory.
  - [x] Implement a multi-stage Dockerfile aligned with ReferenceProjects/docassemble and verify baseline versions.
  - [x] Configure `docker-compose.yml` / Dev Container and integrate scripts such as `make render-sample` and `make healthcheck`.
- [x] Document the process in `docs/toolkit-usage-and-debugging.en.md`.
  - [x] Run `make healthcheck` / `make render-sample` locally (2025-11-11) to validate the toolkit and rendering workflow.
- [x] **Phase 3: Backend Infrastructure**
  - [x] Scaffold a FastAPI project with Pydantic models and routers.
  - [x] Establish the template directory layout, caching, and sample metadata.
  - [x] Manage Python dependencies with `uv`, generate the lock file, and define the update process.
  - [x] Configure Makefile/justfile targets and reuse the toolkit health-check script.
- [x] Set up configuration/logging baselines and complete `docs/backend-environment-setup.en.md`.
- [x] **Phase 4: Backend Rendering & Conversion**
  - [x] Implement DOCX rendering (including images, conditional logic).
  - [x] Implement PDF form filling with flattening, PDF/A, and password options.
  - [x] Build `ConversionPipeline` that chains docx → pdf → {html, rtf, tex, md}.
  - [x] Integrate health checks/degradation strategies for external tools.
- [x] Create focused unit tests and record them in `docs/backend-render-testing-guide.en.md`.
- [x] **Phase 5: Backend Task Orchestration & APIs**
  - [x] Design and migrate database tables (`templates`, `tasks`, `task_results`, etc.).
  - [x] Implement task creation, progress updates, and status APIs using the BackgroundTasks abstraction.
  - [x] Finish result archiving, expiration cleanup, and download token management.
  - [x] Provide format/option queries and template detail APIs.
- [x] Author `docs/backend-api-user-guide.en.md`.
- [x] **Phase 6: Frontend Implementation**
  - [x] Wrap Axios with a shared client for error handling, downloads, and configuration.
  - [x] Build template list/preview pages backed by the template APIs.
  - [x] Implement metadata-driven dynamic forms with validation.
  - [x] Implement output format and advanced option components tied to task submission.
  - [x] Build task status, download management, and retry UX.
- [x] Document reuse guidelines in `docs/frontend-components-and-state-guide.en.md`.
- [ ] **Phase 7: End-to-End Verification & Delivery**
- [ ] Run frontend/backend unit, integration, and E2E tests; produce `docs/test-report.md`.
  - [ ] Complete K6/JMeter performance tests with monitoring and publish a performance baseline report.
  - [ ] Validate compatibility and large-file scenarios, logging issues and resolutions.
  - [ ] Finalize deployment assets (Docker Compose, Helm) and write `deploy/README.md`.
  - [ ] Conduct internal acceptance and knowledge sharing, producing a delivery retrospective.

## docassemble Capabilities Snapshot
- Template types: `docx_template_file`, `pdf_template_file`, `rtf_template_file`, etc.
- Data filling:
  - DOCX: `docxtpl` renders Jinja2 templates with images, sub-templates, and conditionals.
  - PDF: Fills AcroForm text, checkboxes, and signature images with configurable export values.
- Output formats:
  - DOCX templates: `docx`, `pdf`, `rtf`, `tex`, `html`, `md`, etc.
  - PDF templates: `pdf` with optional flattening, PDF/A, and encryption.
  - Attachments: Any static file.
- Advanced features: PDF/A, flattening, password protection, DOCX reference updates, hyperlink styling, sub-template merging, image embedding, etc.

## Scope
### Frontend (React + TS + Tailwind)
- Template selection with built-in DOCX samples (name, preview, description).
- Dynamic forms based on metadata (text, number, boolean, date, file uploads, etc.).
- Optional JSON view/edit mode.
- Output format selection (DOCX, PDF, HTML, RTF, TeX, Markdown, etc.) with multi-select and advanced options (PDF/A, flattening, encryption).
- Generation & downloads: trigger tasks, display progress, enable single or bundled downloads, handle errors and retries.
- Authentication: Not required during MVP; assume trusted network.

### Backend (Python / FastAPI)
- Accept template identifiers and field payloads, orchestrating DOCX/PDF pipelines.
- Support conversion chain covering docassemble’s output formats.
- Manage task status, temp files, logging, and download endpoints.
- Handle advanced options (PDF/A, flattening, passwords, attachments).

## Technical Approach
### Frontend
- Components: template gallery, field form, output selector, task status, download list, settings, alerts.
- State: React Query + local state initially; evaluate Zustand later. Separate form state from task state.
- API client: Axios wrapper for error interception, uploads, and downloads.
- UI: Tailwind + Headless UI for reusable components; support theming, dark mode, responsive layouts.
- Extensibility: Hooks for i18n/a11y, centralized copy, keyboard accessibility.

### Backend
- Framework: FastAPI + Pydantic v2 on Uvicorn/Gunicorn; modular routers with OpenAPI docs.
- Dependencies: Align with docassemble (`docxtpl`, `python-docx`, `docxcompose`, `pikepdf`, `xfdfgen`, `pdftk`, `qpdf`, ImageMagick, Pandoc, LibreOffice, `unoconv`, etc.).
- Template management: `templates/<template_id>/` structure with caching (LRU/Redis).
- Conversion pipeline: `ConversionPipeline` orchestrates docx → pdf → {html, rtf, tex, md}, combining Pandoc/LibreOffice/ImageMagick.
- Dependency monitoring: Startup and scheduled checks for tools (Pandoc/LibreOffice); degrade gracefully by returning raw DOCX.
- File handling: `tempfile` for task-level directories, archive to `results/<task_id>/`, clean up expired data, optionally integrate object storage.
- Async tasks: MVP uses BackgroundTasks; plan for Celery + Redis with a pluggable executor.
- Observability: Structured logging (loguru/structlog) capturing template ID, formats, durations, errors; expose Prometheus metrics.

## Architecture
- **Overall:** SPA served via static hosting (Vercel/S3 + CloudFront), FastAPI backend over HTTPS, optional API gateway/object storage.
- **Modules:** Frontend UI, API layer, rendering engine, conversion service, storage, task orchestration.
- **Deployment:** Docker Compose locally; automated CI/CD in test; Kubernetes/container service in production with scaling, health checks, and centralized logging.

## Template & Field Modeling
- `templates/<id>/metadata.json` example mirrors docassemble (fields, options, outputs).  
- Field types: `string`, `number`, `boolean`, `date`, `enum`, `file`, `textarea/richtext`; support regex, bounds, length constraints.  
- Advanced config: field grouping, conditional visibility, default expressions, future JSON Schema/DSL integration.

## Core Workflow
1. User selects a template and retrieves metadata, preview, and supported formats.
2. Frontend renders the form with advanced options.
3. Upon submission:
   - Frontend validates and posts `RenderRequest`.
   - Backend validates, creates a task, persists, and returns `task_id`.
4. Execution:
   - Rendering engine loads and fills DOCX/PDF templates.
   - Conversion service generates requested outputs.
   - Result metadata stored in `task_results`.
5. Frontend polls `GET /api/templates/{task_id}` or subscribes via SSE/WebSocket.
6. Users download individual files or bunded archives.

### Error Handling & Retry
- Validation failures → HTTP 422 with field-level errors.
- Rendering/conversion failures → log, monitor, respond 500 with `error_code`, support backend retry once.
- External command timeouts → 120s limit with kill/retry guidance.
- Archive failures → roll back task state and alert operators.

## Data Model & Contracts
- Tables: `templates`, `template_files`, `tasks`, `task_results`, `task_logs`.
- Pydantic models: `TemplateSummary`, `FieldSchema`, `RenderRequest`, `RenderResponse`, `TaskStatus`, `ResultFile`, etc.
- APIs: `GET /api/templates`, `GET /api/templates/{id}`, `POST /api/templates/render`, `GET /api/templates/{task_id}`, `GET /api/templates/{task_id}/files/{format}`, `GET /api/formats`, optional `POST /api/templates/validate`.
- Files stored under `results/<task_id>/`, assigned download tokens; expiration defaults to seven days.

## Environment & Tooling
- **Development:** Python 3.11, Node.js 20, pnpm; Dev Container or Makefile/justfile shortcuts.
- **Python Dependencies:** Managed via `uv` (`uv sync`, `uv lock --upgrade`).
- **Container Strategy:** Base Ubuntu image aligned with docassemble; multi-stage Dockerfile; `docker-compose.yml` orchestrates services; startup scripts probe tool versions and expose `/health/deps`.
- **Local Debugging:** Scripts (`make render-sample`, `make healthcheck`) verify Pandoc/LibreOffice/ImageMagick; documentation references `docs/docassemble-capabilities-research.en.md`.
- **CI/CD:** GitHub Actions/GitLab CI for lint/test/build/integration/image push.
- **Quality Gates:** Frontend (ESLint, Prettier, Stylelint, Vitest, RTL); Backend (Ruff, Mypy, Pytest, Coverage, Bandit); Dependabot for updates.

## Process & Collaboration
- Track work via Jira/Linear; weekly syncs on progress/risks.
- Maintain Architecture Decision Records (ADRs).
- Template release flow: submit package (template, metadata, samples, preview), run automated checks, merge via code review.

## Testing & Acceptance
- **Testing Layers:** unit (renderers, converters, validation), integration (real templates & API outputs), E2E (user flows with error handling), regression (snapshot comparison).
- **Acceptance Criteria:** ≥3 DOCX + 1 PDF pass end-to-end; DOCX/PDF/HTML/Markdown outputs accurate; failure responses include codes and trace IDs; deliver deployment scripts, user manual, and template guidelines.

## Risks & Mitigation
- Dependency/deployment complexity → containerization and scripted setup.
- Template compatibility → validation tools and sample library regression tests.
+- Performance bottlenecks → concurrency control, rate limiting, caching; split rendering and conversion with throughput/latency baselines.
- Resource constraints → enforce CPU/memory quotas and timeouts; monitor external commands.
- Frontend field configuration → automated validation plus manual review.

## Follow-up Work
- Support template uploads/versioning and online previews.
- Build visual mapping tools for business users.
- Integrate object storage (S3/OSS/MinIO) and message queues for scalability.
- Plan multilingual UI and localized outputs.
- Continue evaluating alternative libraries (`borb`, `pdfplumber`, `docx2pdf`, etc.) for performance and dependency optimizations.


