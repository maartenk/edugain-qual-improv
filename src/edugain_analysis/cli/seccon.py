import argparse
from xml.etree import ElementTree as ET

from ..core.entities import iter_entity_records
from .utils import run_csv_cli

EDUGAIN_METADATA_URL = "https://mds.edugain.org/edugain-v2.xml"
REQUEST_TIMEOUT = 30

DESCRIPTION = "security contacts without SIRTFI certification"
HEADERS = ["RegistrationAuthority", "EntityType", "OrganizationName", "EntityID"]


def analyze_entities(root: ET.Element) -> list[list[str | None]]:
    """Analyze entities to find those with security contacts but no SIRTFI certification."""
    entities_list: list[list[str | None]] = []
    for record in iter_entity_records(root):
        if (
            record.registration_authority
            and record.has_security
            and not record.has_sirtfi
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
