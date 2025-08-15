.PHONY: install dev-api dev-web test fmt

install:
	uv sync
	cd web && bun install
	echo 'Install complete'

dev-api:
	uv run uvicorn api.main:create_app --factory --reload --reload-dir api

dev-web:
	cd web && bun run dev

test:
	uv run pytest

fmt:
	uv run ruff check . --fix
	uv run black .
