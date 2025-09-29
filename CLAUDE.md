# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains tools for eduGAIN quality improvement:

- **`seccon_nosirtfi.py`**: Analyzes eduGAIN metadata to identify entities with security contacts but without SIRTFI Entity Category certification
- **`edugain_analysis/`**: Modular Python package for comprehensive privacy statement and security contact analysis
- **`analyze.py`**: Streamlined entry point for the eduGAIN analysis package
- **`privacy_security_analysis.py`**: ⚠️ DEPRECATED - Legacy monolithic script (use analyze.py instead)

## Setup and Installation

### Environment Setup
```bash
# Create virtual environment (required due to externally-managed Python environment)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
# Production: pip install -r requirements-runtime.txt
# Development: pip install -r requirements.txt
```

### Running the Main Script
```bash
# With virtual environment activated - basic usage
python seccon_nosirtfi.py

# Command-line options
python seccon_nosirtfi.py --help                    # Show help
python seccon_nosirtfi.py --no-headers              # Omit CSV headers
python seccon_nosirtfi.py --local-file metadata.xml # Use local XML file
python seccon_nosirtfi.py --url CUSTOM_URL          # Use custom metadata URL

# Save output to file
python seccon_nosirtfi.py > entities_without_sirtfi.csv

# Output is CSV format with headers: RegistrationAuthority,EntityType,OrganizationName,EntityID
# Example output:
# https://rafiki.ke,SP,KENET eduVPN,https://eduvpn.kenet.or.ke/php-saml-sp/metadata
```

### Running the Privacy/Security Analysis Tool
```bash
# NEW MODULAR INTERFACE (recommended)
python analyze.py                          # Show summary statistics (default)
python analyze.py --report                 # Generate detailed markdown report
python analyze.py --csv entities           # Export all entities to CSV
python analyze.py --csv federations        # Export federation statistics to CSV
python analyze.py --csv urls --validate    # Export detailed URL validation results
python analyze.py --validate               # Enable comprehensive URL validation

# LEGACY INTERFACE (deprecated but still works)
python privacy_security_analysis.py

# Export detailed CSV lists of entities (single-purpose commands)
python privacy_security_analysis.py --list-all-entities
python privacy_security_analysis.py --list-missing-privacy
python privacy_security_analysis.py --list-missing-security
python privacy_security_analysis.py --list-missing-both

# Export markdown report with federation breakdown
python privacy_security_analysis.py --federation-summary > report.md

# Export federation statistics as CSV
python privacy_security_analysis.py --federation-csv > federations.csv

# Use local metadata file or custom URL
python privacy_security_analysis.py --local-file metadata.xml
python privacy_security_analysis.py --url CUSTOM_URL

# Save filtered results
python privacy_security_analysis.py --list-missing-both > critical_entities.csv

# Output format: Federation,EntityType,OrganizationName,EntityID,HasPrivacyStatement,PrivacyStatementURL,HasSecurityContact
# Note: Federation names are automatically mapped from registration authorities via eduGAIN API
# Summary shows separate statistics for SPs and IdPs:
# - Privacy statements: Only analyzed for SPs (e.g., "2681 out of 3849 SPs (69.7%)")
# - Security contacts: Analyzed for both SPs and IdPs with separate percentages
# - Combined statistics: Only shown for SPs since IdPs don't use privacy statements
# - Federation breakdown: Shows friendly federation names instead of URLs
```

## Architecture

### Core Components

- **seccon_nosirtfi.py**: Main script that downloads eduGAIN metadata XML aggregate and parses it
  - Downloads from configurable URL (default: `https://mds.edugain.org/edugain-v2.xml`)
  - Parses SAML metadata using ElementTree with comprehensive error handling
  - Identifies entities with security contacts but no SIRTFI certification
  - Outputs CSV format to stdout with optional headers
  - Supports command-line arguments for flexibility

- **privacy_security_analysis.py**: Advanced analysis tool with federation mapping, caching, and flexible output formats
  - **Smart Caching**: Metadata cached locally (12h expiry), federation names cached (30d expiry)
  - **Federation Mapping**: Uses eduGAIN API to map registration authorities to friendly names
  - **Default Behavior**: Shows summary statistics only (no CSV unless explicitly requested)
  - **Single-Purpose Commands**: `--list-missing-both`, `--list-missing-privacy`, `--federation-summary`
  - **Multiple Output Formats**: Summary statistics, detailed CSV exports, markdown reports
  - **Entity Type Differentiation**: Privacy statements analyzed for SPs only, security contacts for both
  - **Comprehensive Statistics**: Split by entity type with federation-level breakdowns

### Data Processing Flow (privacy_security_analysis.py)
1. **Initialization**: Command-line argument parsing and configuration
2. **Federation Mapping**: Load cached federation names or fetch from eduGAIN API
3. **Metadata Acquisition**: Use cached metadata or download from eduGAIN endpoint
4. **XML Parsing**: Namespace-aware ElementTree parsing with comprehensive error handling
5. **Entity Analysis**: Iterate through entities extracting:
   - Security contact elements (REFEDS or InCommon types)
   - Privacy statement URLs (SPs only)
   - Registration authority → federation name mapping
   - Entity type determination (SP/IdP)
6. **Output Generation**: Summary statistics, CSV exports, or markdown reports based on user selection

### Key Functions (privacy_security_analysis.py)
- `get_metadata()`: Smart metadata acquisition with caching and 12-hour expiry
- `get_federation_mapping()`: Federation name mapping with API integration and 30-day cache
- `analyze_privacy_security()`: Core analysis with federation name mapping
- `print_federation_summary()`: Markdown report generation with federation names
- `export_federation_csv()`: CSV export of federation-level statistics
- `map_registration_authority()`: Registration authority → federation name conversion

### Known Issues
- Broken pipe error when piping output to `head` (normal behavior)
- Script requires network connectivity unless using `--local-file` option

## Dependencies

- **requests 2.32.5**: HTTP client for downloading metadata
- **Python 3.11+**: Uses xml.etree.ElementTree and csv modules

## Development Notes

- Virtual environment is required due to macOS externally-managed Python environment
- Script supports both remote and local XML processing via command-line options
- Namespace definitions support multiple SAML metadata schemas (REFEDS, InCommon, etc.)
- Code is modularized with separate functions for downloading, parsing, and analysis
- Comprehensive error handling for network failures and XML parsing errors
- Null-safe handling for optional metadata elements

### Testing Structure

Tests are organized following Python best practices:

```
tests/
├── __init__.py
├── test_privacy_security_analysis.py    # 30 comprehensive tests
└── test_seccon_nosirtfi.py              # 24 comprehensive tests
```

Run tests with:
```bash
# Basic test run (coverage enabled by default via pyproject.toml)
pytest

# Run specific test files
pytest tests/test_seccon_nosirtfi.py -v
pytest tests/test_privacy_security_analysis.py -v

# Generate HTML coverage report
pytest --cov-report=html

# Run tests without coverage (for faster development)
pytest --no-cov

# Run with verbose output and show missing coverage lines
pytest -v --cov-report=term-missing
```

Test coverage: 96%+ on both scripts with comprehensive federation-level testing.

### Coverage Configuration
- HTML reports generated in `htmlcov/` directory
- XML reports for CI/CD integration
- **Multi-version coverage**: Automatic upload to Codecov for Python 3.11, 3.12, 3.13
- Each Python version tracked separately with flags (python-3.11, python-3.12, python-3.13)
- Parallel coverage collection enabled for comprehensive testing
- Configured to exclude test files and common boilerplate patterns

### New Features (Recent Updates)

#### Federation Name Mapping
- Automatic federation name resolution via eduGAIN API (`https://technical.edugain.org/api.php?action=list_feds`)
- Shows "InCommon" instead of "https://incommon.org" in all outputs
- 30-day cache for federation names (`.edugain_federations_cache.json`)
- Graceful fallback to registration authority URLs if API is unavailable

#### Smart Caching System
- **Metadata Cache**: 12-hour expiry (`.edugain_metadata_cache.xml`)
- **Federation Cache**: 30-day expiry (`.edugain_federations_cache.json`)
- Automatic cache management with status messages
- Significant performance improvement for repeated analysis

#### Single-Purpose Commands
- Clean command structure replacing complex argument combinations
- `--list-missing-both`: Export entities missing both privacy and security
- `--list-missing-privacy`: Export entities missing privacy statements
- `--list-missing-security`: Export entities missing security contacts
- `--list-all-entities`: Export complete entity analysis
- `--federation-summary`: Markdown report with federation breakdown
- `--federation-csv`: CSV export of federation statistics

#### Enhanced Output Formats
- Markdown reports with federation-level analysis
- CSV exports with federation statistics
- Summary-only default behavior (no CSV unless requested)
- Federation names in all outputs for improved readability
