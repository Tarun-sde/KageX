.PHONY: install check backend-check frontend-check up down migrate
install:
	cd backend && uv sync --locked
	cd frontend && npm ci
check: backend-check frontend-check
backend-check:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest
frontend-check:
	cd frontend && npm run lint && npm run format:check && npm run typecheck && npm test && npm run build
up:
	docker compose up --build --wait
down:
	docker compose down
migrate:
	cd backend && uv run alembic upgrade head
