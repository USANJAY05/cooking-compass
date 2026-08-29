# ---------- Build stage ----------
FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

# Install dependencies
COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --no-install-project --no-dev

# Copy application
COPY app.py .
COPY src ./src
COPY ca.cer .

# Install project
RUN uv sync --frozen --no-dev


# ---------- Production stage ----------
FROM python:3.14-slim AS production

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Copy virtual environment
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY --from=builder /app/app.py /app/app.py
COPY --from=builder /app/src /app/src
COPY --from=builder /app/ca.cer /app/ca.cer

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]