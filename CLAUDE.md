# CLAUDE.md

Guidance for Claude Code and AI assistants working with this repository.

## Project Overview

A modern Python package for eduGAIN quality improvement analysis with modular architecture:

- **`src/edugain_analysis/`**: Main package (CLI, core logic, formatters, config)
- **CLI Commands**: `edugain-analyze`, `edugain-seccon`, `edugain-sirtfi`, `edugain-broken-privacy`
- **Standards**: PEP 517/518/621 compliant, Python 3.11+

## Quick Setup

```bash
# Fast path - Makefile
make install EXTRAS=dev,tests
make shell

# Alternative - dev script
./scripts/dev/dev-env.sh --fresh --with-tests

# Manual
python3 -m venv .venv && source .venv/bin/activate
pip install -e .[dev,tests]
```

## Architecture

```
src/edugain_analysis/
├── cli/          # Command-line interfaces (4 tools)
├── core/         # Business logic (analysis, metadata, validation, security)
├── formatters/   # Output generation (CSV, markdown, summary, PDF)
└── config/       # Configuration constants
```

### Key Components

**CLI Layer** (`cli/`):
- `main.py` - Privacy/security/SIRTFI analysis
- `seccon.py` - Security contacts without SIRTFI
- `sirtfi.py` - SIRTFI without security contacts
- `broken_privacy.py` - Broken privacy links
- `pdf.py` - PDF report generation

**Core Logic** (`core/`):
- `analysis.py` - Entity analysis engine
- `metadata.py` - Smart caching (XDG-compliant)
- `validation.py` - Parallel URL validation
- `security.py` - SSRF protection, CSV injection prevention

**Formatters** (`formatters/`):
- `base.py` - Text, CSV, markdown
- `pdf.py` - PDF reports with charts

## Testing

```bash
# Run tests (245 tests)
pytest

# Coverage report
pytest --cov=src/edugain_analysis --cov-report=html

# Parallel execution
pytest -n auto
```

Tests are in `tests/unit/` with comprehensive coverage (100% CLI, 90%+ core).

## Code Guidelines

**Module Separation**:
- CLI: Argument parsing, orchestration only
- Core: Business logic, no I/O dependencies
- Formatters: Output generation, no business logic
- Config: Constants only

**Patterns**:
- Type hints: Use `str | None` (PEP 604)
- Imports: Absolute from package root
- Error handling: Specific exceptions, print to stderr
- Caching: Use platformdirs for XDG paths
- Testing: Mock external deps, test edge cases

## Development Tasks

```bash
# Code quality
ruff format src/ tests/
ruff check --fix src/ tests/
pre-commit run --all-files

# Testing
pytest -v
pytest --cov=src/edugain_analysis

# Local CI
./scripts/dev/local-ci.sh
```

## Feature Development Workflow

1. Create feature branch: `git checkout -b feature/name`
2. Implement in appropriate module (`cli/`, `core/`, `formatters/`)
3. Add type hints and docstrings
4. Write unit tests in `tests/unit/`
5. Run tests: `pytest -v`
6. Check coverage: `pytest --cov`
7. Quality checks: `ruff check`, `ruff format --check`
8. Commit with descriptive message
9. Push and create PR

## Security Considerations

The codebase includes security protections:
- **SSRF protection** (`core/security.py`): Blocks private IPs, cloud metadata
- **CSV injection prevention**: Sanitizes formula characters
- **URL sanitization**: Removes credentials from logs

Always validate user inputs, especially:
- `--source` parameter (URL/file paths)
- CSV exports (entity names, federation names)
- URL display in error messages

## CI/CD

- **GitHub Actions**: `.github/workflows/ci.yml`
- **Matrix testing**: Python 3.11, 3.12, 3.13, 3.14
- **Quality gates**: Tests, linting (ruff), coverage (Codecov)
- **CLI validation**: All 4 entry points tested

## Troubleshooting

- **Import errors**: Run `pip install -e .`
- **Cache issues**: Clear `~/.cache/edugain-analysis/`
- **Test failures**: Run `pytest -v` for details
- **Coverage gaps**: Check `artifacts/coverage/html/index.html`

## Key References

- User documentation: `README.md`
- Feature roadmap: `docs/ROADMAP.md`
- Test structure: `tests/unit/` (organized by module)
- Development scripts: `scripts/dev/`
