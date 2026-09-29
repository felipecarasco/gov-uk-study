.DEFAULT_GOAL := help
.PHONY: help db-up db-down db-shell api-run api-test openapi web-install assets web-run web-test dev test lint a11y images images-run images-down

# The JDK is managed by SDKMAN, which only loads in interactive shells.
# Without this, `make api-test` fails with "java: command not found" when run
# from a script, an IDE or a git hook.
SDKMAN_JAVA := $(HOME)/.sdkman/candidates/java/current
ifneq ($(wildcard $(SDKMAN_JAVA)/bin/java),)
export JAVA_HOME := $(SDKMAN_JAVA)
export PATH := $(SDKMAN_JAVA)/bin:$(PATH)
endif

help: ## List the available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

db-up: ## Start PostgreSQL and wait until it is healthy
	docker compose up -d --wait postgres

db-down: ## Stop PostgreSQL (keeps the volume)
	docker compose down

db-shell: ## Open psql on the database
	docker compose exec postgres psql -U land_registry -d land_registry

api-run: db-up ## Run the Spring Boot API on :8080
	cd api && ./mvnw spring-boot:run

api-test: ## Run the API tests (unit + integration in containers)
	cd api && ./mvnw verify

openapi: ## Rewrite api/openapi.json from the running API
	@echo "Needs the API running (make api-run) in another terminal."
	curl -sf localhost:8080/v3/api-docs | python3 -m json.tool > api/openapi.json
	@echo "api/openapi.json updated."

web-install: ## Install the Python dependencies
	cd web && env -u VIRTUAL_ENV uv sync

assets: ## Fetch the GOV.UK Frontend assets from npm
	cd web && npm install --no-audit --no-fund
	rm -rf web/app/static/govuk
	mkdir -p web/app/static/govuk
	cp -r web/node_modules/govuk-frontend/dist/govuk/assets web/app/static/govuk/assets
	cp web/node_modules/govuk-frontend/dist/govuk/govuk-frontend.min.css web/app/static/govuk/
	cp web/node_modules/govuk-frontend/dist/govuk/govuk-frontend.min.js  web/app/static/govuk/

web-run: ## Run the Flask front end on :5000
	cd web && env -u VIRTUAL_ENV uv run flask --app app:create_app run --debug --port 5000

web-test: ## Run the front-end tests
	cd web && env -u VIRTUAL_ENV uv run pytest

dev: db-up assets ## Run everything: database, API and front end (Ctrl+C stops both)
	@./scripts/dev.sh

test: ## Run both test suites
	cd api && ./mvnw verify
	cd web && env -u VIRTUAL_ENV uv run pytest

lint: ## Run the Python linter
	cd web && env -u VIRTUAL_ENV uv run ruff check .
	cd web && env -u VIRTUAL_ENV uv run ruff format --check .

a11y: ## Audit every page with axe-core and check keyboard access (needs make dev running)
	uvx --with playwright python scripts/a11y_audit.py

# --- Container images (target: OpenShift) -------------------------------------
# The images do not run tests: the pipeline tests before asking for a build.

IMAGE_TAG ?= local

images: ## Build the API and front-end images
	docker build -t land-registry-api:$(IMAGE_TAG) ./api
	docker build -t land-registry-web:$(IMAGE_TAG) ./web

# --user mimics the arbitrary UID OpenShift injects: a container that only works
# with the Dockerfile's UID fails here instead of on the cluster.
images-run: images db-up ## Run both containers with an arbitrary UID, as on OpenShift
	docker run -d --name lr-api --network gov-study_default --user 1000670000:0 \
	  -e SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/land_registry \
	  -p 18080:8080 land-registry-api:$(IMAGE_TAG)
	docker run -d --name lr-web --network gov-study_default --user 1000670000:0 \
	  -e API_BASE_URL=http://lr-api:8080 -e SECRET_KEY=not-for-production \
	  -p 15000:5000 land-registry-web:$(IMAGE_TAG)
	@echo "Front end at http://localhost:15000 · API at http://localhost:18080"

images-down: ## Remove the containers created by images-run
	-docker rm -f lr-api lr-web
