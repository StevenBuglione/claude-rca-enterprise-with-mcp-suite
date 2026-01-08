.PHONY: up down fmt lint ci

up:
	docker compose up --build

down:
	docker compose down -v

# These are optional; add ruff/black if you want.
fmt:
	@echo "Add ruff/black in requirements-dev.txt and wire here."

lint:
	./scripts/ci_check.sh

ci:
	./scripts/ci_check.sh
