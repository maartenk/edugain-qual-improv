.PHONY: dev-env dev-env-coverage dev-env-parallel dev-env-tests dev-env-fresh clean-env clean-artifacts clean-artifacts-all test coverage lint

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

clean-artifacts:
	./scripts/clean-artifacts.sh

clean-artifacts-all:
	./scripts/clean-artifacts.sh --reports

test:
	. .venv/bin/activate && pytest

coverage:
	mkdir -p reports
	. .venv/bin/activate && pytest --cov=src/edugain_analysis --cov-report=term --cov-report=xml:reports/coverage.xml --cov-report=html:reports/htmlcov

lint:
	. .venv/bin/activate && scripts/lint.sh
