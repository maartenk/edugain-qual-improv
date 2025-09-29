"""Core analysis functionality for eduGAIN metadata."""

from .analysis import analyze_privacy_security, filter_entities
from .metadata import (
    get_federation_mapping,
    get_metadata,
    load_url_validation_cache,
    parse_metadata,
    save_url_validation_cache,
)
from .validation import validate_privacy_url

__all__ = [
    "analyze_privacy_security",
    "filter_entities",
    "get_metadata",
    "parse_metadata",
    "get_federation_mapping",
    "load_url_validation_cache",
    "save_url_validation_cache",
    "validate_privacy_url",
]
