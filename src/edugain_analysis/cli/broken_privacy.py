"""
eduGAIN Broken Privacy Links Analysis Tool

This script downloads the current eduGAIN metadata aggregate XML and parses it to identify
SPs with broken privacy statement URLs. It uses the URL validation cache if available.

If no cache exists, run with --validate to build it, or run 'edugain-analyze --validate' first.

Output: CSV format with columns: Federation, SP, PrivacyLink, ErrorCode

Usage:
    edugain-broken-privacy                    # Download and analyze current metadata (requires cache)
    edugain-broken-privacy --validate         # Build cache if missing, then analyze
    edugain-broken-privacy --local-file file  # Analyze local XML file
    edugain-broken-privacy --no-headers       # Omit CSV headers
    edugain-broken-privacy --url URL          # Use custom metadata URL

Based on the code of https://gitlab.geant.org/edugain/edugain-contacts
"""

import argparse
import csv
import sys
from xml.etree import ElementTree as ET

import requests

from ..core.analysis import analyze_privacy_security
from ..core.metadata import (
    get_federation_mapping,
    load_url_validation_cache,
    map_registration_authority,
    save_url_validation_cache,
)

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
    xml_content: bytes | None, local_file: str | None = None
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


def analyze_broken_privacy_links(
    root: ET.Element,
    validation_cache: dict[str, dict] | None,
    federation_mapping: dict[str, str] | None,
) -> list[list[str]]:
    """Analyze SPs to find those with broken privacy statement URLs."""
    broken_links_list = []
    entities = root.findall("./md:EntityDescriptor", NAMESPACES)

    # Pre-compile XPath expressions for performance
    privacy_xpath = ".//mdui:PrivacyStatementURL"
    reg_info_xpath = "./md:Extensions/mdrpi:RegistrationInfo"
    org_name_xpath = "./md:Organization/md:OrganizationDisplayName"
    sp_descriptor_xpath = "./md:SPSSODescriptor"

    for entity in entities:
        # Early exit if no entityID
        ent_id = entity.attrib.get("entityID")
        if not ent_id:
            continue

        # Only analyze SPs
        is_sp = entity.find(sp_descriptor_xpath, NAMESPACES) is not None
        if not is_sp:
            continue

        # Check for privacy statement URL
        privacy_elem = entity.find(privacy_xpath, NAMESPACES)
        if privacy_elem is None or privacy_elem.text is None:
            continue

        privacy_url = privacy_elem.text.strip()
        if not privacy_url:
            continue

        # Check if URL is in validation cache and is broken
        if validation_cache is None or privacy_url not in validation_cache:
            # No validation data available for this URL
            continue

        validation_result = validation_cache[privacy_url]

        # Determine if URL is broken
        # URL is considered broken if:
        # 1. Not accessible (accessible == False)
        # 2. Has an error
        # 3. Has a non-2xx/3xx status code
        is_broken = not validation_result.get("accessible", False)
        error_msg = validation_result.get("error", "")
        status_code = validation_result.get("status_code", 0)

        if not is_broken and not error_msg:
            # URL is working fine
            continue

        # Get registration authority and map to federation name
        registration_info = entity.find(reg_info_xpath, NAMESPACES)
        if registration_info is None:
            continue

        registration_authority = registration_info.attrib.get(
            "registrationAuthority", ""
        ).strip()
        if not registration_authority:
            continue

        # Map registration authority to federation name
        federation_name = map_registration_authority(
            registration_authority, federation_mapping or {}
        )

        # Get organization name with null safety
        orgname_elem = entity.find(org_name_xpath, NAMESPACES)
        orgname = (
            orgname_elem.text.strip()
            if orgname_elem is not None and orgname_elem.text
            else "Unknown"
        )

        # Format error code - prefer actual HTTP status code, fallback to error message
        if status_code and status_code != 0:
            error_code = str(status_code)
        elif error_msg:
            error_code = error_msg
        else:
            error_code = "Unknown error"

        broken_links_list.append([federation_name, orgname, privacy_url, error_code])

    return broken_links_list


def main() -> None:
    """Main function to orchestrate the analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze eduGAIN metadata for SPs with broken privacy statement URLs"
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
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate URLs if cache is missing or outdated",
    )
    args = parser.parse_args()

    # Load URL validation cache
    print("Loading URL validation cache...", file=sys.stderr)
    validation_cache = load_url_validation_cache()

    # Check if cache is available
    if validation_cache is None:
        if not args.validate:
            print(
                "Error: No URL validation cache found. Run with --validate to build cache,",
                file=sys.stderr,
            )
            print(
                "or run 'edugain-analyze --validate' first.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(
            "No URL validation cache found. Will run validation after loading metadata...",
            file=sys.stderr,
        )
    else:
        print(
            f"Loaded {len(validation_cache)} cached URL validation results",
            file=sys.stderr,
        )

    # Load federation mapping
    print("Loading federation mapping...", file=sys.stderr)
    federation_mapping = get_federation_mapping()

    # Get metadata
    if args.local_file:
        print(f"Parsing local metadata file: {args.local_file}", file=sys.stderr)
        root = parse_metadata(None, args.local_file)
    else:
        print(f"Downloading metadata from {args.url}...", file=sys.stderr)
        xml_content = download_metadata(args.url)
        root = parse_metadata(xml_content)

    # Run validation if cache was missing
    if validation_cache is None and args.validate:
        print("Running URL validation to build cache...", file=sys.stderr)
        validation_cache = {}
        entities_list, stats, federation_stats = analyze_privacy_security(
            root,
            federation_mapping=federation_mapping,
            validate_urls=True,
            validation_cache=validation_cache,
            max_workers=10,
        )

        # Save cache
        if validation_cache:
            print(
                f"Saving URL validation cache with {len(validation_cache)} entries",
                file=sys.stderr,
            )
            save_url_validation_cache(validation_cache)

    # Analyze entities
    print("Analyzing SPs for broken privacy links...", file=sys.stderr)
    broken_links_list = analyze_broken_privacy_links(
        root, validation_cache, federation_mapping
    )

    print(
        f"Found {len(broken_links_list)} SPs with broken privacy links", file=sys.stderr
    )

    # Output results
    writer = csv.writer(sys.stdout)
    if not args.no_headers:
        writer.writerow(["Federation", "SP", "PrivacyLink", "ErrorCode"])
    writer.writerows(broken_links_list)


if __name__ == "__main__":
    main()
