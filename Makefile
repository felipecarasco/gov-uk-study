.DEFAULT_GOAL := help
.PHONY: help db-up db-down db-shell api-run api-test

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
