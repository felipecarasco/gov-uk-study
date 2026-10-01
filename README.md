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

## Run

- Front end: <http://localhost:5000>
- API: <http://localhost:8080>, Swagger UI at `/swagger-ui/index.html`

### With Docker only (Linux, macOS or Windows)

Nothing to install but Docker (Docker Desktop on Windows and macOS):

```bash
docker compose --profile app up --build
```

Stop it with `docker compose --profile app down`. The host ports can be changed
with `WEB_PORT`, `API_PORT` and `DB_PORT`, for example `WEB_PORT=5050` on macOS,
where AirPlay Receiver often holds port 5000 (in PowerShell:
`$env:WEB_PORT = "5050"`).

### For development (Linux, macOS or WSL2)

Needs Docker, `make`, JDK 25, [`uv`](https://docs.astral.sh/uv/) and Node (only
to fetch the GOV.UK Frontend assets). The JDK is expected from
[SDKMAN](https://sdkman.io/), which is where the `Makefile` looks for it; the
version is pinned in `.sdkmanrc`:

```bash
sdk install java 25.0.4-tem    # answer Y to make it the default
```

Then:

```bash
make dev
```

`make help` lists every target. The Docker-only way and `make dev` use the same
ports: stop one before starting the other.

### On Windows

For development, use WSL2: the `Makefile` and `scripts/dev.sh` are bash. Clone
the repository inside the WSL file system (for example `~/code`), not under
`/mnt/c`, where builds are much slower, and turn on Docker Desktop's WSL
integration for your distribution. Without WSL, use the Docker-only way above.

## Test

```bash
make test    # API (unit + integration against a real PostgreSQL) and front end
make lint    # ruff
```

`make a11y` audits every page and error state with axe-core (WCAG 2.2 AA) and
checks keyboard access. It needs the service running, either way; set
`A11Y_BASE_URL` if the front end is not on `http://localhost:5000`. On a machine
without Google Chrome (WSL, for example), install a browser for it once with
`uvx playwright install --with-deps chromium`.

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
| `GET` | `/api/v1/titles?postcode=&cursor=&limit=` | Titles in a postcode, one page at a time (keyset pagination) |
| `GET` | `/api/v1/titles/{titleNumber}` | Title summary |
| `POST` | `/api/v1/orders` | Create an order for a copy of the register |
| `GET` | `/api/v1/orders/{reference}` | Fetch an order |
| `POST` | `/api/v1/orders/{reference}/payment` | Simulated payment; paying twice changes nothing |
| `GET` | `/api/v1/orders/{reference}/document` | The copy as a PDF, once the order is paid (409 before) |

## Layout

```
api/        Spring Boot API: controllers, services, JdbcClient repositories
  src/main/resources/db/migration/   Flyway migrations
  openapi.json                       committed REST contract
web/        Flask front end: blueprints, WTForms, Jinja templates
scripts/    development helpers
```
