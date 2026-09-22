# Imagem do front-end Flask, construída para rodar no OpenShift.
# Vale o mesmo cuidado com UID arbitrário descrito em api/Dockerfile.

# ---------- assets do GOV.UK ----------
# O CSS/JS do GOV.UK Frontend vem do npm e é gitignorado (ver web/package.json e
# o alvo `assets` do Makefile). Sem este estágio a imagem sobe sem estilo algum.
FROM node:22-slim AS assets
WORKDIR /assets
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# ---------- dependências Python ----------
FROM python:3.12-slim AS deps
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app

# `--frozen` faz o build falhar se o uv.lock estiver defasado em relação ao
# pyproject.toml, em vez de resolver versões novas silenciosamente.
# `--no-default-groups` deixa pytest, ruff e afins fora da imagem.
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

# A página inicial é o sinal de readiness: renderiza um template do GOV.UK e não
# depende da API, então responde 200 mesmo se o back-end estiver fora — o que é
# o comportamento desejado, o pod do front-end não deve reiniciar por causa dela.
# urllib em vez de curl: evita instalar pacote só para a probe.
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:5000/', timeout=3).read()"]

# A API é alcançada pelo Service do OpenShift; localhost é só o default de dev.
ENV API_BASE_URL=http://localhost:8080

# O servidor de desenvolvimento do Flask não vai para imagem nenhuma. O gunicorn
# recebe a factory `create_app()` direto, sem precisar de um wsgi.py.
#
# Workers síncronos: cada request fica bloqueado numa chamada HTTP à API, então o
# que importa aqui é concorrência de I/O, não CPU. Dois workers com quatro
# threads cada dão 8 requests simultâneos num container pequeno.
# `--no-control-socket`: o gunicorn 26 abre um socket de controle em
# $XDG_RUNTIME_DIR/gunicorn.ctl ou, na falta dele, $HOME/.gunicorn/. Sob UID
# arbitrário o usuário não está em /etc/passwd, $HOME resolve para "/" e o
# processo sobe servindo requests mas logando "Control server error: Permission
# denied" a cada boot. Como não se administra o gunicorn por dentro do pod
# (usa-se `oc rsh`/redeploy), o socket é desligado em vez de ganhar um diretório.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
     "--workers", "2", "--threads", "4", \
     "--no-control-socket", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "app:create_app()"]
