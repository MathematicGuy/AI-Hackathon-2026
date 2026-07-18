# Backend image: FastAPI health/advisor API + ingestion CLI.
# Built from the repository root as build context.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir uv

WORKDIR /app

# Dependency layer (cached until pyproject/uv.lock change).
COPY pyproject.toml uv.lock ./
COPY backend ./backend
COPY scripts ./scripts

# Install locked main dependencies into /app/.venv.
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000

# Apply migrations, then serve. Ingestion overrides this command.
CMD ["sh", "-c", "python -m backend.app.db.migrate && uvicorn backend.app.api.main:app --host 0.0.0.0 --port 8000"]
