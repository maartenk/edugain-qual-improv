"""Basic import tests for the refactored package structure."""

import os
import sys

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


def test_package_imports():
    """Test that basic package imports work."""
    from edugain_analysis import __version__

    assert __version__ == "2.1.0"


def test_core_imports():
    """Test core module imports."""
    from edugain_analysis.core.analysis import analyze_privacy_security, filter_entities
    from edugain_analysis.core.metadata import (
        get_federation_mapping,
        get_metadata,
        parse_metadata,
    )
    from edugain_analysis.core.validation import validate_privacy_url

    # Basic checks that functions exist
    assert callable(analyze_privacy_security)
    assert callable(filter_entities)
    assert callable(get_metadata)
    assert callable(parse_metadata)
    assert callable(get_federation_mapping)
    assert callable(validate_privacy_url)


def test_formatters_imports():
    """Test formatter imports."""
    from edugain_analysis.formatters.base import (
        export_federation_csv,
        print_federation_summary,
        print_summary,
        print_summary_markdown,
    )

    assert callable(print_summary)
    assert callable(export_federation_csv)
    assert callable(print_summary_markdown)
    assert callable(print_federation_summary)


def test_cli_imports():
    """Test CLI imports."""
    from edugain_analysis.cli import seccon
    from edugain_analysis.cli.main import main

    assert callable(main)
    assert hasattr(seccon, "main")


def test_config_imports():
    """Test configuration imports."""
    from edugain_analysis.config.settings import (
        EDUGAIN_METADATA_URL,
        NAMESPACES,
        URL_VALIDATION_THREADS,
    )

    assert isinstance(EDUGAIN_METADATA_URL, str)
    assert isinstance(URL_VALIDATION_THREADS, int)
    assert isinstance(NAMESPACES, dict)


def test_cache_imports():
    """Test cache utilities imports (now in metadata module)."""
    from edugain_analysis.core.metadata import (
        get_cache_dir,
        load_json_cache,
        save_json_cache,
    )

    assert callable(get_cache_dir)
    assert callable(load_json_cache)
    assert callable(save_json_cache)
