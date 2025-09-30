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
from ..core.validation import validate_urls_parallel
from .models import Entity, Federation, Snapshot, SessionLocal, URLValidation


def import_snapshot(validate_urls: bool = False):
    """Run analysis and import results into database.

    Args:
        validate_urls: If True, validate privacy statement URLs
    """
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

        # Validate URLs if requested
        url_validation_results = {}
        if validate_urls:
            print("  → Validating privacy statement URLs...")
            # Collect URLs to validate
            urls_to_validate = {}
            for entity in entities_list:
                if entity.get("PrivacyStatementURL"):
                    urls_to_validate[entity["EntityID"]] = entity["PrivacyStatementURL"]

            if urls_to_validate:
                # Run validation
                url_validation_results = validate_urls_parallel(
                    list(urls_to_validate.values()), cache={}
                )
                print(f"     Validated {len(url_validation_results)} URLs")

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

            # Create federation records and map federation IDs
            federation_id_map = {}
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
                db.flush()  # Get federation ID
                federation_id_map[fed_name] = federation.id

            # Create entity records
            # entities_list is a list of lists with format:
            # [Federation, EntityType, OrgName, EntityID, HasPrivacy, PrivacyURL, HasSecurity]
            # or with validation:
            # [Federation, EntityType, OrgName, EntityID, HasPrivacy, PrivacyURL, HasSecurity,
            #  StatusCode, FinalURL, Accessible, RedirectCount, ValidationError]
            entity_id_map = {}
            for entity_row in entities_list:
                if validate_urls:
                    # Extended format with validation
                    (
                        federation_name,
                        entity_type,
                        org_name,
                        entity_id,
                        has_privacy,
                        privacy_url,
                        has_security,
                        status_code,
                        final_url,
                        accessible,
                        redirect_count,
                        validation_error,
                    ) = entity_row
                else:
                    # Standard format without validation
                    (
                        federation_name,
                        entity_type,
                        org_name,
                        entity_id,
                        has_privacy,
                        privacy_url,
                        has_security,
                    ) = entity_row
                    status_code = (
                        final_url
                    ) = accessible = redirect_count = validation_error = None

                federation_id = federation_id_map.get(federation_name)

                # Convert Yes/No to boolean
                has_privacy_bool = has_privacy == "Yes"
                has_security_bool = has_security == "Yes"

                entity = Entity(
                    snapshot_id=snapshot.id,
                    federation_id=federation_id,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    organization_name=org_name if org_name else None,
                    has_privacy_statement=has_privacy_bool,
                    privacy_statement_url=privacy_url if privacy_url else None,
                    has_security_contact=has_security_bool,
                )
                db.add(entity)
                db.flush()  # Get entity ID
                entity_id_map[entity_id] = entity.id

                # Add URL validation results if available
                if validate_urls and privacy_url and status_code:
                    # Convert accessible Yes/No to boolean
                    accessible_bool = accessible == "Yes" if accessible else False

                    # Parse status code and redirect count
                    try:
                        status_code_int = (
                            int(status_code)
                            if status_code and status_code != "Not Checked"
                            else None
                        )
                    except (ValueError, TypeError):
                        status_code_int = None

                    try:
                        redirect_count_int = (
                            int(redirect_count)
                            if redirect_count and redirect_count != "Not Checked"
                            else 0
                        )
                    except (ValueError, TypeError):
                        redirect_count_int = 0

                    url_validation = URLValidation(
                        entity_id=entity.id,
                        url=privacy_url,
                        status_code=status_code_int,
                        final_url=final_url
                        if final_url and final_url != privacy_url
                        else None,
                        accessible=accessible_bool,
                        redirect_count=redirect_count_int,
                        validation_error=validation_error if validation_error else None,
                        validated_at=datetime.now(),
                    )
                    db.add(url_validation)

            db.commit()
            print(
                f"✅ Successfully imported snapshot with {len(federation_stats)} federations and {len(entities_list)} entities"
            )
            print(f"   Total entities: {stats['total_entities']}")
            print(f"   Coverage: {snapshot.coverage_pct:.1f}%")
            if validate_urls:
                print(f"   URL validations: {len(url_validation_results)}")

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
    parser.add_argument(
        "--validate-urls",
        action="store_true",
        help="Validate privacy statement URLs (slower)",
    )

    args = parser.parse_args()

    if args.test_data:
        generate_test_data(args.days)
    else:
        import_snapshot(validate_urls=args.validate_urls)


if __name__ == "__main__":
    main()
