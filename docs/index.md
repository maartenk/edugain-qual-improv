# eduGAIN Analysis Documentation

## Overview

The eduGAIN Analysis package (v3.0.0) provides comprehensive tools for analyzing eduGAIN metadata quality, focusing on privacy statement and security contact coverage across federations. Features a modern HTMX-powered web dashboard for interactive federation monitoring.

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/maartenk/edugain-qual-improv.git
cd edugain-qual-improv

# Create virtual environment (Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# Install package
pip install -e .

# Install with web dashboard
pip install -e .[web]
```

### Basic Usage

#### CLI Analysis

```bash
# Analyze current eduGAIN metadata
edugain-analyze

# Generate detailed markdown report
edugain-analyze --report

# Export entities missing privacy statements
edugain-analyze --csv missing-privacy

# Enable URL validation (checks accessibility)
edugain-analyze --validate

# Analyze security contacts without SIRTFI
edugain-seccon
```

#### Web Dashboard

```bash
# Import data into database
python -m edugain_analysis.web.import_data

# Import with URL validation
python -m edugain_analysis.web.import_data --validate-urls

# Start web server
uvicorn edugain_analysis.web.app:app --reload

# Access dashboard at http://localhost:8000
```

## Features

### CLI Tools
- **Privacy & Security Analysis**: Comprehensive coverage metrics for SPs and IdPs
- **URL Validation**: Parallel HTTP accessibility checking for privacy statement URLs
- **Federation Intelligence**: Automatic mapping from registration authorities to friendly names
- **Multiple Output Formats**: Summary statistics, CSV exports, markdown reports
- **XDG Compliance**: Smart caching with 12h metadata, 30d federation, 7d URL validation expiry

### Web Dashboard
- **Interactive Monitoring**: Real-time federation statistics with HTMX partial updates
- **Entity-Level Tracking**: Individual SP/IdP storage with historical snapshots
- **Search & Filtering**: Live search with 300ms debounce, multi-column sorting
- **Trend Analysis**: Chart.js visualizations for 7/30/90/180/365 day trends
- **URL Validation Results**: Status codes, redirects, error tracking
- **Export Functionality**: CSV/JSON exports with filters
- **Mobile Responsive**: Breakpoints at 480px/768px/1024px

### Code Quality
- **Testing**: 204 tests with 81.53% coverage (100% for CLI, 91%+ for core modules)
- **Type Safety**: Full type hints throughout codebase
- **Modern Tooling**: Ruff for linting and formatting
- **CI/CD**: GitHub Actions with Python 3.11/3.12/3.13 matrix testing

## Architecture

The package follows modern Python standards (PEP 517/518/621) with a modular structure:

```
src/edugain_analysis/
├── cli/              # Command-line interfaces (main.py, seccon.py)
├── core/             # Business logic (analysis, metadata, validation)
├── formatters/       # Output formatting (CSV, markdown, summary)
├── config/           # Configuration constants and settings
└── web/              # Web dashboard (FastAPI + HTMX + SQLAlchemy)
    ├── app.py        # FastAPI routes and API endpoints
    ├── models.py     # SQLAlchemy ORM (Snapshot, Federation, Entity, URLValidation)
    ├── import_data.py # CLI to database sync
    ├── templates/    # Jinja2 + HTMX templates
    └── static/       # CSS/JS (PicoCSS, Chart.js)
```

## Documentation

- **[README.md](../README.md)**: Project overview and quick start
- **[CLAUDE.md](../CLAUDE.md)**: Developer guide for contributors
- **[production.md](../production.md)**: Production deployment guide
- **[COVERAGE_ANALYSIS.md](../COVERAGE_ANALYSIS.md)**: Test coverage report
- **[CHANGELOG.md](../CHANGELOG.md)**: MVP completion history

## Links

- **Repository**: https://github.com/maartenk/edugain-qual-improv
- **Issues**: https://github.com/maartenk/edugain-qual-improv/issues
- **License**: MIT
