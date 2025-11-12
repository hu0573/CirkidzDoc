## CirkidzDoc

CirkidzDoc is a document authoring and conversion toolkit designed for the Cirkidz team. It combines a FastAPI backend, a React/Vite frontend, and a Docker-based rendering toolkit to transform rich templates (DOCX, PDF, HTML, Markdown) into finalized deliverables.

### Key Capabilities
- **Templated publishing pipeline** — upload, inspect, and populate rich templates with structured data.
- **Multi-format rendering** — leverage LibreOffice, Pandoc, Ghostscript, and other tools packaged inside the rendering toolkit container.
- **Task orchestration** — queue, monitor, and retrieve conversion jobs through a RESTful API.
- **Developer-friendly tooling** — end-to-end launcher (`run_project.py`), automated dependency checks, and extensive project documentation.

### Repository Structure
- `BackEnd/` — FastAPI service, SQLAlchemy models, conversion pipeline, and automated tests.
- `FrontEnd/` — React + TypeScript admin console built with Vite.
- `infra/` — Docker compose definition and helper scripts for the rendering toolkit container.
- `docs/` — Architecture notes, setup guides, API usage instructions, and research materials.
- `run_project.py` — Unified launcher for local development (backend + frontend + toolkit).
- `ReferenceProjects/` — Historical references (e.g., Docassemble) for comparison and migration work.

### Prerequisites
| Requirement | Notes |
|-------------|-------|
| Python 3.11+ | Recommended to install via `pyenv`, `asdf`, or system package manager. |
| [uv](https://github.com/astral-sh/uv) | Used for Python dependency management and task execution. |
| Node.js 18+ & npm | Frontend tooling; `run_project.py` verifies and installs dependencies automatically. |
| Docker Engine & docker compose | Required for the rendering toolkit container. |

> Install `uv` if missing: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Quick Start
```bash
cd /Volumes/DataBank/github/CirkidzDoc
python run_project.py
```

The launcher will:
1. Verify Docker availability and ensure the `cirkidzdoc/toolkit:dev` image is present (building if necessary).
2. Check for Node.js dependencies; run `npm install` and install `tailwindcss`/`@tailwindcss/vite` if missing.
3. Start the FastAPI backend (via `uv run uvicorn`) and the Vite development server.

Backend API: `http://127.0.0.1:8000` (health check at `/health`)  
Frontend UI: `http://127.0.0.1:5173`

Stop the stack with `Ctrl+C`; the launcher gracefully shuts down all processes.

#### Running on the remote notebook server

When deploying on the managed notebook (the one behind the FRP tunnel), run the launcher from a shell on that machine using the following sequence:

```bash
newgrp docker                     # pick up docker group membership if you just logged in
source ~/.local/bin/env           # add uv/node from ~/.local/bin to PATH
export VITE_API_BASE_URL="http://141.148.141.184:9005/api"
python run_project.py --frontend-host 0.0.0.0
```

- The backend listens on `0.0.0.0:8000` and the frontend on `0.0.0.0:5173`.
- FRP maps these services to the public endpoints `http://141.148.141.184:9005/` (API) and `http://141.148.141.184:9004/` (Vite dev server).
- To detach the processes, you can instead run the helper script `~/start_cirkidz.sh`, which wraps the steps above and redirects logs to `~/Code/run_project.log`.

### Using the Frontend Console
1. Open `http://127.0.0.1:5173` in your browser once `python run_project.py` reports that both services are running.
2. **Template Library** — the left panel lists available templates; click one to view details.
3. **Metadata & Fields** — the detail panel shows template description, supported formats, and required data fields.
4. **Upload New Template** — drag-and-drop a `.docx` template and fill in the metadata form; the backend stores it under `BackEnd/templates/`.
5. **Create a Task** — choose a template, select desired output formats (HTML, PDF, DOCX, Markdown), provide field values, then submit.
6. **Track Progress** — the Task Center displays running and completed jobs; click a finished task to download generated files.

Tips for non-technical users:
- Required fields appear with an asterisk; the console prevents submission until all required data is provided.
- Validation errors show inline; you can edit and resubmit without leaving the page.
- The browser auto-refreshes task status every few seconds; no manual refresh needed.

### Manual Development Setup

**Backend**
```bash
cd /Volumes/DataBank/github/CirkidzDoc/BackEnd
uv sync
uv run fastapi dev app/main.py --reload
```
- Default database: SQLite file at `BackEnd/data/backend.db`.
- Templates reside under `BackEnd/templates/`; adjust with `BACKEND_TEMPLATE_ROOT`.
- For automated tests: `uv run pytest`.

**Frontend**
```bash
cd /Volumes/DataBank/github/CirkidzDoc/FrontEnd
npm install
npm run dev
```
- Builds: `npm run build`
- Preview: `npm run preview`

### Configuration Notes
- Backend environment variables use the `BACKEND_` prefix (e.g., `BACKEND_LOG_LEVEL`, `BACKEND_DATABASE_URL`).
- Rendering toolkit paths are configurable; see `BackEnd/app/core/config.py` for available options.
- Docker compose file (toolkit) lives at `infra/docker-compose.yml`; adjust render binaries or volumes there.

### Documentation & Further Reading
- `docs/system-architecture-blueprint.en.md` — high-level system architecture.
- `docs/backend-api-user-guide.en.md` — REST endpoints and payload formats.
- `docs/frontend-components-and-state-guide.en.md` — UI architecture.
- `docs/template-dependencies-and-metadata.en.md` — template structure and metadata schema.

### Creating and Maintaining Templates
- Author templates in Microsoft Word (or LibreOffice) and save as `.docx`.
- Use double curly braces (`{{ placeholder_name }}`) as markers for dynamic content, e.g., `Dear {{ student_name }}` or `{{ event_date }}`.
- Placeholders should match the field names you enter in the frontend metadata form; they are case-sensitive and support underscores (`{{guardian_email}}`, `{{class_level}}`).
- To include conditional content, create sections that can be blank (for optional data); the pipeline replaces missing fields with empty strings.
- When uploading, provide:
  - **Template Name** — shown in the frontend library.
  - **Description** — helps colleagues understand the use case.
  - **Metadata** — define human-friendly labels, default values, and data types for each placeholder.
- After uploading, download a sample output from the Task Center to confirm formatting.
- To update a template, upload a new version with the same name; the backend keeps revision history in `BackEnd/results/`.

### Contributing
1. Fork the repository and create a feature branch.
2. Keep backend code formatted via `uv run ruff check --fix` (if enabled) and frontend linting with `npm run lint` (when configured).
3. Add or update tests under `BackEnd/tests`.
4. Open a pull request describing changes, testing steps, and any follow-up tasks.

### Troubleshooting
- **Docker not found** — ensure `docker` CLI is on your `PATH` and the daemon is running.
- **npm missing** — install Node.js; `run_project.py` will abort if `npm` is unavailable.
- **Toolkit render errors** — inspect container logs (`docker compose -f infra/docker-compose.yml logs toolkit`) and confirm required binaries exist.
- **Permission issues on macOS/Linux** — ensure the repository resides on a case-sensitive volume and you have read/write access to `infra/tmp` and `infra/output`.

Happy building!

