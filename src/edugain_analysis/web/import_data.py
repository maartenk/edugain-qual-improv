"""Utility to import analysis data into web database.

TODO: This is a placeholder for data import functionality.
The actual implementation should:
1. Run the eduGAIN analysis (or use existing analysis module)
2. Save results to the web application database
3. Support scheduled/cron job execution

Usage:
    python -m edugain_analysis.web.import_data
    python -m edugain_analysis.web.import_data --days-history 30
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

from ..core.analysis import analyze_privacy_security
from ..core.metadata import get_federation_mapping, get_metadata, parse_metadata
from .models import Federation, Snapshot, SessionLocal


def import_snapshot():
    """Run analysis and import results into database."""
    print("📊 Running eduGAIN analysis...")

    try:
        # Get metadata
        print("  → Downloading metadata...")
        xml_content = get_metadata()
        root = parse_metadata(xml_content)

        # Get federation mapping
        print("  → Fetching federation names...")
        federation_mapping = get_federation_mapping()

        # Run analysis
        print("  → Analyzing entities...")
        entities_list, stats, federation_stats = analyze_privacy_security(
            root, federation_mapping, validate_urls=False
        )

        # Save to database
        print("  → Saving to database...")
        db = SessionLocal()
        try:
            # Create snapshot
            snapshot = Snapshot(
                timestamp=datetime.now(),
                total_entities=stats["total_entities"],
                total_sps=stats["total_sps"],
                total_idps=stats["total_idps"],
                sps_with_privacy=stats["sps_has_privacy"],
                sps_missing_privacy=stats["sps_missing_privacy"],
                sps_has_security=stats["sps_has_security"],
                idps_has_security=stats["idps_has_security"],
                coverage_pct=stats["sps_has_privacy"] / stats["total_sps"] * 100
                if stats["total_sps"] > 0
                else 0,
            )
            db.add(snapshot)
            db.flush()  # Get snapshot ID

            # Create federation records
            for fed_name, fed_stats in federation_stats.items():
                federation = Federation(
                    snapshot_id=snapshot.id,
                    name=fed_name,
                    total_entities=fed_stats["total_entities"],
                    total_sps=fed_stats["total_sps"],
                    total_idps=fed_stats["total_idps"],
                    sps_with_privacy=fed_stats["sps_has_privacy"],
                    sps_has_security=fed_stats["sps_has_security"],
                    idps_has_security=fed_stats["idps_has_security"],
                    coverage_pct=fed_stats["sps_has_privacy"]
                    / fed_stats["total_sps"]
                    * 100
                    if fed_stats["total_sps"] > 0
                    else 0,
                )
                db.add(federation)

            db.commit()
            print(
                f"✅ Successfully imported snapshot with {len(federation_stats)} federations"
            )
            print(f"   Total entities: {stats['total_entities']}")
            print(f"   Coverage: {snapshot.coverage_pct:.1f}%")

        except Exception as e:
            db.rollback()
            print(f"❌ Error saving to database: {e}", file=sys.stderr)
            raise
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error during import: {e}", file=sys.stderr)
        sys.exit(1)


def generate_test_data(days: int = 30):
    """Generate test data for development/demo purposes.

    Creates synthetic snapshots for the last N days to demonstrate trends.
    """
    print(f"🧪 Generating test data for last {days} days...")

    import random

    db = SessionLocal()
    try:
        base_coverage = 70.0
        base_entities = 5000

        for day in range(days, 0, -1):
            timestamp = datetime.now() - timedelta(days=day)

            # Add some variance
            coverage_variance = random.uniform(-5, 5)
            coverage = max(50, min(90, base_coverage + coverage_variance))

            entities_variance = random.randint(-200, 200)
            total_entities = base_entities + entities_variance

            total_sps = int(total_entities * 0.7)
            total_idps = total_entities - total_sps
            sps_with_privacy = int(total_sps * (coverage / 100))

            # Create snapshot
            snapshot = Snapshot(
                timestamp=timestamp,
                total_entities=total_entities,
                total_sps=total_sps,
                total_idps=total_idps,
                sps_with_privacy=sps_with_privacy,
                sps_missing_privacy=total_sps - sps_with_privacy,
                sps_has_security=int(total_sps * 0.65),
                idps_has_security=int(total_idps * 0.80),
                coverage_pct=coverage,
            )
            db.add(snapshot)
            db.flush()

            # Add a few test federations
            test_federations = [
                ("InCommon", 0.85, 1500),
                ("DFN-AAI", 0.72, 800),
                ("HAKA", 0.68, 500),
                ("eduGAIN.org", 0.55, 300),
            ]

            for fed_name, fed_coverage, fed_entities in test_federations:
                fed_sps = int(fed_entities * 0.7)
                fed_idps = fed_entities - fed_sps

                federation = Federation(
                    snapshot_id=snapshot.id,
                    name=fed_name,
                    total_entities=fed_entities,
                    total_sps=fed_sps,
                    total_idps=fed_idps,
                    sps_with_privacy=int(fed_sps * fed_coverage),
                    sps_has_security=int(fed_sps * 0.65),
                    idps_has_security=int(fed_idps * 0.80),
                    coverage_pct=fed_coverage * 100,
                )
                db.add(federation)

        db.commit()
        print(f"✅ Successfully generated {days} days of test data")

    except Exception as e:
        db.rollback()
        print(f"❌ Error generating test data: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Import eduGAIN analysis data into web database"
    )
    parser.add_argument(
        "--test-data",
        action="store_true",
        help="Generate test data instead of real analysis",
    )
    parser.add_argument(
        "--days", type=int, default=30, help="Days of test data to generate"
    )

    args = parser.parse_args()

    if args.test_data:
        generate_test_data(args.days)
    else:
        import_snapshot()


if __name__ == "__main__":
    main()
