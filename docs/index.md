# eduGAIN Analysis Documentation

## Overview

The eduGAIN Analysis package provides comprehensive tools for analyzing eduGAIN metadata quality, focusing on privacy statement and security contact coverage across federations.

## Quick Start

### Installation

```bash
pip install edugain-analysis
```

### Basic Usage

```bash
# Analyze current eduGAIN metadata
edugain-analyze

# Generate detailed report
edugain-analyze --report

# Export entities missing privacy statements
edugain-analyze --csv missing-privacy

# Analyze security contacts without SIRTFI
edugain-seccon
```

## Features

- **Comprehensive Analysis**: Privacy statements, security contacts, federation mapping
- **URL Validation**: Advanced privacy URL validation with language detection
- **Multiple Output Formats**: Summary, CSV, Markdown reports
- **XDG Compliance**: Cache files stored in standard locations
- **Modern Python**: Type hints, async support, comprehensive testing

## Architecture

The package follows Python best practices with a modular structure:

- `core/`: Analysis logic and metadata handling
- `formatters/`: Output formatting (text, CSV, markdown)
- `cli/`: Command-line interfaces
- `config/`: Configuration and patterns
- `utils/`: Utilities including XDG-compliant caching
