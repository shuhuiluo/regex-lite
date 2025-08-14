.PHONY: install dev-api dev-web test fmt

install:
pip install -e engine[dev]
pip install -e api[dev]
npm --prefix web install
echo 'Install complete'

dev-api:
UVICORN_RELOAD_DIRS=api uvicorn api.main:create_app --factory --reload

dev-web:
npm --prefix web run dev

test:
pytest engine/tests api/tests

fmt:
ruff .
black .
