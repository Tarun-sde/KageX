FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv sync --frozen --no-dev && useradd --create-home --uid 10001 kagex && mkdir -p /app/storage && chmod 700 /app/storage && chown -R kagex:kagex /app
USER kagex
EXPOSE 8000
CMD ["python", "-m", "app"]
