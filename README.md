# eduGAIN Quality Improvement Tools

[![CI](https://github.com/maartenk/edugain-qual-improv/workflows/CI/badge.svg)](https://github.com/maartenk/edugain-qual-improv/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/maartenk/edugain-qual-improv/branch/main/graph/badge.svg)](https://codecov.io/gh/maartenk/edugain-qual-improv)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

Python tools for analyzing eduGAIN federation metadata quality and security compliance.

### Key Features
- 🔍 **Security Contact Analysis**: Identify entities with security contacts lacking SIRTFI certification
- 🔒 **Privacy Statement Monitoring**: Track entities missing privacy statement URLs with SP/IdP differentiation
- 🌍 **Federation Name Mapping**: Automatic mapping from registration authorities to friendly federation names via eduGAIN API
- 💾 **Smart Caching**: Metadata cached locally (12-hour expiry), federation names cached (30-day expiry)
- 📊 **Multiple Output Formats**: Summary statistics, detailed CSV exports, and markdown reports
- 🎯 **Single-Purpose Commands**: Clean command structure with no complex argument combinations
- 📈 **Comprehensive Reporting**: Split statistics for SPs vs IdPs with compliance metrics

## 🚀 Quick Start
```bash
# Clone repository
git clone https://github.com/maartenk/edugain-qual-improv.git
cd edugain-qual-improv

# Create virtual environment (requires Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
# For production use:
pip install -r requirements-runtime.txt

# For development (adds testing + code formatting):
pip install -r requirements.txt

# Run analysis tools
python seccon_nosirtfi.py
python privacy_security_analysis.py
```

## 📚 Usage Examples

### Security Contact Analysis (seccon_nosirtfi.py)
```bash
# Basic usage - analyze entities with security contacts but no SIRTFI
python seccon_nosirtfi.py

# Save results with headers
python seccon_nosirtfi.py > entities_without_sirtfi.csv

# Use custom metadata URL
python seccon_nosirtfi.py --url https://your-metadata-source.xml

# Use local metadata file
python seccon_nosirtfi.py --local-file metadata.xml --no-headers
```

### Privacy & Security Analysis (privacy_security_analysis.py)
```bash
# Default: Show summary statistics only
python privacy_security_analysis.py

# Export detailed CSV lists of entities
python privacy_security_analysis.py --list-all-entities
python privacy_security_analysis.py --list-missing-privacy
python privacy_security_analysis.py --list-missing-security
python privacy_security_analysis.py --list-missing-both

# Export markdown report with federation breakdown
python privacy_security_analysis.py --federation-summary > report.md

# Export federation statistics as CSV
python privacy_security_analysis.py --federation-csv > federations.csv

# Use local metadata file
python privacy_security_analysis.py --local-file metadata.xml

# Save filtered results
python privacy_security_analysis.py --list-missing-both > critical_entities.csv
```


## 📊 Output Formats

### Security Contact Analysis Output
```csv
RegistrationAuthority,EntityType,OrganizationName,EntityID
https://rafiki.ke,SP,KENET eduVPN,https://eduvpn.kenet.or.ke/php-saml-sp/metadata
https://aaf.edu.au,IdP,University of Example,urn:mace:aaf.edu.au:idp:example.edu.au
```

### Privacy/Security Analysis Output
```csv
Federation,EntityType,OrganizationName,EntityID,HasPrivacyStatement,PrivacyStatementURL,HasSecurityContact
InCommon,SP,Example Service,https://sp.example.org,Yes,https://example.org/privacy,No
DFN-AAI,IdP,Example University,https://idp.university.edu,No,,Yes
MAREN,SP,University of Malawi,https://sp.unima.ac.mw,No,,No
```

### Summary Statistics
```
=== eduGAIN Privacy Statement and Security Contact Coverage ===
Total entities analyzed: 10044 (SPs: 3849, IdPs: 6193)

📊 Privacy Statement URL Coverage (SPs only):
  ✅ SPs with privacy statements: 2681 out of 3849 (69.7%)
  ❌ SPs missing privacy statements: 1168 out of 3849 (30.3%)

🔒 Security Contact Coverage:
  ✅ Total entities with security contacts: 4422 out of 10044 (44.0%)
  ❌ Total entities missing security contacts: 5622 out of 10044 (56.0%)
    📊 SPs: 2254 with / 1595 without (58.6% coverage)
    📊 IdPs: 2168 with / 4025 without (35.0% coverage)

📈 Combined Coverage Summary (SPs only):
  🌟 SPs with BOTH (fully compliant): 2167 out of 3849 (56.3%)
  ⚡ SPs with AT LEAST ONE: 2768 out of 3849 (71.9%)
  ❌ SPs missing both: 1081 out of 3849 (28.1%)
```

### Federation-Level Markdown Report
```markdown
# 📊 eduGAIN Quality Analysis Report

**Analysis Date:** 2025-09-25 21:08:02 UTC
**Total Entities Analyzed:** 10,046 (3,850 SPs, 6,194 IdPs)

## 🌍 Federation-Level Summary

### 📍 **InCommon**
- **Total Entities:** 2,431 (1,851 SPs, 580 IdPs)
- **SP Privacy Coverage:** 🟢 1,851/1,851 (100.0%)
- **Security Contact Coverage:** 🟢 2,431/2,431 (100.0%)
  - SPs: 1,851/1,851 (100.0%), IdPs: 580/580 (100.0%)
- **SP Full Compliance:** 🟢 1,851/1,851 (100.0%)

### 📍 **UK federation**
- **Total Entities:** 1,476 (780 SPs, 696 IdPs)
- **SP Privacy Coverage:** 🔴 100/780 (12.8%)
- **Security Contact Coverage:** 🔴 116/1,476 (7.9%)
  - SPs: 55/780 (7.1%), IdPs: 61/696 (8.8%)
- **SP Full Compliance:** 🔴 12/780 (1.5%)
```

## 💾 Caching & Performance

The tools implement smart caching to improve performance and reduce API load:

### Metadata Caching
- **Automatic**: eduGAIN metadata (84MB) cached locally as `.edugain_metadata_cache.xml`
- **Expiry**: 12-hour refresh policy
- **Benefits**: Faster analysis, reduced network usage, offline capability

### Federation Name Mapping
- **Automatic**: Federation names fetched from eduGAIN API and cached as `.edugain_federations_cache.json`
- **Expiry**: 30-day refresh policy
- **Benefits**: Shows "InCommon" instead of "https://incommon.org" in all outputs
- **Smart Integration**: Friendly names appear in all CSV exports and markdown reports

### Cache Status Messages
```
Using cached metadata (2.5 hours old)
Using cached federation names (85 federations)
Downloading fresh metadata from eduGAIN (cache expired)
```

Caches are automatically managed - no manual intervention needed!

## 👩‍💻 Development

### Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/maartenk/edugain-qual-improv.git
cd edugain-qual-improv

# Setup virtual environment (requires Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black .
```

## 🔒 Testing & Quality

- **54 comprehensive tests** covering all functionality
- **96%+ code coverage** on both scripts across all Python versions
- **Tests organized** in `tests/` directory following Python best practices
- **Automated CI/CD** testing on Python 3.11, 3.12, and 3.13
- **Multi-version coverage reporting** via Codecov for each Python version
- **Federation-level testing** including new `--federation-summary` functionality
- **Modern Python support** - requires Python 3.11+ for latest language features

## 🏗️ Architecture

### Core Components

#### seccon_nosirtfi.py
Main script that downloads eduGAIN metadata XML aggregate and parses it:
- Downloads from configurable URL (default: `https://mds.edugain.org/edugain-v2.xml`)
- Parses SAML metadata using ElementTree with comprehensive error handling
- Identifies entities with security contacts but no SIRTFI certification
- Outputs CSV format to stdout with optional headers
- Supports command-line arguments for flexibility

#### privacy_security_analysis.py
Advanced analysis tool with federation mapping, caching, and flexible output formats:
- **Smart Caching**: Metadata cached locally (12h expiry), federation names cached (30d expiry)
- **Federation Mapping**: Uses eduGAIN API to map registration authorities to friendly names
- **Default Behavior**: Shows summary statistics only (no CSV unless explicitly requested)
- **Single-Purpose Commands**: `--list-missing-both`, `--list-missing-privacy`, `--federation-summary`
- **Multiple Output Formats**: Summary statistics, detailed CSV exports, markdown reports
- **Entity Type Differentiation**: Privacy statements analyzed for SPs only, security contacts for both
- **Comprehensive Statistics**: Split by entity type with federation-level breakdowns

### Data Processing Flow
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

### Key Functions
- `get_metadata()`: Smart metadata acquisition with caching and 12-hour expiry
- `get_federation_mapping()`: Federation name mapping with API integration and 30-day cache
- `analyze_privacy_security()`: Core analysis with federation name mapping
- `print_federation_summary()`: Markdown report generation with federation names
- `export_federation_csv()`: CSV export of federation-level statistics
- `map_registration_authority()`: Registration authority → federation name conversion

## 📋 Requirements

### System Requirements
- **Python**: 3.11-3.13 (tested on 3.11, 3.12, 3.13)
- **Memory**: 256MB+ recommended for large metadata files
- **Network**: Internet connectivity for metadata download (unless using local files)

### Dependencies

Simple two-tier approach:

| File | Use Case | Dependencies |
|------|----------|--------------|
| `requirements-runtime.txt` | **Production** | `requests` only |
| `requirements.txt` | **Development** | Runtime + testing + formatting |

#### Runtime Dependencies
- **requests 2.32.5**: HTTP client for downloading metadata
- **Standard Library**: All other functionality uses built-in Python modules

#### Development Dependencies
- **pytest**: Testing framework
- **black**: Code formatting

## ❓ Troubleshooting

### Common Issues

**Q: "ModuleNotFoundError" when running scripts**
A: Ensure virtual environment is activated: `source .venv/bin/activate`

**Q: Network timeouts during metadata download**
A: Use `--local-file` option with pre-downloaded metadata

**Q: "Externally managed environment" error on Python install**
A: Always use virtual environments as shown in setup instructions

### Performance Tips
- Use `--summary-only` for quick statistics without full CSV output
- Use `--federation-summary` to identify which federations need improvement
- Pre-download metadata files for repeated analysis
- Enable compression for large output files: `python script.py | gzip > output.csv.gz`

### Known Issues
- Broken pipe error when piping output to `head` (normal behavior)
- Script requires network connectivity unless using `--local-file` option

### Getting Help
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/maartenk/edugain-qual-improv/issues)

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository and create a feature branch
2. Set up development environment as described above
3. Ensure all tests pass
4. Create a pull request with your changes

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Based on the original work of the [eduGAIN contacts project](https://gitlab.geant.org/edugain/edugain-contacts).

Special thanks to:
- The eduGAIN community for their continuous support and feedback
- GÉANT for providing the infrastructure and initial codebase
- Contributors who have helped improve this project

## 🔗 Related Projects

- [eduGAIN Website](https://edugain.org/)
- [REFEDS](https://refeds.org/)
- [SIRTFI Information](https://refeds.org/sirtfi)
