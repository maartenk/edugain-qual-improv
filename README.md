# eduGAIN Quality Improvement Tools

[![CI](https://github.com/maartenk/edugain-qual-improv/workflows/CI/badge.svg)](https://github.com/maartenk/edugain-qual-improv/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/maartenk/edugain-qual-improv/branch/main/graph/badge.svg)](https://codecov.io/gh/maartenk/edugain-qual-improv)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

Python tools for analyzing eduGAIN federation metadata quality and security compliance.

### Key Features
- 🔍 **Security Contact Analysis**: Identify entities with security contacts lacking SIRTFI certification
- 🔒 **Privacy Statement Monitoring**: Track entities missing privacy statement URLs

## 🚀 Quick Start
```bash
# Clone repository
git clone https://github.com/maartenk/edugain-qual-improv.git
cd edugain-qual-improv

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
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
# Full analysis with summary statistics
python privacy_security_analysis.py

# Show only summary (no CSV output)
python privacy_security_analysis.py --summary-only

# Filter for specific issues
python privacy_security_analysis.py --missing-privacy
python privacy_security_analysis.py --missing-security
python privacy_security_analysis.py --missing-both

# Save filtered results
python privacy_security_analysis.py --missing-both > critical_entities.csv
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
RegistrationAuthority,EntityType,OrganizationName,EntityID,HasPrivacyStatement,PrivacyStatementURL,HasSecurityContact
https://example.org,SP,Example Service,https://sp.example.org,True,https://example.org/privacy,False
https://university.edu,IdP,Example University,https://idp.university.edu,False,,True
```

### Summary Statistics
```
Privacy Statement Analysis:
- 4127 out of 10044 entities (~41.1%) have privacy statements
- 5917 entities missing privacy statements

Security Contact Analysis:
- 2156 out of 10044 entities (~21.5%) have security contacts
- 7888 entities missing security contacts
```

## 👩‍💻 Development

### Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/maartenk/edugain-qual-improv.git
cd edugain-qual-improv

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest test_seccon_nosirtfi.py test_privacy_security_analysis.py -v --cov=seccon_nosirtfi --cov=privacy_security_analysis
```

## 🔒 Testing & Quality

Tests are automatically run for Python 3.11, 3.12, and 3.13 with code coverage reporting.

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
Analyzes entities for privacy statement URLs and security contacts:
- Downloads and parses eduGAIN metadata using the same infrastructure as seccon_nosirtfi.py
- Identifies entities missing privacy statement URLs (`mdui:PrivacyStatementURL`)
- Identifies entities missing security contacts (`remd:contactType="http://refeds.org/metadata/contactType/security"`)
- Provides comprehensive statistics and filtering options
- Outputs detailed CSV reports with summary statistics to stderr

### Data Processing Flow
1. Command-line argument parsing for configuration options
2. HTTP GET request to eduGAIN metadata endpoint (with timeout and error handling)
3. XML parsing with namespace-aware ElementTree (with error handling)
4. Entity iteration looking for:
   - Security contact elements (REFEDS or InCommon types)
   - SIRTFI Entity Category absence
   - Registration authority information
   - Entity type (SP/IdP) determination
5. CSV output generation with optional headers

### Key Functions
- `download_metadata()`: Handles HTTP requests with timeout and error handling
- `parse_metadata()`: Parses XML content or local files with error handling
- `analyze_entities()`: Core analysis logic for identifying target entities
- `main()`: Command-line interface and orchestration

## 📋 Requirements

### System Requirements
- **Python**: 3.11+ (tested on 3.11, 3.12, 3.13)
- **Memory**: 256MB+ recommended for large metadata files
- **Network**: Internet connectivity for metadata download (unless using local files)

### Dependencies
- **requests 2.32.5**: HTTP client for downloading metadata
- **pytest**: Testing framework with coverage support

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
