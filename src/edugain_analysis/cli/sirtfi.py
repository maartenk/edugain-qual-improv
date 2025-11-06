"""
eduGAIN SIRTFI Compliance Validation Tool

This script downloads the current eduGAIN metadata aggregate XML and parses it to identify
entities that carry SIRTFI Entity Category certification but do NOT have security contacts.

This helps identify entities that claim SIRTFI compliance but violate the requirement
to publish security contact information in their metadata.

Output: CSV format with columns: RegistrationAuthority, EntityType, OrganizationName, EntityID

Usage:
    edugain-sirtfi                    # Download and analyze current metadata
    edugain-sirtfi --local-file file  # Analyze local XML file
    edugain-sirtfi --no-headers       # Omit CSV headers
    edugain-sirtfi --url URL          # Use custom metadata URL

Based on the code of https://gitlab.geant.org/edugain/edugain-contacts
"""

import argparse
from xml.etree import ElementTree as ET

from ..core.entities import iter_entity_records
from .utils import run_csv_cli

EDUGAIN_METADATA_URL = "https://mds.edugain.org/edugain-v2.xml"
REQUEST_TIMEOUT = 30

DESCRIPTION = "SIRTFI certifications without security contacts"
HEADERS = ["RegistrationAuthority", "EntityType", "OrganizationName", "EntityID"]


def analyze_entities(root: ET.Element) -> list[list[str | None]]:
    """Analyze entities to find those with SIRTFI certification but no security contacts."""
    entities_list: list[list[str | None]] = []
    for record in iter_entity_records(root):
        if (
            record.registration_authority
            and record.has_sirtfi
            and not record.has_security
        ):
            entity_type: str | None = record.entity_type if record.roles else None
            entities_list.append(
                [
                    record.registration_authority,
                    entity_type,
                    record.org_name,
                    record.entity_id,
                ]
            )

    return entities_list


def main() -> None:
    """Main function to orchestrate the analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze eduGAIN metadata for entities with SIRTFI certification but no security contacts"
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

    run_csv_cli(
        analyze_entities,
        HEADERS,
        local_file=args.local_file,
        url=None if args.local_file else args.url,
        default_url=EDUGAIN_METADATA_URL,
        timeout=REQUEST_TIMEOUT,
        include_headers=not args.no_headers,
        error_label=DESCRIPTION,
    )


if __name__ == "__main__":
    main()
