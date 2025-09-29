"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

import pytest

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_metadata_xml():
    """Sample metadata XML for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
    <md:EntityDescriptor entityID="https://example.edu/sp">
        <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
            <md:Extensions>
                <mdui:UIInfo xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui">
                    <mdui:PrivacyStatementURL xml:lang="en">https://example.edu/privacy</mdui:PrivacyStatementURL>
                </mdui:UIInfo>
                <remd:ContactPerson xmlns:remd="http://refeds.org/metadata"
                                   contactType="http://refeds.org/metadata/contactType/security"
                                   remd:contactType="http://refeds.org/metadata/contactType/security">
                    <md:EmailAddress>security@example.edu</md:EmailAddress>
                </remd:ContactPerson>
            </md:Extensions>
        </md:SPSSODescriptor>
        <md:Organization>
            <md:OrganizationName xml:lang="en">Example University</md:OrganizationName>
        </md:Organization>
    </md:EntityDescriptor>
</md:EntitiesDescriptor>"""


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Temporary cache directory for testing."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir
