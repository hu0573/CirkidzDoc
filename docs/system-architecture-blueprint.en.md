## Document Template Filling System Architecture Blueprint

### 1. High-Level Architecture
- **Frontend:** Built with Vite + React + TypeScript + Tailwind, delivering template selection, dynamic forms, task status, and download management. React Query manages API data; forms rely on React Hook Form + Zod.
- **Backend:** FastAPI exposes REST APIs across template management, task scheduling, rendering/conversion, and file downloads, using Pydantic v2 for models.
- **Task Execution Layer:** MVP leverages FastAPI BackgroundTasks. A `TaskExecutor` abstraction prepares the system for Celery/Redis migration.
- **Rendering Engine:** Encapsulates DOCX/PDF rendering, format conversion, and file archiving with unified error handling and logging.
- **Storage:** Postgres stores template, task, and result metadata. The local filesystem keeps template files and outputs, with the option to switch to object storage later.

### 2. Module Breakdown
| Module | Responsibility | Key Implementation |
| --- | --- | --- |
| `TemplateService` | Load/cache template metadata, list/detail APIs | Read `templates/<id>/metadata.json`, cache via LRU/Redis |
| `RenderService` | Support DOCX/PDF rendering | DOCX via `docxtpl`, PDF via `xfdfgen` + `pikepdf`, with input validation |
| `ConversionPipeline` | Convert base files into target formats | LibreOffice/Pandoc/ImageMagick with configurable steps |
| `TaskService` | Manage task lifecycle, status, results | Database persistence + BackgroundTasks execution |
| `FileArchive` | Handle temp directories, result archiving, cleanup | Use `tempfile` for task dirs; scheduled cleanup of expired files |
| `HealthCheck` | Monitor dependency status | Run external command probes at startup and intervals |

Frontend components span template browsing, dynamic forms, output options, task list, download center, and settings. Shared UI utilities provide form controls, progress, modals, and notifications.

### 3. Data & Flow
1. **Template Loading:** Backend scans `templates/`, validates `metadata.json`, and builds an in-memory cache. Frontend fetches the list via `GET /api/templates`.
2. **Task Creation:** Frontend submits a `RenderRequest` (template ID, data, output formats/options). Backend validates, persists to `tasks`, and dispatches async execution.
3. **Rendering & Conversion:**
   - DOCX: `docxtpl` renders → save DOCX → LibreOffice converts to PDF → Pandoc produces HTML/Markdown/RTF/TeX.
   - PDF: Build XFDF → `pikepdf` writes fields → optional `ghostscript` flattening/PDF-A based on configuration.
4. **Archiving:** Outputs stored under `results/<task_id>/`; corresponding `task_results` records and download tokens are generated.
5. **Status & Downloads:** Frontend polls or subscribes to progress; upon completion, users download individual files or ZIP bundles.
6. **Cleanup:** Scheduled jobs identify expired records, delete files, and update statuses.

Data model highlights:
- `templates(id, name, description, version, status, updated_at, config_hash)`
- `tasks(id, template_id, status, requested_formats, options, progress, error_code, created_at, expires_at)`
- `task_results(id, task_id, format, file_path, file_size, checksum, download_token, expires_at)`
- `task_logs(id, task_id, level, message, payload, created_at)`

### 4. Operations & Deployment
- **Local Development:** `docker-compose` spins up FastAPI, frontend, database, and optional Redis with mounted templates; Makefile/justfile provide shortcuts.
- **CI/CD:** GitHub Actions run lint (Ruff, ESLint), tests (Pytest, Vitest), build/push images, and execute database migrations plus health checks during deployment.
- **Production:** Deploy on Kubernetes with HPA-driven scaling. Serve the static frontend via CDN. Backend pods mount persistent volumes for templates and outputs.

### 5. Security & Observability
- **Security:** Restrict upload types/size, issue short-lived download tokens, and record audit logs.
- **Observability:** Collect metrics (task duration, success rate, external command failures) via Prometheus; ship traces with OpenTelemetry; centralize logs (ELK or cloud services).

### 6. Evolution Path
1. Phase 1: Deliver the MVP (no auth, BackgroundTasks, filesystem storage).
2. Phase 2: Introduce Celery + Redis queues, object storage, and template upload review workflows.
3. Phase 3: Support multi-tenancy, role-based access, localized UI, and a visual template editor.


