.DEFAULT_GOAL := help
.PHONY: help db-up db-down db-shell api-run api-test openapi web-install assets web-run web-test

# O JDK é gerenciado pelo SDKMAN, que só é carregado em shells interativos.
# Sem isto, `make api-test` falha com "java: command not found" quando rodado
# de um script, de uma IDE ou de um hook de git.
SDKMAN_JAVA := $(HOME)/.sdkman/candidates/java/current
ifneq ($(wildcard $(SDKMAN_JAVA)/bin/java),)
export JAVA_HOME := $(SDKMAN_JAVA)
export PATH := $(SDKMAN_JAVA)/bin:$(PATH)
endif

help: ## Lista os alvos disponíveis
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

db-up: ## Sobe o PostgreSQL e espera ficar saudável
	docker compose up -d --wait postgres

db-down: ## Derruba o PostgreSQL (mantém o volume)
	docker compose down

db-shell: ## Abre um psql no banco
	docker compose exec postgres psql -U land_registry -d land_registry

api-run: db-up ## Sobe a API Spring Boot em :8080
	cd api && ./mvnw spring-boot:run

api-test: ## Roda os testes da API (unitários + integração em container)
	cd api && ./mvnw verify

openapi: ## Regrava docs/openapi.json a partir da API em execução
	@mkdir -p docs
	@echo "Requer a API rodando (make api-run) em outro terminal."
	curl -sf localhost:8080/v3/api-docs | python3 -m json.tool > docs/openapi.json
	@echo "docs/openapi.json atualizado."

web-install: ## Instala as dependências Python
	cd web && env -u VIRTUAL_ENV uv sync

assets: ## Baixa os assets do GOV.UK Frontend do npm
	cd web && npm install --no-audit --no-fund
	rm -rf web/app/static/govuk
	mkdir -p web/app/static/govuk
	cp -r web/node_modules/govuk-frontend/dist/govuk/assets web/app/static/govuk/assets
	cp web/node_modules/govuk-frontend/dist/govuk/govuk-frontend.min.css web/app/static/govuk/
	cp web/node_modules/govuk-frontend/dist/govuk/govuk-frontend.min.js  web/app/static/govuk/

web-run: ## Sobe o front-end Flask em :5000
	cd web && env -u VIRTUAL_ENV uv run flask --app app:create_app run --debug --port 5000

web-test: ## Roda os testes do front-end
	cd web && env -u VIRTUAL_ENV uv run pytest
