COMPOSE_FILE := infra/docker-compose.yml
SERVICE := toolkit

.PHONY: build up down healthcheck render-sample shell clean

build:
	docker compose -f $(COMPOSE_FILE) build $(SERVICE)

up: build
	docker compose -f $(COMPOSE_FILE) up $(SERVICE)

down:
	docker compose -f $(COMPOSE_FILE) down --remove-orphans

healthcheck: build
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE) /opt/scripts/healthcheck.sh

render-sample: build
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE) /opt/scripts/render_sample.sh

shell: build
	docker compose -f $(COMPOSE_FILE) run --rm $(SERVICE) bash

clean:
	rm -rf infra/output/* infra/tmp/*

