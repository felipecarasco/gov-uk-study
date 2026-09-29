# Search the Land Register

A study replica of a public land register lookup service: search a property by
title number, see the title summary, and order an official copy of the register.

All data is fictitious. No property, person or lender shown is real.

## Stack

| Part | Technology |
|---|---|
| API | Java 25, Spring Boot 4.1.1, `JdbcClient` with raw SQL, Flyway |
| Front end | Python 3.12, Flask 3.1, server-side rendering, GOV.UK Design System |
| Database | PostgreSQL 18 |
| Contract | OpenAPI 3, errors as RFC 9457 Problem Details |
| Tests | JUnit 6 + Testcontainers, pytest + respx |
| Delivery | Docker images for OpenShift, CI for GitHub Actions, GitLab CI and Jenkins |

The browser talks only to Flask; Flask talks only to the API over REST; only the
API talks to PostgreSQL.

## Requirements

Docker, JDK 25, [`uv`](https://docs.astral.sh/uv/) and Node (only to fetch the
GOV.UK Frontend assets).

## Run

```bash
make dev
```

- Front end: <http://localhost:5000>
- API: <http://localhost:8080>, Swagger UI at `/swagger-ui/index.html`

`make help` lists every target.

## Test

```bash
make test    # API (unit + integration against a real PostgreSQL) and front end
make lint    # ruff
```

The integration tests start PostgreSQL with Testcontainers, so Docker must be
running.

`api/openapi.json` is the committed REST contract. A test fails if the API
drifts from it; after an intended change, run `make openapi` with the API
running and commit the file with the change.

## Containers

```bash
make images-run    # builds both images and runs them with an arbitrary UID
make images-down
```

The images run as a non-root, arbitrary UID in group 0, which is what OpenShift
does.

## API

| Method | Path | |
|---|---|---|
| `GET` | `/api/v1/titles/{titleNumber}` | Title summary |
| `POST` | `/api/v1/orders` | Create an order for a copy of the register |
| `GET` | `/api/v1/orders/{reference}` | Fetch an order |

## Layout

```
api/        Spring Boot API: controllers, services, JdbcClient repositories
  src/main/resources/db/migration/   Flyway migrations
  openapi.json                       committed REST contract
web/        Flask front end: blueprints, WTForms, Jinja templates
scripts/    development helpers
```
