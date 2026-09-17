FROM node:22-bookworm-slim AS web
WORKDIR /web
COPY packages/web/package.json packages/web/package-lock.json ./
RUN npm ci
COPY packages/web/ ./
# Vite copies public/. Overlay the package mark so the image does not depend on
# git symlinks whose targets sit outside this stage.
COPY packages/mcp/src/open_ux/static/logo-mark.svg ./public/logo-mark.svg
COPY packages/mcp/src/open_ux/static/logo-mark.svg ./public/favicon.svg
COPY packages/mcp/src/open_ux/static/icon.png ./public/icon.png
COPY catalog /catalog
ENV OPEN_UX_CATALOG=/catalog
RUN npm run build

FROM python:3.12-slim AS python-build
COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/
WORKDIR /src
RUN apt-get update \
  && apt-get install -y --no-install-recommends git \
  && rm -rf /var/lib/apt/lists/*
COPY .git /src/.git
COPY packages/mcp /src/packages/mcp
COPY catalog /src/catalog
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV UV_LINK_MODE=copy
RUN git config --global --add safe.directory /src \
  && uv sync --frozen --no-dev --no-editable --no-cache --directory packages/mcp

FROM python:3.12-slim
WORKDIR /app
COPY --from=python-build /opt/venv /opt/venv
COPY catalog /app/catalog
COPY --from=web /web/dist /app/web/dist

ENV PATH="/opt/venv/bin:$PATH"
ENV OPEN_UX_MODE=hosted
ENV OPEN_UX_HOSTED=1
ENV OPEN_UX_CATALOG=/app/catalog
ENV OPEN_UX_SCHEMA=/app/catalog/schema.json
ENV OPEN_UX_DATA_DIR=/data
ENV OPEN_UX_DATABASE=/data/open-ux.sqlite
ENV OPEN_UX_WEB_DIST=/app/web/dist
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "open_ux", "http"]
