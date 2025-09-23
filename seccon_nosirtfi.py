#!/usr/bin/env python3
"""
eduGAIN Security Contact Analysis Tool

This script downloads the current eduGAIN metadata aggregate XML and parses it to identify
entities that have security contacts but do not carry a SIRTFI Entity Category certification.

Output: CSV format with columns: RegistrationAuthority, EntityType, OrganizationName, EntityID

Usage:
    python seccon_nosirtfi.py                    # Download and analyze current metadata
    python seccon_nosirtfi.py --local-file file  # Analyze local XML file
    python seccon_nosirtfi.py --no-headers       # Omit CSV headers
    python seccon_nosirtfi.py --url URL          # Use custom metadata URL

Based on the code of https://gitlab.geant.org/edugain/edugain-contacts
"""

import argparse
import csv
import sys
from typing import List, Optional, Union
from xml.etree import ElementTree as ET

import requests

# Configuration
EDUGAIN_METADATA_URL = "https://mds.edugain.org/edugain-v2.xml"
REQUEST_TIMEOUT = 30

# SAML metadata namespaces
NAMESPACES = {
    "md": "urn:oasis:names:tc:SAML:2.0:metadata",
    "mdui": "urn:oasis:names:tc:SAML:metadata:ui",
    "shibmd": "urn:mace:shibboleth:metadata:1.0",
    "remd": "http://refeds.org/metadata",
    "icmd": "http://id.incommon.org/metadata",
    "mdrpi": "urn:oasis:names:tc:SAML:metadata:rpi",
    "mdattr": "urn:oasis:names:tc:SAML:metadata:attribute",
    "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
}


def download_metadata(url: str, timeout: int = REQUEST_TIMEOUT) -> bytes:
    """Download eduGAIN metadata from the specified URL."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        content: bytes = response.content
        return content
    except requests.exceptions.RequestException as e:
        print(f"Error downloading metadata from {url}: {e}", file=sys.stderr)
        sys.exit(1)


def parse_metadata(
    xml_content: Optional[bytes], local_file: Optional[str] = None
) -> ET.Element:
    """Parse XML metadata content or local file."""
    try:
        if local_file:
            return ET.parse(local_file).getroot()
        else:
            return ET.fromstring(xml_content)  # type: ignore
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        sys.exit(1)


def analyze_entities(root: ET.Element) -> List[List[Union[str, None]]]:
    """Analyze entities to find those with security contacts but no SIRTFI certification."""
    entities_list = []
    entities = root.findall("./md:EntityDescriptor", NAMESPACES)

    # Pre-compile XPath expressions for performance
    sec_contact_refeds = './md:ContactPerson[@remd:contactType="http://refeds.org/metadata/contactType/security"]'
    sec_contact_incommon = './md:ContactPerson[@icmd:contactType="http://id.incommon.org/metadata/contactType/security"]'
    sirtfi_xpath = './md:Extensions/mdattr:EntityAttributes/saml:Attribute[@Name="urn:oasis:names:tc:SAML:attribute:assurance-certification"]/saml:AttributeValue'
    reg_info_xpath = "./md:Extensions/mdrpi:RegistrationInfo"
    org_name_xpath = "./md:Organization/md:OrganizationDisplayName"
    sp_descriptor_xpath = "./md:SPSSODescriptor"
    idp_descriptor_xpath = "./md:IDPSSODescriptor"

    sirtfi_value = "https://refeds.org/sirtfi"

    for entity in entities:
        # Early exit if no entityID
        ent_id = entity.attrib.get("entityID")
        if not ent_id:
            continue

        # Find security contact elements (optimized)
        sec_contact_els = entity.findall(sec_contact_refeds, NAMESPACES)
        if not sec_contact_els:
            sec_contact_els = entity.findall(sec_contact_incommon, NAMESPACES)

        # Skip if no security contacts
        if not sec_contact_els:
            continue

        # Check for SIRTFI Entity Category (optimized with early exit)
        sirtfi = any(
            ec.text == sirtfi_value
            for ec in entity.findall(sirtfi_xpath, NAMESPACES)
            if ec.text
        )

        # Skip if has SIRTFI certification
        if sirtfi:
            continue

        # Get registration authority (required field)
        registration_info = entity.find(reg_info_xpath, NAMESPACES)
        if registration_info is None:
            continue

        registration_authority = registration_info.attrib.get(
            "registrationAuthority", ""
        ).strip()
        if not registration_authority:
            continue

        # Get organization name with null safety
        orgname_elem = entity.find(org_name_xpath, NAMESPACES)
        orgname = (
            orgname_elem.text.strip()
            if orgname_elem is not None and orgname_elem.text
            else "Unknown"
        )

        # Determine entity type (optimized)
        if entity.find(sp_descriptor_xpath, NAMESPACES) is not None:
            ent_type = "SP"
        elif entity.find(idp_descriptor_xpath, NAMESPACES) is not None:
            ent_type = "IdP"
        else:
            ent_type = None

        entities_list.append([registration_authority, ent_type, orgname, ent_id])

    return entities_list


def main() -> None:
    """Main function to orchestrate the analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze eduGAIN metadata for entities with security contacts but no SIRTFI certification"
    )
    parser.add_argument(
        "--local-file", help="Use local XML file instead of downloading"
    )
    parser.add_argument(
        "--no-headers", action="store_true", help="Omit CSV headers from output"
    )
    parser.add_argument(
        "--url", default=EDUGAIN_METADATA_URL, help="Custom metadata URL"
    )
    args = parser.parse_args()

    # Get metadata
    if args.local_file:
        root = parse_metadata(None, args.local_file)
    else:
        xml_content = download_metadata(args.url)
        root = parse_metadata(xml_content)

    # Analyze entities
    entities_list = analyze_entities(root)

    # Output results
    writer = csv.writer(sys.stdout)
    if not args.no_headers:
        writer.writerow(
            ["RegistrationAuthority", "EntityType", "OrganizationName", "EntityID"]
        )
    writer.writerows(entities_list)


if __name__ == "__main__":
    main()
