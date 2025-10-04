# eduGAIN Analysis Package

[![CI](https://github.com/maartenk/edugain-qual-improv/workflows/CI/badge.svg)](https://github.com/maartenk/edugain-qual-improv/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/maartenk/edugain-qual-improv/branch/main/graph/badge.svg)](https://codecov.io/gh/maartenk/edugain-qual-improv)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

A comprehensive Python package for analyzing eduGAIN federation metadata quality, privacy statement coverage, security compliance, and SIRTFI certification. Built following modern Python standards with PEP 517/518/621 compliance.

### Key Features
- 🔰 **SIRTFI Coverage Tracking**: Comprehensive SIRTFI certification tracking across all CLI outputs (summary, CSV, markdown reports)
- 🔍 **SIRTFI Compliance Tools**: Two specialized CLI tools for security contact and SIRTFI certification validation
- 🔒 **Privacy Statement Monitoring**: HTTP accessibility validation for privacy statement URLs with dedicated broken links detection tool
- 🌍 **Federation Intelligence**: Automatic mapping from registration authorities to friendly names via eduGAIN API
- 💾 **XDG-Compliant Caching**: Smart caching system with configurable expiry (metadata: 12h, federations: 30d, URLs: 7d)
- 📊 **Multiple Output Formats**: Summary statistics, detailed CSV exports, and markdown reports
- 🏗️ **Modern Architecture**: Modular design with comprehensive testing (100% for CLI, 90%+ for core modules)
- ⚡ **Fast Tooling**: Ruff for linting and formatting
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

# Or install with development dependencies
pip install -e .[dev]
```

### Basic Usage

```bash
# Analyze eduGAIN metadata for privacy, security, and SIRTFI coverage
python analyze.py

# Generate detailed markdown report (includes SIRTFI statistics)
python analyze.py --report

# Export entities missing privacy statements (includes SIRTFI column)
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

### SIRTFI Compliance Analysis

The package includes two specialized commands for analyzing SIRTFI compliance:

```bash
# Find entities WITH security contacts but WITHOUT SIRTFI certification
edugain-seccon                              # Analyze current metadata
edugain-seccon --local-file metadata.xml    # Use local file
edugain-seccon --no-headers                 # Omit CSV headers
edugain-seccon > seccon_report.csv          # Save to file

# Find entities WITH SIRTFI certification but WITHOUT security contacts (compliance violation)
edugain-sirtfi                              # Analyze current metadata
edugain-sirtfi --local-file metadata.xml    # Use local file
edugain-sirtfi --no-headers                 # Omit CSV headers
edugain-sirtfi > sirtfi_violations.csv      # Save to file
```

**Output Format:** CSV with columns `RegistrationAuthority,EntityType,OrganizationName,EntityID`

**Use Cases:**
- `edugain-seccon`: Identify potential candidates for SIRTFI certification (entities already with security contacts)
- `edugain-sirtfi`: Detect SIRTFI compliance violations (entities claiming SIRTFI without publishing security contacts)

### Broken Privacy Links Analysis

The package includes a specialized command for finding Service Providers with broken (inaccessible) privacy statement URLs:

```bash
# Find SPs with broken privacy statement links (always runs live validation)
edugain-broken-privacy                          # Analyze current metadata
edugain-broken-privacy --local-file metadata.xml # Use local file
edugain-broken-privacy --no-headers             # Omit CSV headers
edugain-broken-privacy --url CUSTOM_URL         # Use custom metadata URL
edugain-broken-privacy > broken_links.csv       # Save to file
```

**Output Format:** CSV with columns `Federation,SP,EntityID,PrivacyLink,ErrorCode,ErrorType,CheckedAt`

**Features:**
- **Live Validation**: Always performs real-time HTTP checks (10 parallel workers)
- **Error Categorization**: Categorizes errors into actionable types (SSL errors, 404s, timeouts, etc.)
- **Federation Mapping**: Automatically maps registration authorities to friendly federation names
- **Progress Reporting**: Shows validation progress with status updates

**Use Cases:**
- Identify broken privacy statement links that need fixing
- Monitor privacy statement accessibility across federations
- Generate reports for federation operators to improve compliance

### Using the Package Directly

```bash
# Run the main analysis module
python -m edugain_analysis

# Run specific components
python -m edugain_analysis.cli.main
python -m edugain_analysis.cli.seccon
python -m edugain_analysis.cli.sirtfi
python -m edugain_analysis.cli.broken_privacy
```

## 🏗️ Package Architecture

The package follows Python best practices with a modular structure:

```
src/edugain_analysis/
├── core/                     # Core analysis logic
│   ├── analysis.py          # Main analysis functions
│   ├── metadata.py          # Metadata handling and XDG-compliant caching
│   └── validation.py        # URL validation with parallel processing
├── formatters/              # Output formatting
│   └── base.py             # Text, CSV, and markdown formatters
├── cli/                     # Command-line interfaces
│   ├── main.py             # Primary CLI (edugain-analyze)
│   ├── seccon.py           # Security contact CLI (edugain-seccon)
│   ├── sirtfi.py           # SIRTFI compliance CLI (edugain-sirtfi)
│   └── broken_privacy.py   # Broken privacy links CLI (edugain-broken-privacy)
└── config/                  # Configuration and patterns
    └── settings.py         # Constants and validation patterns
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

## 🔰 SIRTFI Coverage Tracking

The main analysis tools (`edugain-analyze`, `python analyze.py`) now include comprehensive SIRTFI (Security Incident Response Trust Framework for Federated Identity) certification tracking across all output formats.

### What is SIRTFI?

SIRTFI is a framework that enables the coordination of incident response activities for federated identity services. Entities with SIRTFI certification have committed to specific incident response capabilities and communication practices.

### Output Examples

**Summary Statistics** (includes SIRTFI section):
```
=== eduGAIN Quality Analysis: Privacy, Security & SIRTFI Coverage ===
Total entities analyzed: 10,234 (SPs: 6,145, IdPs: 4,089)

🔰 SIRTFI Certification Coverage:
  ✅ Total entities with SIRTFI: 4,623 out of 10,234 (45.2%)
  ❌ Total entities without SIRTFI: 5,611 out of 10,234 (54.8%)
    📊 SPs: 2,768 with / 3,377 without (45.0% coverage)
    📊 IdPs: 1,855 with / 2,234 without (45.4% coverage)
```

**CSV Entity Export** (includes `HasSIRTFI` column):
```csv
Federation,EntityType,OrganizationName,EntityID,HasPrivacyStatement,PrivacyStatementURL,HasSecurityContact,HasSIRTFI
InCommon,SP,Example University,https://sp.example.edu,Yes,https://example.edu/privacy,Yes,Yes
DFN-AAI,IdP,Test Institute,https://idp.test.de,N/A,N/A,Yes,No
```

**Federation Statistics CSV** (includes SIRTFI columns):
```csv
Federation,TotalEntities,TotalSPs,TotalIdPs,SPsWithPrivacy,SPsMissingPrivacy,EntitiesWithSecurity,EntitiesMissingSecurity,SPsWithSecurity,SPsMissingSecurity,IdPsWithSecurity,IdPsMissingSecurity,EntitiesWithSIRTFI,EntitiesMissingSIRTFI,SPsWithSIRTFI,SPsMissingSIRTFI,IdPsWithSIRTFI,IdPsMissingSIRTFI,SPsWithBoth,SPsWithAtLeastOne,SPsMissingBoth
InCommon,3450,2100,1350,1890,210,2760,690,1680,420,1080,270,1552,1898,945,1155,607,743,1575,2058,42
```

**Markdown Reports** (includes per-federation SIRTFI statistics):
```markdown
## Federation Analysis

### InCommon (3,450 entities: 2,100 SPs, 1,350 IdPs)

**SIRTFI Certification:** 🟢 1,552/3,450 (45.0%)
  ├─ SPs: 🟡 945/2,100 (45.0%)
  └─ IdPs: 🟡 607/1,350 (45.0%)
```

### Key Points

- **Applies to Both SPs and IdPs**: Unlike privacy statements (SP-only), SIRTFI applies to both entity types
- **Always Included**: The `HasSIRTFI` column is automatically included in all entity CSV exports
- **Federation Breakdown**: Per-federation statistics show SIRTFI coverage at the federation level
- **Color-Coded Status**: 🟢 (≥80%), 🟡 (50-79%), 🔴 (<50%) for visual feedback

For SIRTFI compliance validation and finding violations, use the specialized tools:
- `edugain-seccon`: Find entities with security contacts but without SIRTFI (potential candidates)
- `edugain-sirtfi`: Find entities with SIRTFI but without security contacts (compliance violations)

## 💾 Cache Management

All data is stored in XDG-compliant cache directories:

**Cache Location by Platform:**
- macOS: `~/Library/Caches/edugain-analysis/`
- Linux: `~/.cache/edugain-analysis/`
- Windows: `%LOCALAPPDATA%\edugain\edugain-analysis\Cache\`

**Cache Files:**
- `metadata.xml` - eduGAIN metadata (expires after 12 hours)
- `federations.json` - Federation name mappings (expires after 30 days)
- `url_validation.json` - URL validation results (expires after 7 days)

**Cache Management Commands:**
```bash
# View cache location
python -c "from platformdirs import user_cache_dir; print(user_cache_dir('edugain-analysis', 'edugain'))"

# Clear cache to force fresh download
rm -rf ~/Library/Caches/edugain-analysis/metadata.xml  # macOS
rm -rf ~/.cache/edugain-analysis/metadata.xml           # Linux
```

## 🔧 Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/edugain_analysis

# Lint and format code
ruff check src/ tests/
ruff format --check src/ tests/

# Or use the convenience script
scripts/lint.sh
```

### Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/                          # Unit tests (260+ tests)
pytest tests/unit/test_cli_sirtfi.py        # SIRTFI CLI tests only

# Run with coverage reporting
pytest --cov=src/edugain_analysis --cov-report=html

# Run without coverage (faster)
pytest --no-cov

# Run tests in parallel
pytest -n auto
```

### Code Quality

The project uses modern Python tooling:
- **Ruff**: Fast linting and code formatting
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

## 🏗️ Recent Improvements (v2.1.0)

**SIRTFI Compliance Analysis:**
- 🆕 Added `edugain-sirtfi` CLI for SIRTFI compliance validation
- 🆕 Added `edugain-broken-privacy` CLI for finding broken privacy statement links
- 🔍 Detects entities with SIRTFI certification but missing security contacts (compliance violations)
- 📊 Comprehensive SIRTFI tracking across all output formats (summary, CSV, markdown)
- ✅ 260+ comprehensive test cases with high code coverage

**Tooling & Code Quality:**
- 🧹 Removed Black and mypy dependencies - using Ruff exclusively for all linting and formatting
- 📝 Streamlined development workflow with single unified toolchain
- ✅ All tests passing with 100% CLI coverage, 90%+ core module coverage

**Documentation:**
- 📚 Updated README.md and CLAUDE.md with new CLI tools
- 🔧 Cleaned up all references to deprecated tooling
- 📖 Enhanced developer guide with detailed data processing flows

## 📋 Requirements

- **Python**: 3.11 or later
- **Dependencies**:
  - `requests` (≥2.28.0) - HTTP requests
  - `platformdirs` (≥3.0.0) - XDG-compliant directories
- **Development Dependencies** (install with `[dev]`):
  - pytest, pytest-cov, pytest-xdist - Testing and coverage
  - ruff - Linting and formatting
  - pre-commit - Git hooks for quality assurance

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
