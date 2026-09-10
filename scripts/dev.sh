#!/usr/bin/env bash
#
# Sobe a API e o front-end juntos. Ctrl+C encerra os dois.
#
# Nota sobre sinais: num terminal, o Ctrl+C vai para o grupo de processos em
# primeiro plano e o trap abaixo trata. Se você iniciar este script em segundo
# plano a partir de um shell não-interativo, o SIGINT é IGNORADO (comportamento
# POSIX para jobs de fundo) — nesse caso use SIGTERM.
set -uo pipefail

# Job control: faz o bash colocar cada job de segundo plano no seu PRÓPRIO grupo
# de processos, o que torna `kill -- -PID` capaz de derrubar a árvore inteira.
# Sem isto, matar o ./mvnw deixa a JVM viva e a porta 8080 presa — o wrapper
# lança o Java como processo separado.
set -m

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDS=()

encerrar() {
  trap - INT TERM EXIT
  echo
  echo "Encerrando..."
  for pid in "${PIDS[@]:-}"; do
    kill -TERM -- "-$pid" 2>/dev/null || true
  done
  sleep 2
  for pid in "${PIDS[@]:-}"; do
    kill -KILL -- "-$pid" 2>/dev/null || true
  done
  exit 0
}
trap encerrar INT TERM EXIT

echo "API   -> http://localhost:8080  (swagger em /swagger-ui/index.html)"
( cd "$RAIZ/api" && exec ./mvnw -q spring-boot:run ) &
PIDS+=($!)

# Espera a API responder antes de subir o front-end, para que a primeira
# requisição não caia na página de indisponível.
for _ in $(seq 1 120); do
  curl -sf localhost:8080/actuator/health >/dev/null 2>&1 && break
  sleep 1
done

echo "Front -> http://localhost:5000"
( cd "$RAIZ/web" && exec env -u VIRTUAL_ENV uv run flask --app app:create_app run --port 5000 ) &
PIDS+=($!)

wait
