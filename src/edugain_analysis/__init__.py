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

__version__ = "2.0.0"
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
