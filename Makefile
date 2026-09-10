.DEFAULT_GOAL := help
.PHONY: help db-up db-down db-shell

help: ## Lista os alvos disponíveis
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

db-up: ## Sobe o PostgreSQL e espera ficar saudável
	docker compose up -d --wait postgres

db-down: ## Derruba o PostgreSQL (mantém o volume)
	docker compose down

db-shell: ## Abre um psql no banco
	docker compose exec postgres psql -U land_registry -d land_registry
