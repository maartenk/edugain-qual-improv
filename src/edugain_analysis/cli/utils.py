"""
Utility helpers for CLI entry points.

Provides shared logic for loading metadata (local file or remote URL)
and emitting CSV output, so individual CLI scripts can focus on their
domain-specific filtering.
"""

from __future__ import annotations

import csv
import sys
from collections.abc import Callable, Iterable, Sequence
from xml.etree import ElementTree as ET

from ..core import get_metadata, parse_metadata

CliRows = Iterable[Sequence[str | None]]


def load_metadata_for_cli(
    local_file: str | None,
    url: str | None,
    default_url: str,
    timeout: int,
) -> ET.Element:
    """
    Load metadata for CLI usage, honouring local file overrides.

    Args:
        local_file: Optional path to a local XML file.
        url: Optional remote URL override.
        default_url: Fallback metadata URL.
        timeout: HTTP timeout when downloading.

    Returns:
        Parsed ElementTree root element.
    """
    if local_file:
        return parse_metadata(None, local_file)

    target_url = url or default_url
    xml_content = get_metadata(target_url, timeout)
    return parse_metadata(xml_content)


def run_csv_cli(
    rows_factory: Callable[[ET.Element], CliRows],
    headers: Sequence[str],
    *,
    local_file: str | None,
    url: str | None,
    default_url: str,
    timeout: int,
    include_headers: bool,
    error_label: str,
) -> None:
    """
    Common CSV CLI runner: load metadata, build rows, stream to stdout.

    Args:
        rows_factory: Callable that converts the metadata root into CSV rows.
        headers: CSV header row.
        local_file: Optional local file path override.
        url: Optional metadata URL override.
        default_url: Default metadata URL.
        timeout: HTTP timeout in seconds.
        include_headers: Whether to emit CSV headers.
        error_label: Human readable label used in error messages.
    """
    try:
        root = load_metadata_for_cli(local_file, url, default_url, timeout)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Error loading metadata for {error_label}: {exc}", file=sys.stderr)
        sys.exit(1)
        return

    rows = rows_factory(root)

    writer = csv.writer(sys.stdout)
    if include_headers:
        writer.writerow(headers)
    writer.writerows(rows)
