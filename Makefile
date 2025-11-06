.DEFAULT_GOAL := help

VENV ?= .venv
PYTHON ?= python3
PIP := $(VENV)/bin/pip
PYTHON_BIN := $(VENV)/bin/python
EXTRAS ?= dev

HELP_COL := 24
comma := ,

define PRINT_HELP
	@printf "  %-$(HELP_COL)s %s\n" "$(1)" "$(2)"
endef

.PHONY: help env pip-upgrade deps install extras shell enter leave deps-shell test coverage lint fmt dev-env dev-env-coverage dev-env-parallel dev-env-tests dev-env-fresh clean clean-pycache clean-env clean-artifacts clean-cache clean-artifacts-all clean-all purge

help:
	@echo "End-user targets:"
	$(call PRINT_HELP,make help,show this message)
	$(call PRINT_HELP,make install,create/update .venv and install extras ($(EXTRAS)))
	$(call PRINT_HELP,make shell,activate the virtualenv in a subshell)
	$(call PRINT_HELP,make test,run pytest)
	$(call PRINT_HELP,make coverage,run pytest with coverage reports)
	$(call PRINT_HELP,make lint,run ruff checks)
	$(call PRINT_HELP,make fmt,format the codebase with ruff)
	@echo ""
	@echo "Development targets:"
	$(call PRINT_HELP,make deps,install base requirements only)
	$(call PRINT_HELP,make deps-shell,install requirements then drop into the shell)
	$(call PRINT_HELP,make enter,alias for make shell)
	$(call PRINT_HELP,make leave,print instructions for leaving the shell)
	$(call PRINT_HELP,make dev-env,run scripts/dev/dev-env.sh)
	$(call PRINT_HELP,make dev-env-tests,run dev-env with --with-tests)
	$(call PRINT_HELP,make dev-env-coverage,run dev-env with --with-coverage)
	$(call PRINT_HELP,make dev-env-parallel,run dev-env with --with-parallel)
	$(call PRINT_HELP,make dev-env-fresh,run dev-env with --fresh)
	@echo ""
	@echo "Maintenance targets:"
	$(call PRINT_HELP,make clean,remove build artefacts (retains venv))
	$(call PRINT_HELP,make clean-pycache,delete Python bytecode caches)
	$(call PRINT_HELP,make clean-artifacts,drop dev/test/coverage artifacts)
	$(call PRINT_HELP,make clean-cache,clear cached metadata)
	$(call PRINT_HELP,make clean-env,delete the virtualenv ($(VENV)))
	$(call PRINT_HELP,make clean-all,remove caches$(comma) reports$(comma) and the virtualenv)
	$(call PRINT_HELP,make purge,alias for clean-all)
	@echo ""
	@echo "Variables:"
	$(call PRINT_HELP,EXTRAS=dev$(comma)tests,choose extras installed by make install)
	$(call PRINT_HELP,PYTHON=python3.11,override interpreter used to create the venv)

$(PYTHON_BIN):
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment ($(VENV)) with $(PYTHON)"; \
		"$(PYTHON)" -m venv "$(VENV)"; \
	fi

pip-upgrade: $(PYTHON_BIN)
	@echo "Upgrading pip in $(VENV)..."
	@$(PYTHON_BIN) -m pip install --upgrade pip

deps: pip-upgrade requirements.txt
	@echo "Installing base requirements..."
	@$(PIP) install -r requirements.txt

install: deps
	@echo "Installing project extras: $(EXTRAS)"
	@$(PIP) install -e ".[${EXTRAS}]"

extras: install

env: deps

shell: $(PYTHON_BIN)
	@echo "Entering virtual environment; type 'exit' or press Ctrl-D to leave."
	@. "$(VENV)"/bin/activate && exec $${SHELL:-/bin/sh} -i

enter: shell

leave:
	@echo "Already in an activated shell? Type 'exit' or press Ctrl-D to leave the virtualenv."

deps-shell: install shell

test: install
	@$(PYTHON_BIN) -m pytest

coverage: install
	@mkdir -p reports
	@$(PYTHON_BIN) -m pytest --cov=src/edugain_analysis --cov-report=term --cov-report=xml:reports/coverage.xml --cov-report=html:reports/htmlcov

lint: install
	@$(VENV)/bin/bash scripts/lint.sh

fmt: install
	@$(PYTHON_BIN) -m ruff format src/ tests/

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

clean:
	@$(MAKE) clean-pycache
	@rm -rf .pytest_cache .ruff_cache reports/htmlcov *.egg-info

clean-pycache:
	@find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.py[co]" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true

clean-env:
	@rm -rf "$(VENV)"

clean-artifacts:
	./scripts/clean-artifacts.sh

clean-artifacts-all:
	./scripts/clean-artifacts.sh --reports

clean-all: clean clean-env clean-artifacts-all

purge: clean-all
