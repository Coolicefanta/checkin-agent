.PHONY: dev test lint

dev:
	uvicorn services.agent.main:app --reload

test:
	pytest

lint:
	ruff check .
	ruff format --check .

install:
	pip install -e .
