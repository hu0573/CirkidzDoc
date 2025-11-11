UV := uv
APP_MODULE := app.main:app
HEALTHCHECK_SCRIPT := ../infra/scripts/healthcheck.sh

.PHONY: sync run dev test healthcheck refresh-templates

sync:
	$(UV) sync

run: sync
	$(UV) run uvicorn $(APP_MODULE) --host 0.0.0.0 --port 8000

dev: sync
	$(UV) run uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

test:
	$(UV) run pytest

healthcheck:
	bash $(HEALTHCHECK_SCRIPT)

refresh-templates:
	$(UV) run python -c "from app.services.templates import template_repository; template_repository.refresh()"

