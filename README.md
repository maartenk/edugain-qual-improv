# eduGAIN Analysis Package

[![CI](https://github.com/maartenk/edugain-qual-improv/workflows/CI/badge.svg)](https://github.com/maartenk/edugain-qual-improv/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/maartenk/edugain-qual-improv/branch/main/graph/badge.svg)](https://codecov.io/gh/maartenk/edugain-qual-improv)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

A comprehensive Python package for analyzing eduGAIN federation metadata quality, privacy statement coverage, and security compliance. Built following modern Python standards with PEP 517/518/621 compliance.

### Key Features
- 🔍 **Security Contact Analysis**: Identify entities with security contacts lacking SIRTFI certification
- 🔒 **Privacy Statement Monitoring**: HTTP accessibility validation for privacy statement URLs
- 🌍 **Federation Intelligence**: Automatic mapping from registration authorities to friendly names via eduGAIN API
- 💾 **XDG-Compliant Caching**: Cache files stored in standard user directories with configurable expiry
- 📊 **Multiple Output Formats**: Summary statistics, detailed CSV exports, and markdown reports
- 🏗️ **Modern Architecture**: Modular design with comprehensive testing (92.17% coverage)
- 📈 **Comprehensive Reporting**: Split statistics for SPs vs IdPs with federation-level breakdowns

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/maartenk/edugain-qual-improv.git
cd edugain-qual-improv

# Create virtual environment (requires Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# Install package in development mode
pip install -e .

# Or install with optional dependencies
pip install -e .[dev,web]
```

### Basic Usage

```bash
# Analyze eduGAIN metadata for privacy and security compliance
python analyze.py

# Generate detailed markdown report
python analyze.py --report

# Export entities missing privacy statements
python analyze.py --csv missing-privacy

# Enable comprehensive URL validation (slower but thorough)
python analyze.py --validate

# Or use the package directly
python -m edugain_analysis
```

## 📚 CLI Reference

### Privacy & Security Analysis

```bash
# Show summary statistics (default)
python analyze.py

# Export options
python analyze.py --csv entities               # All entities
python analyze.py --csv federations            # Federation statistics
python analyze.py --csv missing-privacy        # Entities missing privacy statements
python analyze.py --csv missing-security       # Entities missing security contacts
python analyze.py --csv missing-both           # Entities missing both
python analyze.py --csv urls                   # Basic URL list (SPs with privacy statements)
python analyze.py --csv urls-validated         # URL validation results (enables validation)

# Advanced features
python analyze.py --report                     # Detailed markdown report
python analyze.py --validate                   # Enable URL validation
python analyze.py --source metadata.xml        # Use local XML file
python analyze.py --url CUSTOM_URL             # Use custom metadata URL
```

### Using the Package Directly

```bash
# Run the main analysis module
python -m edugain_analysis

# Run specific components
python -m edugain_analysis.cli.main
python -m edugain_analysis.cli.seccon
```

## 🏗️ Package Architecture

The package follows Python best practices with a modular structure:

```
src/edugain_analysis/
├── core/                     # Core analysis logic
│   ├── analysis.py          # Main analysis functions
│   ├── metadata.py          # Metadata handling and caching
│   └── validation.py        # URL validation with language detection
├── formatters/              # Output formatting
│   └── base.py             # Text, CSV, and markdown formatters
├── cli/                     # Command-line interfaces
│   ├── main.py             # Primary CLI (edugain-analyze)
│   └── seccon.py           # Security contact CLI (edugain-seccon)
├── config/                  # Configuration and patterns
│   └── settings.py         # Constants and validation patterns
└── utils/                   # Utilities
    └── cache.py            # XDG-compliant cache management
```

## 🔍 Privacy Statement URL Validation

The package includes a fast privacy statement URL validation system that checks link accessibility across eduGAIN federations. This helps identify broken privacy statement links that need attention.

### How It Works

1. **URL Collection**: Extracts privacy statement URLs from Service Provider (SP) metadata
2. **Parallel Checking**: Tests URLs concurrently using 16 threads for fast processing
3. **HTTP Status Validation**: Simple status code check:
   - **200-399**: Accessible (working link) ✅
   - **400-599**: Broken (needs fixing) ❌
4. **Real-time Progress**: Shows validation progress with visual indicators
5. **Smart Caching**: Results cached for 1 week to avoid re-checking unchanged URLs

### Usage Examples

```bash
# Basic validation with user-friendly summary
python analyze.py --validate

# Get detailed CSV with HTTP status codes for each URL
python analyze.py --csv urls --validate

# Export entities missing privacy statements
python analyze.py --csv missing-privacy
```

### Sample Output

The summary shows simple, actionable information:
```
🔗 Privacy Statement URL Check:
  📊 Checked 2,683 privacy statement links

  ╭─ 🔗 LINK STATUS SUMMARY ─────────────────────────────────╮
  │  ✅ 2,267 links working (84.5%) │
  │  ❌ 416 links broken (15.5%)    │
  ╰───────────────────────────────────╯
```

### CSV Export Details

When using `--csv urls --validate`, you get detailed technical information:

| Field | Description | Example |
|-------|-------------|---------|
| `StatusCode` | HTTP response code | `200`, `404`, `500` |
| `FinalURL` | URL after redirects | `https://example.org/privacy` |
| `Accessible` | Working status | `Yes` / `No` |
| `ContentType` | MIME type | `text/html` |
| `RedirectCount` | Number of redirects | `0`, `1`, `2` |
| `ValidationError` | Error details | `Connection timeout` |

This gives technical staff the specific information needed to fix broken links.

## 🔧 Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/edugain_analysis

# Lint code
ruff check src/ tests/
black --check src/ tests/
mypy src/

# Or use the convenience script
scripts/lint.sh
```

### Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/                          # Unit tests
pytest tests/integration/                   # Integration tests

# Run with coverage reporting
pytest --cov=src/edugain_analysis --cov-report=html

# Run tests in parallel
pytest -n auto
```

### Code Quality

The project uses modern Python tooling:
- **Ruff**: Fast linting and code quality checks
- **Black**: Code formatting
- **mypy**: Type checking
- **pytest**: Testing with coverage
- **pre-commit**: Git hooks for quality assurance

## 📊 Output Examples

### Summary Statistics
```
eduGAIN Metadata Analysis Results
================================

📊 Entity Overview:
   Total Entities: 8,234
   Service Providers (SPs): 3,849
   Identity Providers (IdPs): 4,385

🔒 Privacy Statement Coverage (SPs only):
   SPs with Privacy Statements: 2,681 out of 3,849 (69.7%)

🛡️  Security Contact Coverage:
   SPs with Security Contacts: 1,205 out of 3,849 (31.3%)
   IdPs with Security Contacts: 2,891 out of 4,385 (65.9%)

🌍 Federation Coverage: 73 federations analyzed
```

### CSV Export Formats
- **entities**: All entities with privacy/security status
- **federations**: Federation-level statistics
- **missing-privacy**: SPs without privacy statements
- **missing-security**: Entities without security contacts
- **missing-both**: SPs missing both privacy and security
- **urls**: URL validation results (with `--validate`)

## 🏗️ Future Development

See [todo.md](todo.md) for a comprehensive roadmap of planned features and improvements, including:
- Historical tracking with database backend
- Machine learning for privacy analysis
- Advanced web dashboard
- API development
- Internationalization support

## 📋 Requirements

- **Python**: 3.11 or later
- **Dependencies**:
  - `requests` (≥2.28.0) - HTTP requests
  - `platformdirs` (≥3.0.0) - XDG-compliant directories
- **Optional Dependencies**:
  - `streamlit` (≥1.28.0) - Web dashboard (install with `[web]`)
  - Development tools (install with `[dev]`)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the coding standards
4. Run tests and linting (`pytest && scripts/lint.sh`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on the original work from [eduGAIN contacts analysis](https://gitlab.geant.org/edugain/edugain-contacts)
- Built for the eduGAIN community to improve federation metadata quality
- Follows Python packaging standards (PEP 517/518/561/621)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/maartenk/edugain-qual-improv/issues)
- **Documentation**: [Package Documentation](docs/index.md)
- **Development**: See [CLAUDE.md](CLAUDE.md) for development guidelines
