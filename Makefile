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

.PHONY: help env pip-upgrade deps install extras shell shell-pdf enter leave deps-shell test coverage lint fmt dev-env dev-env-coverage dev-env-parallel dev-env-tests dev-env-fresh clean clean-pycache clean-env clean-artifacts clean-cache clean-artifacts-all clean-all purge

help:
	@echo "Common:"
	$(call PRINT_HELP,make help,show this message)
	$(call PRINT_HELP,make install,set up the project with extras ($(EXTRAS)))
	$(call PRINT_HELP,make shell,open the project virtualenv)
	$(call PRINT_HELP,make shell-pdf,install PDF extras and open the shell)
	$(call PRINT_HELP,make test,run the test suite)
	$(call PRINT_HELP,make lint,run ruff checks)
	$(call PRINT_HELP,make fmt,format code with ruff)
	$(call PRINT_HELP,make clean,remove build artifacts (keeps venv))
	@echo ""
	@echo "Variables:"
	$(call PRINT_HELP,EXTRAS=dev$(comma)pdf,choose extras installed by make install)
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

shell-pdf: EXTRAS=pdf
shell-pdf: install
	@$(MAKE) shell

enter: shell

leave:
	@echo "Already in an activated shell? Type 'exit' or press Ctrl-D to leave the virtualenv."

deps-shell: deps
	@$(MAKE) shell

test: install
	@$(PYTHON_BIN) -m pytest

coverage: install
	@mkdir -p artifacts/coverage/html
	@$(PYTHON_BIN) -m pytest --cov=src/edugain_analysis --cov-report=term --cov-report=xml:artifacts/coverage/coverage.xml --cov-report=html:artifacts/coverage/html

lint: install
	@. "$(VENV)"/bin/activate && ./scripts/dev/lint.sh

fmt: install
	@$(PYTHON_BIN) -m ruff format src/ tests/

dev-env:
	./scripts/dev/dev-env.sh

dev-env-coverage:
	./scripts/dev/dev-env.sh --with-coverage

dev-env-parallel:
	./scripts/dev/dev-env.sh --with-parallel

dev-env-tests:
	./scripts/dev/dev-env.sh --with-tests

dev-env-fresh:
	./scripts/dev/dev-env.sh --fresh

clean-pycache:
	@find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.py[co]" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true

clean:
	$(MAKE) clean-pycache
	./scripts/maintenance/clean-artifacts.sh --artifacts-only
	@rm -rf *.egg-info

clean-env:
	@rm -rf "$(VENV)"

clean-artifacts:
	./scripts/maintenance/clean-artifacts.sh --artifacts-only

clean-cache:
	./scripts/maintenance/clean-artifacts.sh --cache-only

clean-artifacts-all:
	./scripts/maintenance/clean-artifacts.sh --reports

clean-all: clean clean-env clean-artifacts-all

purge: clean-all
