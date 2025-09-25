# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains tools for eduGAIN quality improvement:

- **`seccon_nosirtfi.py`**: Analyzes eduGAIN metadata to identify entities with security contacts but without SIRTFI Entity Category certification
- **`privacy_security_analysis.py`**: Analyzes eduGAIN metadata to identify entities missing privacy statement URLs and/or security contacts

## Setup and Installation

### Environment Setup
```bash
# Create virtual environment (required due to externally-managed Python environment)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
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

### Running the Privacy/Security Analysis Script
```bash
# Basic usage - full analysis with summary statistics
python privacy_security_analysis.py

# Show only summary statistics (no CSV output)
python privacy_security_analysis.py --summary-only

# Filter for specific missing elements
python privacy_security_analysis.py --missing-privacy   # Only entities without privacy statements
python privacy_security_analysis.py --missing-security  # Only entities without security contacts
python privacy_security_analysis.py --missing-both      # Only entities missing both

# Use local file or custom URL
python privacy_security_analysis.py --local-file metadata.xml
python privacy_security_analysis.py --url CUSTOM_URL

# Save filtered results
python privacy_security_analysis.py --missing-both > entities_missing_both.csv

# Output format: RegistrationAuthority,EntityType,OrganizationName,EntityID,HasPrivacyStatement,PrivacyStatementURL,HasSecurityContact
# Summary shows statistics like: "4127 out of 10044 (~41.1%)" for privacy statements
```

## Architecture

### Core Components

- **seccon_nosirtfi.py**: Main script that downloads eduGAIN metadata XML aggregate and parses it
  - Downloads from configurable URL (default: `https://mds.edugain.org/edugain-v2.xml`)
  - Parses SAML metadata using ElementTree with comprehensive error handling
  - Identifies entities with security contacts but no SIRTFI certification
  - Outputs CSV format to stdout with optional headers
  - Supports command-line arguments for flexibility

- **privacy_security_analysis.py**: Analyzes entities for privacy statement URLs and security contacts
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

### Known Issues
- Broken pipe error when piping output to `head` (normal behavior)
- Script requires network connectivity unless using `--local-file` option

## Dependencies

- **requests 2.32.5**: HTTP client for downloading metadata
- **Python 3.13+**: Uses xml.etree.ElementTree and csv modules

## Development Notes

- Virtual environment is required due to macOS externally-managed Python environment
- Script supports both remote and local XML processing via command-line options
- Namespace definitions support multiple SAML metadata schemas (REFEDS, InCommon, etc.)
- Code is modularized with separate functions for downloading, parsing, and analysis
- Comprehensive error handling for network failures and XML parsing errors
- Null-safe handling for optional metadata elements
