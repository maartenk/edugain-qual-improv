.PHONY: dev-env dev-env-coverage dev-env-parallel dev-env-tests dev-env-fresh clean-env test lint

dev-env:
	./scripts/dev-env.sh

dev-env-coverage:
	./scripts/dev-env.sh --with-coverage

dev-env-parallel:
	./scripts/dev-env.sh --with-parallel

dev-env-tests:
	./scripts/dev-env.sh --with-tests

dev-env-fresh:
	./scripts/dev-env.sh --fresh

dev-env-web:
	./scripts/dev-env.sh --with-web

clean-env:
	./scripts/clean-env.sh

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && scripts/lint.sh
