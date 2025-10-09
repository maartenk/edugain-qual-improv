# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A modern Python package for eduGAIN quality improvement analysis. The codebase follows PEP 517/518/621 standards with a modular architecture:

- **`src/edugain_analysis/`**: Main package with modular components (CLI, core logic, formatters, config, web)
- **`analyze.py`**: Convenience wrapper that calls the main CLI entry point
- **CLI Commands**: `edugain-analyze`, `edugain-seccon`, `edugain-sirtfi`, and `edugain-broken-privacy` (installed via package entry points)
- **Web Dashboard**: Optional FastAPI + HTMX dashboard for interactive analysis

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
- CSV columns: `Federation,EntityType,OrganizationName,EntityID,HasPrivacyStatement,PrivacyStatementURL,HasSecurityContact,HasSIRTFI`
- Federation names automatically mapped via eduGAIN API (e.g., "InCommon" instead of "https://incommon.org")
- Privacy statements: Only analyzed for SPs
- Security contacts: Analyzed for both SPs and IdPs
- SIRTFI certification: Analyzed for both SPs and IdPs
- URL validation adds columns: `URLStatusCode,FinalURL,URLAccessible,RedirectCount,ValidationError`

### Usage - SIRTFI Compliance Analysis

The package includes two specialized CLI commands for SIRTFI compliance analysis:

```bash
# edugain-seccon: Find entities WITH security contacts but WITHOUT SIRTFI certification
edugain-seccon                                 # Analyze current metadata
edugain-seccon --local-file metadata.xml       # Use local XML file
edugain-seccon --no-headers                    # Omit CSV headers
edugain-seccon --url CUSTOM_URL                # Use custom metadata URL
edugain-seccon > entities_without_sirtfi.csv   # Save output

# edugain-sirtfi: Find entities WITH SIRTFI but WITHOUT security contacts (compliance violation)
edugain-sirtfi                                 # Analyze current metadata
edugain-sirtfi --local-file metadata.xml       # Use local XML file
edugain-sirtfi --no-headers                    # Omit CSV headers
edugain-sirtfi --url CUSTOM_URL                # Use custom metadata URL
edugain-sirtfi > sirtfi_violations.csv         # Save output
```

**Output:** CSV with columns `RegistrationAuthority,EntityType,OrganizationName,EntityID`

**Use Cases:**
- `edugain-seccon`: Identify potential candidates for SIRTFI certification (entities with security contacts)
- `edugain-sirtfi`: Detect SIRTFI compliance violations (SIRTFI entities missing required security contacts)

### Usage - Broken Privacy Links Analysis

```bash
# edugain-broken-privacy: Find SPs with broken (inaccessible) privacy statement URLs
edugain-broken-privacy                           # Analyze current metadata (always runs live validation)
edugain-broken-privacy --local-file metadata.xml # Use local XML file
edugain-broken-privacy --no-headers              # Omit CSV headers
edugain-broken-privacy --url CUSTOM_URL          # Use custom metadata URL
edugain-broken-privacy > broken_links.csv        # Save output
```

**Output:** CSV with columns `Federation,SP,EntityID,PrivacyLink,ErrorCode,ErrorType,CheckedAt`

**Features:**
- **Live Validation**: Always performs real-time HTTP checks with 10 parallel workers
- **Error Categorization**: SSL errors, 404s, timeouts, connection errors, etc.
- **Federation Mapping**: Automatic federation name resolution
- **Progress Reporting**: Real-time validation progress updates

**Use Case:**
- Identify broken privacy statement links across eduGAIN federations for remediation

### Usage - Web Dashboard

```bash
# Install with web dependencies
pip install -e .[web]

# Import data into database (required first-time setup)
python -m edugain_analysis.web.import_data

# Import with URL validation (slower, includes accessibility checks)
python -m edugain_analysis.web.import_data --validate-urls

# Generate test data for development
python -m edugain_analysis.web.import_data --test-data --days 30

# Start the web server
uvicorn edugain_analysis.web.app:app --reload

# Access dashboard at http://localhost:8000
```

**Features (All MVP Priorities Complete + Enhancements):**
- **Priority 1**: Entity-level tracking (10,000+ entities), URL validation database with SQLAlchemy models
- **Priority 2**: Live search (300ms debounce), federation drill-down views, entity detail pages with historical data
- **Priority 3**: Interactive filtering/sorting, Chart.js visualizations, CSV/JSON export
- **Priority 4**: URL validation results page, cache status indicators, configuration page with adjustable settings
- **Priority 5**: Historical trend charts (7/30/90/180/365 day views), snapshot comparison, entity change detection
- **Priority 6**: Mobile-responsive design (480px/768px/1024px breakpoints), print styles
- **Enhanced Progress Tracking**: Real-time 5-stage progress indicator for data refresh operations with global banner
- **Improved UX**: Speedometer gauges with color-coded gradient backgrounds, persistent refresh status across pages
- **Production Ready**: Comprehensive deployment guide (production.md) with Docker, Nginx, systemd configurations
- **API Documentation**: Full OpenAPI/Swagger docs with examples, organized into 8 tagged categories
- **Database Management**: Aligned export/import UI with backup/restore capabilities
- HTMX-powered for fast partial updates without heavy JavaScript
- PicoCSS classless styling for minimal overhead

## Architecture

### Package Structure

```
src/edugain_analysis/
├── __init__.py              # Package exports
├── __main__.py              # Python -m edugain_analysis support
├── cli/
│   ├── main.py              # Privacy/security analysis CLI (edugain-analyze)
│   ├── seccon.py            # Security contact analysis CLI (edugain-seccon)
│   ├── sirtfi.py            # SIRTFI compliance validation CLI (edugain-sirtfi)
│   └── broken_privacy.py    # Broken privacy links CLI (edugain-broken-privacy)
├── config/
│   └── settings.py          # Configuration constants, namespaces, URLs
├── core/
│   ├── analysis.py          # Core analysis logic for privacy/security
│   ├── metadata.py          # Metadata downloading, parsing, federation mapping
│   └── validation.py        # URL validation with parallel processing
├── formatters/
│   └── base.py              # Output formatters (CSV, markdown, summary)
└── web/                     # Web dashboard (optional)
    ├── __init__.py
    ├── app.py               # FastAPI application with routes
    ├── models.py            # SQLAlchemy ORM models (Snapshot, Federation, Entity, URLValidation)
    ├── import_data.py       # CLI for importing analysis results into database
    ├── templates/           # Jinja2 + HTMX templates
    │   ├── base.html        # Base template with navigation
    │   ├── dashboard.html   # Main dashboard page
    │   ├── federations.html # Federation list page
    │   ├── empty.html       # Empty state when no data
    │   └── partials/        # HTMX partial fragments
    │       ├── stats_cards.html
    │       ├── federation_table.html
    │       └── trend_chart.html
    └── static/              # CSS/JS assets (PicoCSS, Chart.js)
```

### Core Components

#### CLI Layer (`cli/`)
- **main.py**: Privacy/security analysis interface with flexible output formats
  - Default: summary statistics
  - Options: markdown reports, CSV exports, URL validation
  - Unified `--source` argument for local files or custom URLs
- **seccon.py**: Security contact analysis tool
  - Identifies entities WITH security contacts but WITHOUT SIRTFI certification
  - Use case: Find SIRTFI certification candidates
  - Standalone tool with minimal dependencies
- **sirtfi.py**: SIRTFI compliance validation tool
  - Identifies entities WITH SIRTFI certification but WITHOUT security contacts
  - Use case: Detect SIRTFI compliance violations
  - Standalone tool with minimal dependencies
- **broken_privacy.py**: Broken privacy links analysis tool
  - Identifies SPs with broken (inaccessible) privacy statement URLs
  - Use case: Find privacy links that need fixing
  - Self-contained with live URL validation (10 parallel workers)
  - Error categorization (SSL, 404, timeouts, connection errors)

#### Core Logic (`core/`)
- **analysis.py**: Entity analysis engine
  - `analyze_privacy_security()`: Main analysis function
  - Processes entities for privacy statements (SPs), security contacts (both SPs/IdPs), and SIRTFI certification (both SPs/IdPs)
  - SIRTFI detection via XPath: `./md:Extensions/mdattr:EntityAttributes/saml:Attribute[@Name="urn:oasis:names:tc:SAML:attribute:assurance-certification"]/saml:AttributeValue` checking for value `https://refeds.org/sirtfi`
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

#### Web Layer (`web/`) - Optional
- **models.py**: SQLAlchemy database models
  - `Snapshot`: Analysis snapshots with timestamps (historical tracking), includes SIRTFI coverage statistics
  - `Federation`: Per-federation statistics linked to snapshots, includes SIRTFI counts (sps_has_sirtfi, idps_has_sirtfi, etc.)
  - `Entity`: Individual SP/IdP entities with privacy/security/SIRTFI status (has_sirtfi column)
  - `URLValidation`: Privacy statement URL validation results with status codes
  - All models use proper indexes and foreign key relationships
- **import_data.py**: Data import pipeline
  - `import_snapshot()`: Runs analysis and saves to database
  - `generate_test_data()`: Creates synthetic data for development
  - Supports `--validate-urls` flag for URL validation
  - Parses list-of-lists format from `analyze_privacy_security()`
- **app.py**: FastAPI web application
  - Full page routes: `/`, `/federations`
  - HTMX partial routes: `/partials/stats`, `/partials/federations`, `/partials/trends`
  - JSON API routes: `/api/snapshot/latest`, `/api/federations`
  - Template filters: `time_ago()` for relative timestamps
  - Database dependency injection via `get_db()`

### Data Processing Flow

**Privacy/Security/SIRTFI Analysis:**
1. **Argument Parsing**: Parse CLI options, determine output format and validation mode
2. **Cache Loading**: Load federation mapping and URL validation cache (if applicable)
3. **Metadata Acquisition**: Download or use cached metadata (12h expiry)
4. **XML Parsing**: Parse with namespace-aware ElementTree
5. **Entity Analysis**: Extract privacy statements, security contacts, SIRTFI certification, and federation info
   - Privacy statements: SP-only (remd:PrivacyStatementURL)
   - Security contacts: Both SPs/IdPs (remd:SecurityContact or md:ContactPerson[type=security])
   - SIRTFI: Both SPs/IdPs (Entity Category `https://refeds.org/sirtfi`)
6. **URL Validation** (optional): Parallel HTTP checks for privacy statement URLs
7. **Statistics Generation**: Aggregate totals and per-federation breakdowns (includes SIRTFI counts)
8. **Output**: Format as summary, CSV, or markdown based on user selection
   - Summary: Displays SIRTFI coverage with color-coded percentages (🟢 ≥80%, 🟡 50-79%, 🔴 <50%)
   - CSV: Includes `HasSIRTFI` column (position 7, after HasSecurityContact)
   - Markdown: Per-federation SIRTFI statistics in tables
9. **Cache Saving**: Persist updated URL validation cache

**SIRTFI Compliance Analysis:**

*edugain-seccon (Security Contact Analysis):*
1. Download/parse metadata
2. Find entities with security contacts (REFEDS or InCommon format)
3. Check SIRTFI Entity Category certification
4. Output CSV of entities with security contacts but WITHOUT SIRTFI

*edugain-sirtfi (SIRTFI Validation):*
1. Download/parse metadata
2. Find entities with SIRTFI Entity Category certification
3. Check for security contact presence (REFEDS or InCommon format)
4. Output CSV of entities with SIRTFI but WITHOUT security contacts (violations)

### Key Features

- **XDG Base Directory Compliance**: Cache files stored in `~/.cache/edugain-analysis/` (respects `XDG_CACHE_HOME`)
- **Smart Caching**: Metadata (12h), federation names (30d), URL validation (persistent)
- **Federation Mapping**: Automatic resolution via eduGAIN API with graceful fallback
- **Entity Type Differentiation**: Privacy statements for SPs only, security contacts and SIRTFI for both SPs/IdPs
- **SIRTFI Coverage Tracking**: Comprehensive tracking of SIRTFI certification across all output formats (summary, CSV, markdown)
- **Parallel URL Validation**: Configurable thread pool (default: 10 threads)
- **Multiple Output Formats**: Summary, CSV (filtered/unfiltered), markdown reports

## Dependencies

**Core:**
- **requests ≥2.28.0**: HTTP client for metadata and API calls
- **platformdirs ≥3.0.0**: XDG Base Directory compliance for cache storage
- **Python 3.11+**: Type hints, xml.etree.ElementTree, csv, concurrent.futures

**Development (optional):**
- pytest, pytest-cov, pytest-xdist: Testing and coverage
- ruff: Linting and formatting
- pre-commit: Git hooks for code quality

**Web (optional):**
- **fastapi ≥0.104.0**: Modern async web framework for dashboard
- **uvicorn ≥0.24.0**: ASGI server for running FastAPI
- **sqlalchemy ≥2.0.0**: ORM for database models (Snapshot, Federation, Entity, URLValidation)
- **jinja2 ≥3.1.0**: Template engine for HTML rendering
- **python-multipart ≥0.0.6**: Form data parsing

## Development Notes

### Code Organization
- **Modular design**: CLI, core logic, formatters, and config are separated
- **Type hints**: Full type annotations for all public functions
- **XDG compliance**: Cache files use platformdirs for OS-appropriate locations
- **Namespace handling**: Support for multiple SAML metadata schemas (REFEDS, InCommon, etc.)
- **Error handling**: Comprehensive try/catch for network, parsing, and validation errors
- **Null safety**: Defensive coding for optional XML elements

### Testing Structure

Tests follow pytest best practices with 260+ test cases covering all modules:

```
tests/
├── unit/
│   ├── test_cli_main.py           # Privacy/security CLI tests (17 tests)
│   ├── test_cli_seccon.py         # Security contact CLI tests (15 tests)
│   ├── test_cli_sirtfi.py         # SIRTFI compliance CLI tests (15 tests)
│   ├── test_cli_broken_privacy.py # Broken privacy links CLI tests (38 tests)
│   ├── test_core_analysis.py      # Analysis logic tests (13 tests)
│   ├── test_core_metadata.py      # Metadata operations tests (43 tests)
│   ├── test_core_validation.py    # URL validation tests (24 tests)
│   ├── test_formatters.py         # Output formatter tests (9 tests)
│   ├── test_web_models.py         # Web database model tests (6 tests)
│   ├── test_web_app.py            # Web application tests (69 tests)
│   ├── test_web_import_data.py    # Web import functionality (4 tests)
│   ├── test_package_basic.py      # Import and basic functionality (10 tests)
│   └── test_main_module.py        # Main module tests (2 tests)
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

**Coverage:** 81.53% overall (100% for CLI, 91%+ for core modules, 62-71% for web modules which contain integration-level code). See [COVERAGE_ANALYSIS.md](COVERAGE_ANALYSIS.md) for detailed breakdown and improvement recommendations.

### Coverage Configuration
- **HTML reports**: Generated in `htmlcov/` directory
- **XML reports**: For CI/CD Codecov integration
- **Multi-version testing**: Python 3.11, 3.12, 3.13 tracked separately
- **Parallel coverage**: Enabled via pytest-cov configuration
- **Exclusions**: Test files, `__main__` blocks, abstract methods, debug code

### CI/CD Integration
- **GitHub Actions**: Automated testing on all branches via `.github/workflows/ci.yml`
- **Trigger events**: Push to any branch, pull requests to any branch, manual workflow dispatch
- **Codecov**: Automatic coverage upload with multi-version flags (python-3.11, python-3.12, python-3.13)
- **Quality gates**: Linting and formatting (ruff)
- **Matrix testing**: Python 3.11, 3.12, and 3.13 tested in parallel
- **Continue on error**: Tests continue even if individual steps fail to maximize coverage reporting

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
# Format code with ruff
ruff format src/ tests/

# Lint with ruff (with auto-fix)
ruff check --fix src/ tests/

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
7. Run quality checks: `ruff check`, `ruff format --check`
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

### Performance Tips
- URL validation is slow by design (network I/O) - use caching
- Parallel testing: `pytest -n auto` for faster test runs
- Metadata caching reduces repeated downloads significantly
