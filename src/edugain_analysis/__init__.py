"""
eduGAIN Quality Analysis Package

A streamlined tool for analyzing eduGAIN metadata to assess privacy statement
and security contact coverage across federations.

Modules:
    config: Configuration constants and settings
    metadata: Metadata downloading, caching, and parsing
    validation: HTTP accessibility validation for privacy statement URLs
    analysis: Core entity and federation analysis logic
    formatters: Output formatting for summaries, reports, and CSV exports
    cli: Command-line interface and main entry point
"""

import sys

# Check Python version requirement (not needed for runtime since pyproject.toml enforces it,
# but provides a friendlier error message for users who bypass pip)
if sys.version_info < (3, 11):  # noqa: UP036
    sys.exit(
        "Error: eduGAIN Analysis requires Python 3.11 or later.\n"
        f"You are running Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}.\n"
        "Please upgrade your Python version or use a compatible interpreter."
    )

__version__ = "2.4.3"
__author__ = "eduGAIN Quality Analysis Team"

from .core import (
    analyze_privacy_security,
    filter_entities,
    get_federation_mapping,
    get_metadata,
    parse_metadata,
    validate_privacy_url,
)
from .formatters import export_federation_csv, print_summary

__all__ = [
    "analyze_privacy_security",
    "filter_entities",
    "print_summary",
    "export_federation_csv",
    "get_metadata",
    "parse_metadata",
    "get_federation_mapping",
    "validate_privacy_url",
]
