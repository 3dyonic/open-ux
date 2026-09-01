FROM python:3.12-slim

WORKDIR /app

COPY packages/mcp /app/packages/mcp
COPY catalog /app/catalog

RUN pip install --no-cache-dir /app/packages/mcp

ENV OPEN_UX_MODE=hosted
ENV OPEN_UX_HOSTED=1
ENV OPEN_UX_CATALOG=/app/catalog
ENV OPEN_UX_SCHEMA=/app/catalog/schema.json
ENV OPEN_UX_DATA_DIR=/data
ENV OPEN_UX_DATABASE=/data/open-ux.sqlite
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "open_ux", "http"]
