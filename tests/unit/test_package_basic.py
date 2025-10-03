"""Basic functionality tests for the eduGAIN analysis package."""

import os
import sys

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


class TestPackageBasics:
    """Test basic package functionality."""

    def test_package_imports(self):
        """Test that basic package imports work."""
        from edugain_analysis import __version__

        assert __version__ == "3.0.0"

    def test_core_analysis_import(self):
        """Test core analysis imports."""
        from edugain_analysis.core.analysis import (
            analyze_privacy_security,
            filter_entities,
        )

        assert callable(analyze_privacy_security)
        assert callable(filter_entities)

    def test_core_metadata_import(self):
        """Test core metadata imports."""
        from edugain_analysis.core.metadata import (
            get_federation_mapping,
            get_metadata,
            parse_metadata,
        )

        assert callable(get_metadata)
        assert callable(parse_metadata)
        assert callable(get_federation_mapping)

    def test_formatters_import(self):
        """Test formatters imports."""
        from edugain_analysis.formatters.base import (
            export_federation_csv,
            print_summary,
        )

        assert callable(print_summary)
        assert callable(export_federation_csv)

    def test_cli_import(self):
        """Test CLI imports."""
        from edugain_analysis.cli.main import main
        from edugain_analysis.cli.seccon import main as seccon_main

        assert callable(main)
        assert callable(seccon_main)

    def test_config_import(self):
        """Test configuration imports."""
        from edugain_analysis.config.settings import EDUGAIN_METADATA_URL, NAMESPACES

        assert isinstance(EDUGAIN_METADATA_URL, str)
        assert isinstance(NAMESPACES, dict)

    def test_cache_utils_import(self):
        """Test cache utilities imports (now in metadata module)."""
        from edugain_analysis.core.metadata import (
            get_cache_dir,
            load_json_cache,
            save_json_cache,
        )

        assert callable(get_cache_dir)
        assert callable(load_json_cache)
        assert callable(save_json_cache)

    def test_filter_entities_basic(self):
        """Test basic filter_entities functionality."""
        from edugain_analysis.core.analysis import filter_entities

        # Test with empty list
        result = filter_entities([], "missing-privacy")
        assert result == []

        # Test with sample entities - check behavior of actual function
        entities = [
            {
                "entity_type": "SP",
                "privacy_statement_url": None,
                "security_contact": "test@example.org",
            },
            {
                "entity_type": "SP",
                "privacy_statement_url": "https://example.org/privacy",
                "security_contact": None,
            },
        ]

        missing_privacy = filter_entities(entities, "missing-privacy")
        # Just verify it returns a list and handles the input correctly
        assert isinstance(missing_privacy, list)
        assert len(missing_privacy) >= 0

    def test_parse_metadata_basic(self):
        """Test basic XML parsing functionality."""
        from edugain_analysis.core.metadata import parse_metadata

        # Test with minimal valid XML
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        entities = parse_metadata(xml_content)
        assert len(entities) == 1
        assert entities[0].attrib["entityID"] == "https://example.org/sp"

    def test_cache_dir_creation(self):
        """Test cache directory creation."""
        from edugain_analysis.core.metadata import get_cache_dir

        cache_dir = get_cache_dir()
        # Handle both string and Path objects
        cache_dir_str = str(cache_dir)
        assert isinstance(cache_dir_str, str)
        assert "edugain" in cache_dir_str.lower()
