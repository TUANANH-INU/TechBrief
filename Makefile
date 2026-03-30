.PHONY: format lint

format:
	@isort .
	@black .
	@ruff check . --fix

lint:
	@isort --check-only .
	@black . --check
	@ruff check .

build:
	@cd hub_manager && make build && cd ..

test:
	@cd hub_manager && make test && cd ..