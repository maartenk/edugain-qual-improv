# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A modern Python package for eduGAIN quality improvement analysis. The codebase follows PEP 517/518/621 standards with a modular architecture:

- **`src/edugain_analysis/`**: Main package with modular components (CLI, core logic, formatters, config)
- **`analyze.py`**: Convenience wrapper that calls the main CLI entry point
- **CLI Commands**: `edugain-analyze` and `edugain-seccon` (installed via package entry points)

## Setup and Installation

### Environment Setup
```bash
# Create virtual environment (Python 3.11+ required)
python3 -m venv .venv
source .venv/bin/activate

# Install package in development mode
pip install -e .

# Or install with optional dependencies
pip install -e .[dev,web]
```

### Usage - Privacy/Security Analysis

```bash
# Using convenience wrapper
python analyze.py                              # Show summary statistics (default)
python analyze.py --report                     # Generate detailed markdown report
python analyze.py --report-with-validation     # Report with URL validation
python analyze.py --csv entities               # Export all entities to CSV
python analyze.py --csv federations            # Export federation statistics
python analyze.py --csv urls-validated         # Export URL validation results
python analyze.py --validate                   # Enable URL validation with summary
python analyze.py --source metadata.xml        # Use local XML file
python analyze.py --source https://custom.url  # Use custom metadata URL

# Using installed CLI command (after pip install)
edugain-analyze                                # Same options as analyze.py
edugain-analyze --report
edugain-analyze --csv entities

# CSV filtering options
python analyze.py --csv missing-privacy        # SPs missing privacy statements
python analyze.py --csv missing-security       # Entities missing security contacts
python analyze.py --csv missing-both           # Entities missing both
```

**Output Format Notes:**
- CSV columns: `Federation,EntityType,OrganizationName,EntityID,HasPrivacyStatement,PrivacyStatementURL,HasSecurityContact`
- Federation names automatically mapped via eduGAIN API (e.g., "InCommon" instead of "https://incommon.org")
- Privacy statements: Only analyzed for SPs
- Security contacts: Analyzed for both SPs and IdPs
- URL validation adds columns: `URLStatusCode,FinalURL,URLAccessible,RedirectCount,ValidationError`

### Usage - SIRTFI Security Contact Analysis

```bash
# Using installed CLI command (recommended)
edugain-seccon                                 # Analyze current metadata
edugain-seccon --local-file metadata.xml       # Use local XML file
edugain-seccon --no-headers                    # Omit CSV headers
edugain-seccon --url CUSTOM_URL                # Use custom metadata URL

# Save output to file
edugain-seccon > entities_without_sirtfi.csv
```

**Output:** CSV with columns `RegistrationAuthority,EntityType,OrganizationName,EntityID` containing entities with security contacts but no SIRTFI certification.

## Architecture

### Package Structure

```
src/edugain_analysis/
├── __init__.py              # Package exports
├── __main__.py              # Python -m edugain_analysis support
├── cli/
│   ├── main.py              # Privacy/security analysis CLI (edugain-analyze)
│   └── seccon.py            # SIRTFI security contact CLI (edugain-seccon)
├── config/
│   └── settings.py          # Configuration constants, namespaces, URLs
├── core/
│   ├── analysis.py          # Core analysis logic for privacy/security
│   ├── metadata.py          # Metadata downloading, parsing, federation mapping
│   └── validation.py        # URL validation with parallel processing
└── formatters/
    └── base.py              # Output formatters (CSV, markdown, summary)
```

### Core Components

#### CLI Layer (`cli/`)
- **main.py**: Privacy/security analysis interface with flexible output formats
  - Default: summary statistics
  - Options: markdown reports, CSV exports, URL validation
  - Unified `--source` argument for local files or custom URLs
- **seccon.py**: SIRTFI security contact analysis
  - Identifies entities with security contacts but no SIRTFI certification
  - Standalone tool with minimal dependencies

#### Core Logic (`core/`)
- **analysis.py**: Entity analysis engine
  - `analyze_privacy_security()`: Main analysis function
  - Processes entities for privacy statements (SPs) and security contacts (both SPs/IdPs)
  - Generates per-entity data, summary stats, and federation statistics
- **metadata.py**: Metadata operations
  - `get_metadata()`: Smart caching (XDG-compliant, 12h expiry)
  - `get_federation_mapping()`: API integration with 30-day cache
  - `parse_metadata()`: XML parsing with namespace handling
  - `map_registration_authority()`: Registration authority → federation name conversion
- **validation.py**: URL validation
  - Parallel HTTP status checking with configurable thread pool
  - Caching support to avoid redundant checks
  - Tracks redirects, final URLs, accessibility

#### Configuration (`config/`)
- **settings.py**: Centralized configuration
  - SAML metadata namespaces (REFEDS, InCommon, etc.)
  - Default URLs and timeouts
  - Cache expiry settings
  - Validation thread pool size

#### Formatters (`formatters/`)
- **base.py**: Output generation
  - `print_summary()`: Terminal-friendly statistics
  - `print_summary_markdown()`: Markdown report headers
  - `print_federation_summary()`: Federation breakdown tables
  - `export_federation_csv()`: Federation statistics CSV

### Data Processing Flow

**Privacy/Security Analysis:**
1. **Argument Parsing**: Parse CLI options, determine output format and validation mode
2. **Cache Loading**: Load federation mapping and URL validation cache (if applicable)
3. **Metadata Acquisition**: Download or use cached metadata (12h expiry)
4. **XML Parsing**: Parse with namespace-aware ElementTree
5. **Entity Analysis**: Extract privacy statements, security contacts, federation info
6. **URL Validation** (optional): Parallel HTTP checks for privacy statement URLs
7. **Statistics Generation**: Aggregate totals and per-federation breakdowns
8. **Output**: Format as summary, CSV, or markdown based on user selection
9. **Cache Saving**: Persist updated URL validation cache

**SIRTFI Analysis:**
1. Download/parse metadata
2. Find entities with security contacts
3. Check SIRTFI Entity Category certification
4. Output CSV of non-SIRTFI entities with security contacts

### Key Features

- **XDG Base Directory Compliance**: Cache files stored in `~/.cache/edugain-analysis/` (respects `XDG_CACHE_HOME`)
- **Smart Caching**: Metadata (12h), federation names (30d), URL validation (persistent)
- **Federation Mapping**: Automatic resolution via eduGAIN API with graceful fallback
- **Entity Type Differentiation**: Privacy statements for SPs only, security contacts for both
- **Parallel URL Validation**: Configurable thread pool (default: 10 threads)
- **Multiple Output Formats**: Summary, CSV (filtered/unfiltered), markdown reports

## Dependencies

**Core:**
- **requests ≥2.28.0**: HTTP client for metadata and API calls
- **platformdirs ≥3.0.0**: XDG Base Directory compliance for cache storage
- **Python 3.11+**: Type hints, xml.etree.ElementTree, csv, concurrent.futures

**Development (optional):**
- pytest, pytest-cov, pytest-xdist: Testing and coverage
- black, ruff, mypy: Code formatting, linting, type checking
- pre-commit: Git hooks for code quality

**Web (optional):**
- streamlit ≥1.28.0: Future web interface support

## Development Notes

### Code Organization
- **Modular design**: CLI, core logic, formatters, and config are separated
- **Type hints**: Full type annotations for all public functions
- **XDG compliance**: Cache files use platformdirs for OS-appropriate locations
- **Namespace handling**: Support for multiple SAML metadata schemas (REFEDS, InCommon, etc.)
- **Error handling**: Comprehensive try/catch for network, parsing, and validation errors
- **Null safety**: Defensive coding for optional XML elements

### Testing Structure

Tests follow pytest best practices with 200+ test cases covering all modules:

```
tests/
├── unit/
│   ├── test_cli_main.py           # Privacy/security CLI tests
│   ├── test_cli_seccon.py         # SIRTFI CLI tests
│   ├── test_core_analysis.py      # Analysis logic tests
│   ├── test_core_metadata.py      # Metadata operations tests
│   ├── test_core_validation.py    # URL validation tests
│   ├── test_formatters.py         # Output formatter tests
│   └── test_package_basic.py      # Import and basic functionality
└── integration/
    └── (integration tests)
```

**Running Tests:**
```bash
# Activate virtual environment first
source .venv/bin/activate

# Basic test run (coverage enabled by default)
pytest

# Run specific test modules
pytest tests/unit/test_cli_main.py -v
pytest tests/unit/test_core_analysis.py -v

# Generate HTML coverage report
pytest --cov-report=html
open htmlcov/index.html

# Run tests without coverage (faster)
pytest --no-cov

# Parallel execution with xdist
pytest -n auto
```

**Coverage:** 92.17% overall with comprehensive testing across all modules.

### Coverage Configuration
- **HTML reports**: Generated in `htmlcov/` directory
- **XML reports**: For CI/CD Codecov integration
- **Multi-version testing**: Python 3.11, 3.12, 3.13 tracked separately
- **Parallel coverage**: Enabled via pytest-cov configuration
- **Exclusions**: Test files, `__main__` blocks, abstract methods, debug code

### CI/CD Integration
- **GitHub Actions**: Automated testing on push/PR via `.github/workflows/ci.yml`
- **Codecov**: Automatic coverage upload with multi-version flags
- **Quality gates**: Linting (ruff), type checking (mypy), formatting (black)
- **Matrix testing**: All supported Python versions tested in parallel

## Key Features

### Federation Intelligence
- **Automatic mapping**: Registration authorities → friendly federation names via eduGAIN API
- **Smart caching**: 30-day cache for federation names (XDG-compliant location)
- **Graceful fallback**: Uses registration authority URLs if API unavailable
- **Example**: "InCommon" displayed instead of "https://incommon.org"

### Caching System
- **Metadata**: 12-hour expiry, stored in `~/.cache/edugain-analysis/`
- **Federation names**: 30-day expiry
- **URL validation**: Persistent cache to avoid redundant HTTP checks
- **Performance**: Significant speed improvement for repeated analysis

### URL Validation
- **Parallel processing**: Configurable thread pool (default: 10 threads)
- **HTTP status tracking**: Status codes, redirects, final URLs
- **Content validation**: Checks for HTML content type
- **Caching**: Persistent cache with timestamps
- **Error handling**: Captures timeout, connection, SSL errors

### Output Flexibility
- **Default**: Summary statistics (terminal-friendly)
- **CSV exports**: Filtered or unfiltered entity lists, federation statistics, URL validation
- **Markdown reports**: Federation breakdowns with detailed tables
- **Filtering**: Missing privacy, missing security, missing both
- **No-header mode**: For downstream processing

## Common Development Tasks

### Code Quality Checks
```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type check with mypy
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Adding New Features
1. Create feature branch: `git checkout -b feature/your-feature`
2. Implement changes in appropriate module (`cli/`, `core/`, `formatters/`)
3. Add type hints and docstrings
4. Write unit tests in `tests/unit/`
5. Run tests: `pytest -v`
6. Check coverage: `pytest --cov-report=term-missing`
7. Run quality checks: `ruff check`, `mypy`, `black --check`
8. Commit with descriptive message
9. Push and create PR

### Module Guidelines
- **CLI modules** (`cli/`): Argument parsing, user interaction, orchestration only
- **Core modules** (`core/`): Business logic, no I/O dependencies, highly testable
- **Formatters** (`formatters/`): Output generation, no business logic
- **Config** (`config/`): Constants only, no logic

### Common Patterns
- **Error handling**: Use try/except with specific exceptions, print to stderr
- **Type hints**: Use `str | None` (PEP 604) not `Optional[str]`
- **Imports**: Absolute imports from package root (`from ..config import ...`)
- **Caching**: Use platformdirs for XDG-compliant paths
- **Testing**: Mock external dependencies (network, file I/O), test edge cases

## Troubleshooting

### Common Issues
- **Import errors**: Ensure package installed with `pip install -e .`
- **Cache issues**: Clear cache at `~/.cache/edugain-analysis/`
- **Test failures**: Run `pytest -v` for detailed output, check mock configurations
- **Coverage gaps**: Run `pytest --cov-report=html` and review `htmlcov/index.html`
- **Type errors**: Run `mypy src/` to catch type issues before CI/CD

### Performance Tips
- URL validation is slow by design (network I/O) - use caching
- Parallel testing: `pytest -n auto` for faster test runs
- Metadata caching reduces repeated downloads significantly
