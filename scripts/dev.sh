#!/usr/bin/env bash
#
# Runs the API and the front end together. Ctrl+C stops both.
#
# A note on signals: in a terminal, Ctrl+C goes to the foreground process group
# and the trap below handles it. If you start this script in the background
# from a non-interactive shell, SIGINT is IGNORED (POSIX behaviour for
# background jobs); use SIGTERM in that case.
set -uo pipefail

# Job control: makes bash put each background job in its OWN process group,
# which lets `kill -- -PID` take down the whole tree. Without it, killing
# ./mvnw leaves the JVM alive and port 8080 taken, because the wrapper starts
# Java as a separate process.
set -m

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDS=()

shutdown() {
  trap - INT TERM EXIT
  echo
  echo "Shutting down..."
  for pid in "${PIDS[@]:-}"; do
    kill -TERM -- "-$pid" 2>/dev/null || true
  done
  sleep 2
  for pid in "${PIDS[@]:-}"; do
    kill -KILL -- "-$pid" 2>/dev/null || true
  done
  exit 0
}
trap shutdown INT TERM EXIT

echo "API   -> http://localhost:8080  (Swagger at /swagger-ui/index.html)"
( cd "$ROOT/api" && exec ./mvnw -q spring-boot:run ) &
PIDS+=($!)

# Wait for the API before starting the front end, so the first request does
# not land on the "service unavailable" page.
for _ in $(seq 1 120); do
  curl -sf localhost:8080/actuator/health >/dev/null 2>&1 && break
  sleep 1
done

echo "Front -> http://localhost:5000"
( cd "$ROOT/web" && exec env -u VIRTUAL_ENV uv run flask --app app:create_app run --port 5000 ) &
PIDS+=($!)

wait
