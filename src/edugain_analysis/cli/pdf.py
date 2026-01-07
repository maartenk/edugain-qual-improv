"""
PDF output handler for the CLI.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


def _report_context(args) -> str:
    if args.report_with_validation:
        return "Detailed report with URL validation"
    if args.report:
        return "Detailed report"
    if args.validate:
        return "Summary with URL validation"
    return "Summary"


def handle_pdf_output(
    args,
    stats: dict,
    federation_stats: dict,
    include_validation: bool,
) -> None:
    from ..formatters.pdf import generate_pdf_report

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    default_path = Path("reports") / f"edugain-report-{timestamp}.pdf"
    output_path = args.output or str(default_path)

    pdf_path = generate_pdf_report(
        stats,
        federation_stats,
        output_path,
        _report_context(args),
        include_validation=include_validation,
    )
    print(f"PDF report written to {pdf_path}", file=sys.stderr)
