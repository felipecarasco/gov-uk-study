# Flask front-end image, built to run on OpenShift.
# The same arbitrary-UID care described in api/Dockerfile applies here.

# ---------- GOV.UK assets ----------
# The GOV.UK Frontend CSS/JS comes from npm and is gitignored (see
# web/package.json and the `assets` Makefile target). Without this stage the
# image would serve pages with no styling at all.
FROM node:22-slim AS assets
WORKDIR /assets
COPY package.json package-lock.json ./
# --omit=dev: axe-core is only for the accessibility audit, not for the image.
RUN npm ci --omit=dev --no-audit --no-fund

# ---------- Python dependencies ----------
FROM python:3.12-slim AS deps
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app

# --frozen fails the build if uv.lock is out of date with pyproject.toml,
# instead of silently resolving new versions.
# --no-default-groups keeps pytest, ruff and friends out of the image.
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/venv
RUN uv sync --frozen --no-default-groups --no-install-project

# ---------- runtime ----------
FROM python:3.12-slim
WORKDIR /app

COPY --from=deps /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY app/ app/
COPY --from=assets /assets/node_modules/govuk-frontend/dist/govuk/assets                  app/static/govuk/assets
COPY --from=assets /assets/node_modules/govuk-frontend/dist/govuk/govuk-frontend.min.css  app/static/govuk/
COPY --from=assets /assets/node_modules/govuk-frontend/dist/govuk/govuk-frontend.min.js   app/static/govuk/

RUN chgrp -R 0 /app && chmod -R g=u /app

USER 1001

EXPOSE 5000

# The start page is the readiness signal: it renders a GOV.UK template and does
# not depend on the API, so it answers 200 even when the back end is down. That
# is intended: the front-end pod should not restart because of the API.
# urllib rather than curl: no package installed just for the probe.
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:5000/', timeout=3).read()"]

# The API is reached through the OpenShift Service; localhost is only the dev default.
ENV API_BASE_URL=http://localhost:8080

# The Flask development server never goes into an image. gunicorn takes the
# create_app() factory directly, with no wsgi.py.
#
# Sync workers with threads: each request blocks on an HTTP call to the API, so
# what matters is I/O concurrency, not CPU. Two workers with four threads each
# give 8 concurrent requests in a small container.
#
# --no-control-socket: gunicorn 26 opens a control socket in
# $XDG_RUNTIME_DIR/gunicorn.ctl or, failing that, $HOME/.gunicorn/. Under an
# arbitrary UID the user is not in /etc/passwd, $HOME resolves to "/", and the
# process serves requests but logs "Control server error: Permission denied" on
# every boot. Nobody manages gunicorn from inside the pod (you use `oc rsh` or a
# redeploy), so the socket is turned off rather than given a directory.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
     "--workers", "2", "--threads", "4", \
     "--no-control-socket", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "app:create_app()"]
