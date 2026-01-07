"""
Command-line interface for eduGAIN quality analysis.

Provides a streamlined CLI for analyzing eduGAIN metadata and generating
various output formats including summaries, reports, and CSV exports.
"""

import argparse
import csv
import sys

from ..config import EDUGAIN_METADATA_URL, URL_VALIDATION_THREADS
from ..core import (
    analyze_privacy_security,
    filter_entities,
    get_federation_mapping,
    get_metadata,
    load_url_validation_cache,
    parse_metadata,
    save_url_validation_cache,
)
from ..formatters import (
    export_federation_csv,
    print_federation_summary,
    print_summary,
    print_summary_markdown,
)
from .pdf import handle_pdf_output


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Analyze eduGAIN metadata for privacy statements, security contacts, and SIRTFI certification. Default: shows summary statistics.",
        epilog="""
Examples:
  %(prog)s                              # Show summary statistics (includes SIRTFI)
  %(prog)s --report                     # Generate detailed markdown report
  %(prog)s --report-with-validation     # Generate detailed report with URL validation
  %(prog)s --report --pdf               # Generate graphical PDF report
  %(prog)s --report --pdf --output reports/edugain-report.pdf
  %(prog)s --csv entities               # Export all entities to CSV (includes SIRTFI column)
  %(prog)s --csv federations            # Export federation statistics (includes SIRTFI stats)
  %(prog)s --csv missing-privacy        # Export only SPs missing privacy statements
  %(prog)s --csv missing-security       # Export only entities missing security contacts
  %(prog)s --csv missing-both           # Export only SPs missing both privacy and security
  %(prog)s --csv urls                   # Export basic URL list (SPs with privacy statements)
  %(prog)s --csv urls-validated         # Export URL validation results (enables validation)
  %(prog)s --validate                   # Enable URL validation with summary
  %(prog)s --source metadata.xml        # Use local XML file
  %(prog)s --source https://custom.url  # Use custom metadata URL

CSV Columns (entities):
  Federation, EntityType, OrganizationName, EntityID, HasPrivacyStatement,
  PrivacyStatementURL, HasSecurityContact, HasSIRTFI

  With --validate: Also includes URLStatusCode, FinalURL, URLAccessible,
                   RedirectCount, ValidationError
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Data source options (unified)
    parser.add_argument(
        "--source",
        help="Local XML file path or custom metadata URL (default: eduGAIN metadata URL)",
    )

    # Output format options (mutually exclusive)
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--csv",
        choices=[
            "entities",
            "federations",
            "missing-privacy",
            "missing-security",
            "missing-both",
            "urls",
            "urls-validated",
        ],
        help=(
            "Export CSV data (includes SIRTFI column). "
            "Choices: entities (all), federations (stats), "
            "missing-privacy/security/both (filtered), "
            "urls (basic list), urls-validated (with validation)"
        ),
    )
    output_group.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed markdown report with privacy, security, and SIRTFI coverage by federation",
    )
    output_group.add_argument(
        "--report-with-validation",
        action="store_true",
        help="Generate detailed markdown report with URL validation (checks privacy statement URLs)",
    )
    output_group.add_argument(
        "--validate",
        action="store_true",
        help="Enable URL validation (checks privacy statement accessibility) and show summary statistics",
    )

    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Generate a graphical PDF report (summary + federation pages)",
    )
    parser.add_argument(
        "--output",
        help=(
            "Output file path for --pdf "
            "(default: reports/edugain-report-YYYYMMDD-HHMMSS.pdf)"
        ),
    )

    # CSV output options
    parser.add_argument(
        "--no-headers", action="store_true", help="Omit CSV headers from output"
    )

    return parser


def handle_csv_export(args, entities_list, stats, federation_stats):
    """Handle CSV export based on the specified type."""
    if args.csv == "federations":
        export_federation_csv(federation_stats, not args.no_headers)
        return

    # Handle entity CSV exports
    if args.csv == "entities":
        pass  # Use all entities
    elif args.csv == "missing-privacy":
        entities_list = filter_entities(entities_list, "missing_privacy")
    elif args.csv == "missing-security":
        entities_list = filter_entities(entities_list, "missing_security")
    elif args.csv == "missing-both":
        entities_list = filter_entities(entities_list, "missing_both")
    elif args.csv == "urls":
        # Basic URLs CSV should only include entities with privacy statements (SPs with URLs)
        entities_list = [e for e in entities_list if e[4] == "Yes"]
    elif args.csv == "urls-validated":
        # Validated URLs CSV should only include entities with privacy statements (SPs with URLs)
        entities_list = [e for e in entities_list if e[4] == "Yes"]

    # Output entity CSV
    writer = csv.writer(sys.stdout)
    if not args.no_headers:
        headers = [
            "Federation",
            "EntityType",
            "OrganizationName",
            "EntityID",
            "HasPrivacyStatement",
            "PrivacyStatementURL",
            "HasSecurityContact",
            "HasSIRTFI",
        ]

        # Add URL validation headers if validation was enabled
        if stats.get("validation_enabled", False):
            headers.extend(
                [
                    "URLStatusCode",
                    "FinalURL",
                    "URLAccessible",
                    "RedirectCount",
                    "ValidationError",
                ]
            )

        writer.writerow(headers)
    writer.writerows(entities_list)


def main() -> None:
    """Main function to orchestrate the analysis."""
    parser = setup_argument_parser()
    args = parser.parse_args()

    if args.output and not args.pdf:
        parser.error("--output is only supported with --pdf")
    if args.pdf and args.csv:
        parser.error("--pdf cannot be used with --csv")

    try:
        # Determine if URL validation should be enabled
        enable_validation = (
            args.validate
            or args.report_with_validation
            or (args.csv == "urls-validated")
        )

        # Determine data source (unified source handling)
        if args.source:
            # Check if source is a URL (starts with http) or a file path
            if args.source.startswith(("http://", "https://")):
                xml_content = get_metadata(args.source)
                root = parse_metadata(xml_content)
            else:
                root = parse_metadata(None, args.source)
        else:
            # Use default eduGAIN metadata URL
            xml_content = get_metadata(EDUGAIN_METADATA_URL)
            root = parse_metadata(xml_content)

        # Get federation name mapping
        federation_mapping = get_federation_mapping()

        # Load URL validation cache if validation is enabled
        validation_cache = None
        if enable_validation:
            validation_cache = load_url_validation_cache() or {}
            if validation_cache:
                print(
                    f"Loaded {len(validation_cache)} cached URL validation results",
                    file=sys.stderr,
                )

        # Analyze entities
        entities_list, stats, federation_stats = analyze_privacy_security(
            root,
            federation_mapping,
            enable_validation,
            validation_cache,
            URL_VALIDATION_THREADS,
        )

        # Save updated URL validation cache if validation was performed
        if enable_validation and validation_cache is not None:
            urls_validated = stats.get("urls_checked", 0)
            if urls_validated > 0:
                print(
                    f"Saving URL validation cache with {len(validation_cache)} entries",
                    file=sys.stderr,
                )
                save_url_validation_cache(validation_cache)

        # Handle different output formats
        if args.pdf:
            handle_pdf_output(args, stats, federation_stats, enable_validation)
        elif args.csv:
            handle_csv_export(args, entities_list, stats, federation_stats)
        elif args.report or args.report_with_validation:
            print_summary_markdown(stats, output_file=sys.stdout)
            print_federation_summary(federation_stats, output_file=sys.stdout)
        else:
            # Default: show summary statistics (includes validation results if enabled)
            print_summary(stats)

    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
