#!/usr/bin/env python3
"""
eduGAIN Privacy Statement and Security Contact Analysis Tool

This script downloads the current eduGAIN metadata aggregate XML and analyzes entities
to identify those missing privacy statement URLs and/or security contacts.

Output:
- CSV format with detailed entity information
- Summary statistics showing coverage percentages
- Optional filtering by missing privacy statements or security contacts

Usage:
    python privacy_security_analysis.py                     # Full analysis report
    python privacy_security_analysis.py --missing-privacy   # Only entities without privacy statements
    python privacy_security_analysis.py --missing-security  # Only entities without security contacts
    python privacy_security_analysis.py --missing-both      # Only entities missing both
    python privacy_security_analysis.py --local-file file   # Use local XML file
    python privacy_security_analysis.py --no-headers        # Omit CSV headers
    python privacy_security_analysis.py --summary-only      # Show only summary statistics
"""

import argparse
import csv
import sys
from typing import List, Optional, Tuple
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


def analyze_privacy_security(root: ET.Element) -> Tuple[List[List[str]], dict]:
    """
    Analyze entities for privacy statement URLs and security contacts.
    Privacy statements are only analyzed for SPs (not IdPs).
    Security contacts are analyzed for both IdPs and SPs.

    Returns:
        Tuple of (entity_data_list, summary_stats)
    """
    entities_list = []
    stats = {
        "total_entities": 0,
        "total_sps": 0,
        "total_idps": 0,
        "sps_has_privacy": 0,
        "sps_missing_privacy": 0,
        "idps_has_security": 0,
        "sps_has_security": 0,
        "idps_missing_security": 0,
        "sps_missing_security": 0,
        "total_has_security": 0,
        "total_missing_security": 0,
        "sps_has_both": 0,
        "sps_missing_both": 0,
    }

    entities = root.findall("./md:EntityDescriptor", NAMESPACES)

    # Pre-compile XPath expressions for performance
    privacy_xpath = ".//mdui:PrivacyStatementURL"
    sec_contact_refeds = './md:ContactPerson[@remd:contactType="http://refeds.org/metadata/contactType/security"]'
    sec_contact_incommon = './md:ContactPerson[@icmd:contactType="http://id.incommon.org/metadata/contactType/security"]'
    reg_info_xpath = "./md:Extensions/mdrpi:RegistrationInfo"
    org_name_xpath = "./md:Organization/md:OrganizationDisplayName"
    sp_descriptor_xpath = "./md:SPSSODescriptor"
    idp_descriptor_xpath = "./md:IDPSSODescriptor"

    for entity in entities:
        stats["total_entities"] += 1

        # Early exit if no entityID
        ent_id = entity.attrib.get("entityID")
        if not ent_id:
            continue

        # Determine entity type first
        is_sp = entity.find(sp_descriptor_xpath, NAMESPACES) is not None
        is_idp = entity.find(idp_descriptor_xpath, NAMESPACES) is not None

        if is_sp:
            ent_type = "SP"
            stats["total_sps"] += 1
        elif is_idp:
            ent_type = "IdP"
            stats["total_idps"] += 1
        else:
            ent_type = "Unknown"

        # Check for privacy statement URL (only for SPs)
        has_privacy = False
        privacy_url = ""
        if is_sp:
            privacy_elem = entity.find(privacy_xpath, NAMESPACES)
            has_privacy = privacy_elem is not None and privacy_elem.text is not None
            privacy_url = privacy_elem.text.strip() if has_privacy else ""

            if has_privacy:
                stats["sps_has_privacy"] += 1
            else:
                stats["sps_missing_privacy"] += 1

        # Check for security contact (both REFEDS and InCommon types)
        sec_contact_refeds_elem = entity.find(sec_contact_refeds, NAMESPACES)
        sec_contact_incommon_elem = entity.find(sec_contact_incommon, NAMESPACES)
        has_security = (
            sec_contact_refeds_elem is not None or sec_contact_incommon_elem is not None
        )

        # Update security contact statistics by entity type
        if has_security:
            stats["total_has_security"] += 1
            if is_sp:
                stats["sps_has_security"] += 1
            elif is_idp:
                stats["idps_has_security"] += 1
        else:
            stats["total_missing_security"] += 1
            if is_sp:
                stats["sps_missing_security"] += 1
            elif is_idp:
                stats["idps_missing_security"] += 1

        # Update combined statistics (only for SPs since privacy is SP-only)
        if is_sp:
            if has_privacy and has_security:
                stats["sps_has_both"] += 1
            elif not has_privacy and not has_security:
                stats["sps_missing_both"] += 1

        # Get registration authority
        registration_info = entity.find(reg_info_xpath, NAMESPACES)
        registration_authority = ""
        if registration_info is not None:
            registration_authority = registration_info.attrib.get(
                "registrationAuthority", ""
            ).strip()

        # Get organization name with null safety
        orgname_elem = entity.find(org_name_xpath, NAMESPACES)
        orgname = (
            orgname_elem.text.strip()
            if orgname_elem is not None and orgname_elem.text
            else "Unknown"
        )

        # Add entity data
        entities_list.append(
            [
                registration_authority,
                ent_type,
                orgname,
                ent_id,
                "Yes" if has_privacy else "No",
                privacy_url if has_privacy else "",
                "Yes" if has_security else "No",
            ]
        )

    return entities_list, stats


def filter_entities(
    entities_list: List[List[str]], filter_mode: str
) -> List[List[str]]:
    """Filter entities based on the specified mode."""
    if filter_mode == "missing_privacy":
        return [e for e in entities_list if e[4] == "No"]  # HasPrivacyStatement column
    elif filter_mode == "missing_security":
        return [e for e in entities_list if e[6] == "No"]  # HasSecurityContact column
    elif filter_mode == "missing_both":
        return [e for e in entities_list if e[4] == "No" and e[6] == "No"]
    else:
        return entities_list


def print_summary(stats: dict) -> None:
    """Print summary statistics with positive framing."""
    total = stats["total_entities"]
    total_sps = stats["total_sps"]
    total_idps = stats["total_idps"]

    if total == 0:
        print("No entities found in metadata.", file=sys.stderr)
        return

    print(
        "\n=== eduGAIN Privacy Statement and Security Contact Coverage ===",
        file=sys.stderr,
    )
    print(
        f"Total entities analyzed: {total} (SPs: {total_sps}, IdPs: {total_idps})",
        file=sys.stderr,
    )
    print("", file=sys.stderr)

    # Privacy statement statistics - SP only
    if total_sps > 0:
        sp_privacy_pct = (stats["sps_has_privacy"] / total_sps) * 100
        sp_missing_privacy_pct = (stats["sps_missing_privacy"] / total_sps) * 100
        print("📊 Privacy Statement URL Coverage (SPs only):", file=sys.stderr)
        print(
            f"  ✅ SPs with privacy statements: {stats['sps_has_privacy']} out of {total_sps} ({sp_privacy_pct:.1f}%)",
            file=sys.stderr,
        )
        print(
            f"  ❌ SPs missing privacy statements: {stats['sps_missing_privacy']} out of {total_sps} ({sp_missing_privacy_pct:.1f}%)",
            file=sys.stderr,
        )
        print("", file=sys.stderr)

    # Security contact statistics - split by entity type
    total_security_pct = (stats["total_has_security"] / total) * 100
    total_missing_security_pct = (stats["total_missing_security"] / total) * 100
    print("🔒 Security Contact Coverage:", file=sys.stderr)
    print(
        f"  ✅ Total entities with security contacts: {stats['total_has_security']} out of {total} ({total_security_pct:.1f}%)",
        file=sys.stderr,
    )
    print(
        f"  ❌ Total entities missing security contacts: {stats['total_missing_security']} out of {total} ({total_missing_security_pct:.1f}%)",
        file=sys.stderr,
    )

    # Split security stats by entity type
    if total_sps > 0:
        sp_security_pct = (stats["sps_has_security"] / total_sps) * 100
        print(
            f"    📊 SPs: {stats['sps_has_security']} with / {stats['sps_missing_security']} without ({sp_security_pct:.1f}% coverage)",
            file=sys.stderr,
        )

    if total_idps > 0:
        idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
        print(
            f"    📊 IdPs: {stats['idps_has_security']} with / {stats['idps_missing_security']} without ({idp_security_pct:.1f}% coverage)",
            file=sys.stderr,
        )

    print("", file=sys.stderr)

    # Combined statistics - SP only (since privacy is SP-only)
    if total_sps > 0:
        sp_both_pct = (stats["sps_has_both"] / total_sps) * 100
        sp_missing_both_pct = (stats["sps_missing_both"] / total_sps) * 100
        sp_has_at_least_one = total_sps - stats["sps_missing_both"]
        sp_at_least_one_pct = (sp_has_at_least_one / total_sps) * 100

        print("📈 Combined Coverage Summary (SPs only):", file=sys.stderr)
        print(
            f"  🌟 SPs with BOTH (fully compliant): {stats['sps_has_both']} out of {total_sps} ({sp_both_pct:.1f}%)",
            file=sys.stderr,
        )
        print(
            f"  ⚡ SPs with AT LEAST ONE: {sp_has_at_least_one} out of {total_sps} ({sp_at_least_one_pct:.1f}%)",
            file=sys.stderr,
        )
        print(
            f"  ❌ SPs missing both: {stats['sps_missing_both']} out of {total_sps} ({sp_missing_both_pct:.1f}%)",
            file=sys.stderr,
        )
        print("", file=sys.stderr)

    # Key insights for both entity types
    print("💡 Key Insights:", file=sys.stderr)

    # SP insights
    if total_sps > 0:
        if sp_privacy_pct > sp_security_pct:
            print(
                f"  • Privacy statements are better covered among SPs ({sp_privacy_pct:.1f}% vs {sp_security_pct:.1f}%)",
                file=sys.stderr,
            )
        else:
            print(
                f"  • Security contacts are better covered among SPs ({sp_security_pct:.1f}% vs {sp_privacy_pct:.1f}%)",
                file=sys.stderr,
            )
        print(
            f"  • {sp_at_least_one_pct:.1f}% of SPs provide at least basic compliance",
            file=sys.stderr,
        )
        print(
            f"  • {sp_both_pct:.1f}% of SPs achieve full compliance with both requirements",
            file=sys.stderr,
        )

    # IdP insights
    if total_idps > 0:
        print(
            f"  • {idp_security_pct:.1f}% of IdPs have security contacts (IdPs don't use privacy statements)",
            file=sys.stderr,
        )
        print(
            f"  • Security contact coverage is higher for SPs ({sp_security_pct:.1f}%) than IdPs ({idp_security_pct:.1f}%)",
            file=sys.stderr,
        )

    print("", file=sys.stderr)


def main() -> None:
    """Main function to orchestrate the analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze eduGAIN metadata for privacy statements and security contacts"
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
        "--summary-only", action="store_true", help="Show only summary statistics"
    )

    # Filter options (mutually exclusive)
    filter_group = parser.add_mutually_exclusive_group()
    filter_group.add_argument(
        "--missing-privacy",
        action="store_true",
        help="Show only entities without privacy statement URLs",
    )
    filter_group.add_argument(
        "--missing-security",
        action="store_true",
        help="Show only entities without security contacts",
    )
    filter_group.add_argument(
        "--missing-both",
        action="store_true",
        help="Show only entities missing both privacy statements and security contacts",
    )

    args = parser.parse_args()

    # Get metadata
    if args.local_file:
        root = parse_metadata(None, args.local_file)
    else:
        xml_content = download_metadata(args.url)
        root = parse_metadata(xml_content)

    # Analyze entities
    entities_list, stats = analyze_privacy_security(root)

    # Print summary statistics
    print_summary(stats)

    # Exit early if only summary requested
    if args.summary_only:
        return

    # Apply filters
    if args.missing_privacy:
        entities_list = filter_entities(entities_list, "missing_privacy")
    elif args.missing_security:
        entities_list = filter_entities(entities_list, "missing_security")
    elif args.missing_both:
        entities_list = filter_entities(entities_list, "missing_both")

    # Output CSV results
    writer = csv.writer(sys.stdout)
    if not args.no_headers:
        writer.writerow(
            [
                "RegistrationAuthority",
                "EntityType",
                "OrganizationName",
                "EntityID",
                "HasPrivacyStatement",
                "PrivacyStatementURL",
                "HasSecurityContact",
            ]
        )
    writer.writerows(entities_list)


if __name__ == "__main__":
    main()
