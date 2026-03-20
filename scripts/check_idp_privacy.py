#!/usr/bin/env python3
"""
Quick analysis script to check IdP privacy statement coverage.

This script reuses the existing metadata parser to count how many IdPs
have privacy statements, both overall and per federation.
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

# Add src to path to import from the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edugain_analysis.core.entities import iter_entity_records
from edugain_analysis.core.metadata import get_metadata, parse_metadata


def analyze_idp_privacy(entities):
    """Analyze IdP privacy statement coverage."""
    # Overall statistics
    total_idps = 0
    idps_with_privacy = 0
    total_sps = 0
    sps_with_privacy = 0

    # Per-federation statistics
    federation_stats = defaultdict(lambda: {"total": 0, "with_privacy": 0})

    for entity in entities:
        if entity.is_idp:
            total_idps += 1
            if entity.has_privacy:
                idps_with_privacy += 1

            # Track per-federation
            federation_stats[entity.federation_name]["total"] += 1
            if entity.has_privacy:
                federation_stats[entity.federation_name]["with_privacy"] += 1

        # Also track SP stats for comparison
        if entity.is_sp:
            total_sps += 1
            if entity.has_privacy:
                sps_with_privacy += 1

    return {
        "total_idps": total_idps,
        "idps_with_privacy": idps_with_privacy,
        "idps_without_privacy": total_idps - idps_with_privacy,
        "total_sps": total_sps,
        "sps_with_privacy": sps_with_privacy,
        "federation_stats": dict(federation_stats),
    }


def print_summary(stats):
    """Print human-readable summary."""
    total_idps = stats["total_idps"]
    idps_with = stats["idps_with_privacy"]
    idps_without = stats["idps_without_privacy"]

    total_sps = stats["total_sps"]
    sps_with = stats["sps_with_privacy"]

    print("\n" + "=" * 70)
    print("📊 IdP Privacy Statement Coverage Analysis")
    print("=" * 70)

    print("\n🔍 Overall Statistics:")
    print(f"  Total IdPs: {total_idps:,}")
    print(
        f"  IdPs with privacy statements: {idps_with:,} ({idps_with/total_idps*100:.1f}%)"
    )
    print(
        f"  IdPs without privacy statements: {idps_without:,} ({idps_without/total_idps*100:.1f}%)"
    )

    print("\n📊 Comparison with SPs:")
    print(f"  Total SPs: {total_sps:,}")
    print(
        f"  SPs with privacy statements: {sps_with:,} ({sps_with/total_sps*100:.1f}%)"
    )
    print(f"  \n  → IdP coverage: {idps_with/total_idps*100:.1f}%")
    print(f"  → SP coverage:  {sps_with/total_sps*100:.1f}%")
    print(
        f"  → Difference: {abs(sps_with/total_sps*100 - idps_with/total_idps*100):.1f} percentage points"
    )

    # Federation breakdown
    federation_stats = stats["federation_stats"]

    # Calculate percentages and sort
    fed_list = []
    for fed_name, fed_data in federation_stats.items():
        total = fed_data["total"]
        with_privacy = fed_data["with_privacy"]
        percentage = (with_privacy / total * 100) if total > 0 else 0
        fed_list.append(
            {
                "name": fed_name,
                "total": total,
                "with_privacy": with_privacy,
                "percentage": percentage,
            }
        )

    # Sort by percentage descending
    fed_list.sort(key=lambda x: x["percentage"], reverse=True)

    print("\n🏆 Top 10 Federations by IdP Privacy Coverage:")
    for i, fed in enumerate(fed_list[:10], 1):
        print(
            f"  {i:2d}. {fed['name'][:45]:45s} {fed['with_privacy']:4d}/{fed['total']:4d} ({fed['percentage']:5.1f}%)"
        )

    print("\n⚠️  Bottom 10 Federations by IdP Privacy Coverage:")
    for i, fed in enumerate(fed_list[-10:][::-1], 1):
        print(
            f"  {i:2d}. {fed['name'][:45]:45s} {fed['with_privacy']:4d}/{fed['total']:4d} ({fed['percentage']:5.1f}%)"
        )

    print("\n" + "=" * 70)


def export_csv(stats, output_file):
    """Export per-federation statistics to CSV."""
    federation_stats = stats["federation_stats"]

    # Prepare data
    rows = []
    for fed_name, fed_data in federation_stats.items():
        total = fed_data["total"]
        with_privacy = fed_data["with_privacy"]
        without_privacy = total - with_privacy
        percentage = (with_privacy / total * 100) if total > 0 else 0

        rows.append(
            {
                "Federation": fed_name,
                "Total IdPs": total,
                "IdPs with Privacy": with_privacy,
                "IdPs without Privacy": without_privacy,
                "Coverage %": f"{percentage:.1f}",
            }
        )

    # Sort by percentage descending
    rows.sort(key=lambda x: float(x["Coverage %"]), reverse=True)

    # Write CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Federation",
                "Total IdPs",
                "IdPs with Privacy",
                "IdPs without Privacy",
                "Coverage %",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ CSV exported to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze IdP privacy statement coverage (overall and per federation)"
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Path to local metadata XML file or URL (default: fetches from eduGAIN)",
    )
    parser.add_argument(
        "--csv",
        metavar="OUTPUT_FILE",
        help="Export per-federation statistics to CSV file",
    )

    args = parser.parse_args()

    # Fetch and parse metadata
    print("📡 Fetching and parsing metadata...", end="", flush=True)
    try:
        if args.source:
            # Local file or custom URL
            root = parse_metadata(local_file=args.source)
        else:
            # Default eduGAIN metadata
            metadata_content = get_metadata()
            root = parse_metadata(content=metadata_content)
        print(" ✅")
    except Exception as e:
        print(f" ❌\nError: {e}", file=sys.stderr)
        return 1

    # Extract entities
    print("📋 Extracting entities...", end="", flush=True)
    try:
        entities = list(iter_entity_records(root))
        print(f" ✅ ({len(entities):,} entities)")
    except Exception as e:
        print(f" ❌\nError extracting entities: {e}", file=sys.stderr)
        return 1

    # Analyze
    print("📊 Analyzing IdP privacy coverage...", end="", flush=True)
    stats = analyze_idp_privacy(entities)
    print(" ✅")

    # Print summary
    print_summary(stats)

    # Export CSV if requested
    if args.csv:
        export_csv(stats, args.csv)

    return 0


if __name__ == "__main__":
    sys.exit(main())
