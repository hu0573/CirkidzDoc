# Backend Environment Setup Guide

This document captures local development setup, dependency management, and key configuration details for the FastAPI backend so teammates can spin up an environment that matches the containerized setup.

## 1. Prerequisites

- Python 3.11 (manage with `asdf` or `pyenv` if possible)
- [uv](https://github.com/astral-sh/uv) version 0.8.0 or later (the project uses `uv sync` to create the lock file and virtual environment)
- Docker (required if you want to reuse the health-check scripts under `infra`)

## 2. Directory Layout

```
BackEnd/
  app/                # FastAPI application code
  templates/          # Template repository organized by template ID
  pyproject.toml      # Dependency declarations
  uv.lock             # uv-generated lock file (must be committed)
  Makefile            # Convenience commands
```

Template directory example `BackEnd/templates/example_contract/`:

- `metadata.json`: Template metadata definition
- `template.docx`: Actual DOCX template (not committed; add locally)
- `preview.png`: Optional preview image for the frontend

## 3. Dependency Workflow

1. Run the following when cloning the repo or before adding dependencies:
   ```bash
   cd BackEnd
   uv sync
   ```
   This command creates the `.venv` virtual environment and generates/updates `uv.lock`.

2. Add dependencies:
   ```bash
   uv add fastapi
   ```
   Always persist dependencies in `pyproject.toml` and `uv.lock`, then commit both files together.

3. Upgrade dependencies:
   ```bash
   uv lock --upgrade fastapi
   ```

4. In CI/CD or inside containers, run:
   ```bash
   uv sync --frozen
   ```
   `--frozen` enforces installation strictly according to the lock file and prevents accidental version drift.

## 4. Environment Variables & Configuration

Configuration is managed by `Settings` in `app/core/config.py`, which reads from `.env` or environment variables prefixed with `BACKEND_`. Common entries:

- `BACKEND_ENVIRONMENT`: Environment indicator, e.g. `development`, `staging`.
- `BACKEND_LOG_LEVEL`: Log level (`INFO` by default).
- `BACKEND_TEMPLATE_ROOT`: Template root directory (defaults to `BackEnd/templates`).
- `BACKEND_TASK_EXPIRY_MINUTES`: Default task expiration in minutes.

Sample `.env`:
```
BACKEND_ENVIRONMENT=development
BACKEND_LOG_LEVEL=DEBUG
BACKEND_TEMPLATE_ROOT=/opt/app/templates
```

## 5. Logging & Health Checks

- Logging uses `loguru` to emit structured output to stdout at level `INFO` by default; tweak with `BACKEND_LOG_LEVEL`.
- `/health` returns version, environment, and timestamp details for basic monitoring.
- The `healthcheck` target in the `Makefile` delegates to `infra/scripts/healthcheck.sh` so local runs match the container behavior.

## 6. Common Commands

Execute these under `BackEnd`:
```bash
make sync              # Run uv sync
make dev               # Start FastAPI with auto-reload
make run               # Launch uvicorn in production mode
make test              # Run pytest (placeholder)
make healthcheck       # Run the container health-check script
make refresh-templates # Manually refresh the template cache
```

## 7. Next Steps

- Integrate the template rendering and conversion task pipeline.
- Introduce database configuration and migration tooling.
- Complete logging aggregation and metrics exposure.

Update this document and request review when adding configuration options or dependencies.


