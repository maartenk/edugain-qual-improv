# eduGAIN Analysis Package

[![CI](https://github.com/maartenk/edugain-qual-improv/workflows/CI/badge.svg)](https://github.com/maartenk/edugain-qual-improv/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/maartenk/edugain-qual-improv/branch/main/graph/badge.svg)](https://codecov.io/gh/maartenk/edugain-qual-improv)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/v/release/maartenk/edugain-qual-improv)](https://github.com/maartenk/edugain-qual-improv/releases)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Table of Contents
- [Overview](#-overview)
- [Quick Start](#-quick-start)
- [Command Reference](#-command-reference)
- [Advanced Configuration](#-advanced-configuration)
- [Metadata & Caching](#-metadata--caching)
- [Advanced (optional)](#-advanced-optional)
- [Developer Setup](#-developer-setup)
- [Contributing](#-contributing)

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

### Install the CLI

```bash
python -m pip install --upgrade pip
python -m pip install edugain-analysis
```

Prefer running from a clone? Install in editable mode instead:

```bash
git clone https://github.com/maartenk/edugain-qual-improv.git
cd edugain-qual-improv
python -m pip install -e .
```

After installation, your environment exposes the CLI entry points `edugain-analyze`, `edugain-seccon`, `edugain-sirtfi`, and `edugain-broken-privacy`. They live in the Python environment’s `bin/` (or `Scripts\` on Windows) like any other console scripts.

Want to run from a clone without installing?

```bash
# Shell wrappers (from repo root)
./scripts/app/edugain-analyze.sh --report
./scripts/app/edugain-seccon.sh
./scripts/app/edugain-sirtfi.sh
./scripts/app/edugain-broken-privacy.sh

# Direct module invocation
python -m edugain_analysis.cli.main

# Convenience wrapper (repo root)
python analyze.py
```

### Run your first analysis

```bash
# Summary of privacy, security contacts, and SIRTFI coverage
edugain-analyze

# Detailed markdown report grouped by federation
edugain-analyze --report

# CSV export of entities missing privacy statements
edugain-analyze --csv missing-privacy

# Validate privacy statement URLs while producing the summary
edugain-analyze --validate
```

## 📋 Command Reference

| Command | Purpose | Helpful options |
| --- | --- | --- |
| `edugain-analyze` | Main privacy/security/SIRTFI analysis | `--report`, `--csv <type>`, `--validate`, `--source <file-or-url>` |
| `edugain-seccon` | Entities with security contacts but no SIRTFI | `--local-file`, `--no-headers` |
| `edugain-sirtfi` | Entities with SIRTFI but no security contact | `--local-file`, `--no-headers` |
| `edugain-broken-privacy` | Service Providers with broken privacy links | `--local-file`, `--no-headers`, `--url <metadata-url>` |

All commands default to the live eduGAIN aggregate metadata. Supply `--source path.xml` or `--source https://custom` to work with alternative metadata files.

### `edugain-analyze`
The primary CLI for day-to-day reporting. Generates summaries, CSV exports, and markdown reports in one pass.

```bash
# Quick snapshot with SIRTFI coverage in the summary
edugain-analyze

# Markdown report plus live privacy URL checks
edugain-analyze --report-with-validation

# Export only SPs missing both safeguards
edugain-analyze --csv missing-both --no-headers > missing.csv
```

### `edugain-seccon`
Surfaces entities that publish a security contact but have not completed SIRTFI certification—ideal for prioritizing follow-up.

```bash
# Live metadata
edugain-seccon

# Offline review against a cached aggregate
edugain-seccon --local-file reports/metadata.xml
```

### `edugain-sirtfi`
Flags entities that claim SIRTFI compliance yet fail to list a security contact, highlighting policy violations.

```bash
# Focus on current gaps
edugain-sirtfi

# Custom feed (e.g., private federation snapshot)
edugain-sirtfi --url https://example/federation.xml
```

### `edugain-broken-privacy`
Targets Service Providers with privacy statement URLs that fail a lightweight accessibility check.

```bash
# Default live run with 10 parallel validators
edugain-broken-privacy

# Skip headers when piping into other tooling
edugain-broken-privacy --no-headers | tee broken-urls.csv
```

## 📤 CSV & Report Exports

`edugain-analyze --csv` supports the following types (all include SIRTFI columns):

- `entities` – complete view of all entities
- `federations` – per-federation roll-up
- `missing-privacy`, `missing-security`, `missing-both`
- `urls` – privacy statement URLs for SPs
- `urls-validated` – includes HTTP status data (enables live validation)

Markdown reports are produced with `--report` (or `--report-with-validation` to perform live URL checks while generating the report).

**CSV Columns**

| Column | Description |
| --- | --- |
| `Federation` | Friendly federation name (API-backed) |
| `EntityType` | `SP` or `IdP` |
| `OrganizationName` | Display name from metadata |
| `EntityID` | SAML entity identifier |
| `HasPrivacyStatement` | `Yes`/`No` (SPs only) |
| `PrivacyStatementURL` | Declared privacy URL (SPs) |
| `HasSecurityContact` | `Yes`/`No` |
| `HasSIRTFI` | `Yes`/`No` |
| *(with validation)* `URLStatusCode`, `FinalURL`, `URLAccessible`, `RedirectCount`, `ValidationError` |

## 🔗 URL Validation (optional)

Enabling `--validate`, `--report-with-validation`, or `--csv urls-validated` triggers live HTTP checks for privacy statement URLs. Results are cached for seven days to avoid repeat lookups. When validation runs, extra columns are appended to CSV exports:

- `URLStatusCode`, `FinalURL`, `URLAccessible`, `RedirectCount`, `ValidationError`

## ⚙️ Advanced Configuration

Runtime defaults live in `src/edugain_analysis/config/settings.py`. Tweak them if you need to point at alternative metadata sources or adjust validation behaviour.

- `EDUGAIN_METADATA_URL`, `EDUGAIN_FEDERATIONS_API`: swap these when working with staging aggregates or private federation indexes.
- Cache knobs (`METADATA_CACHE_HOURS`, `FEDERATION_CACHE_DAYS`, `URL_VALIDATION_CACHE_DAYS`) define how long downloads are reused; shorten them during rapid testing, extend them to reduce network traffic.
- URL validation controls (`URL_VALIDATION_TIMEOUT`, `URL_VALIDATION_DELAY`, `URL_VALIDATION_THREADS`, `MAX_CONTENT_SIZE`) let you balance accuracy with load on remote sites.
- `REQUEST_TIMEOUT` covers metadata and federation lookups; bump it for slow-on-purpose mirrors.

After adjusting the settings file, re-run the CLI—changes take effect immediately because the module is imported at runtime.

## 📦 Metadata & Caching

- **Default source**: eduGAIN aggregate metadata (`https://mds.edugain.org/edugain-v2.xml`)
- **Overrides**: Use `--source path.xml` for local files or `--url` (where available) for alternate feeds
- **Caching**: Metadata (12h), federation mapping (30d), and URL validation results (7d) are cached in the XDG cache directory (typically `~/.cache/edugain-analysis/`)

## 🧰 Advanced (optional)

- Run from source: `python analyze.py` mirrors `edugain-analyze`
- Use Docker: `docker compose build` then `docker compose run --rm cli edugain-analyze`
- Batch everything locally: `scripts/dev/local-ci.sh` runs linting, tests, coverage, and Docker smoke tests
- Tweak the helper via env vars: `SKIP_COVERAGE=1` or `SKIP_DOCKER=1` to skip heavier steps

## 🛠️ Developer Setup

The Makefile now provides an end-user-friendly workflow for managing the virtual environment and tooling:

```bash
# Create/update .venv and install dev+test extras (Python 3.11+)
make install EXTRAS=dev,tests PYTHON=python3.11

# Drop into an activated shell (exit with 'exit' or Ctrl-D)
make shell

# Run linting or the full test suite
make lint
make test
```

Prefer scripts? `scripts/dev/dev-env.sh` remains available if you prefer driving the setup script directly:

```bash
# Fresh environment with test tooling and coverage plugins
./scripts/dev/dev-env.sh --fresh --with-tests --with-coverage

# Add parallel pytest workers
./scripts/dev/dev-env.sh --with-parallel
```

- `DEVENV_PYTHON` overrides the interpreter search (order: `python3.14`, `python3.13`, `python3.12`, `python3.11`, `python3`). Example: `DEVENV_PYTHON=python3.11 ./scripts/dev/dev-env.sh`.
- Manual setup: create a virtualenv and run `pip install -e ".[dev]"`. Layer optional extras like `.[tests]`, `.[coverage]`, or `.[parallel]` as needed.
- `scripts/maintenance/clean-env.sh` and `scripts/maintenance/clean-artifacts.sh` remove virtualenvs and cached outputs when you need a clean slate. Use `make clean-artifacts` or `make clean-cache` for the common paths, or call the script with `--artifacts-only` / `--cache-only` yourself; add `--reports` to prune `reports/`.
- Test coverage outputs land in `artifacts/coverage/` (HTML + XML). The `reports/` directory is reserved for CLI exports or cached metadata snapshots and is only pruned when you run `scripts/maintenance/clean-artifacts.sh --reports`.
- Script layout: `scripts/app/` (CLI wrappers), `scripts/dev/` (developer tooling), `scripts/maintenance/` (cache & environment cleanup).

## 📘 Need developer details?

Developer tooling, architecture notes, and testing guidance now live in `docs/CLAUDE.md`. The docs index at `docs/README.md` links to all supporting material.

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

## 🏗️ Recent Improvements (v2.4.2)

**CLI & Tooling:**
- 🧭 `make help` now guides everyday CLI users vs. contributors with tone-matched sections (“Run the CLI”, “Develop or extend the app”, “Maintenance”).
- 🧹 Maintenance scripts live under `scripts/maintenance/`, dev helpers under `scripts/dev/`, and app wrappers under `scripts/app/`, so you can run CLIs without installing and keep automation clean.
- 🧪 `scripts/dev/local-ci.sh` mirrors CI locally (lint, tests, coverage, Docker) and respects `SKIP_COVERAGE` / `SKIP_DOCKER` toggles.

## 📋 Requirements

- **Python**: 3.11 or later (tested on 3.11, 3.12, 3.13, 3.14)
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
4. Run tests and linting (`pytest && scripts/dev/lint.sh`)
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
- **Docs Index**: Browse [docs/README.md](docs/README.md) for additional references
- **Documentation**: See [README.md](README.md) for full documentation
- **Development**: See [docs/CLAUDE.md](docs/CLAUDE.md) for development guidelines
- **Roadmap**: See [docs/FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md) for upcoming ideas
