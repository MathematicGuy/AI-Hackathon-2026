FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

ARG DMX_INSTALL_EXTRAS=postgres
ARG APP_UID=1000
ARG APP_GID=1000

COPY pyproject.toml README.md ./
COPY dmx_crawler ./dmx_crawler
COPY config ./config
COPY migrations ./migrations
COPY sql ./sql
COPY docs ./docs
COPY scripts ./scripts
COPY data ./data

RUN python -m pip install --upgrade pip \
    && if [ -n "$DMX_INSTALL_EXTRAS" ]; then \
         python -m pip install ".[${DMX_INSTALL_EXTRAS}]"; \
       else \
         python -m pip install .; \
       fi \
    && addgroup --gid "$APP_GID" crawler \
    && adduser --disabled-password --gecos "" --uid "$APP_UID" --gid "$APP_GID" --home /app crawler \
    && mkdir -p /app/data \
    && chown -R crawler:crawler /app

USER crawler

ENTRYPOINT ["dmx"]
CMD ["--help"]
