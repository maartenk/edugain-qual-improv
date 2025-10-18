"""CLI helper to copy the AI implementation prompt."""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import TextIO

PROMPT_PATH = pathlib.Path(__file__).resolve().parents[3] / "AI_IMPLEMENTATION_PROMPT.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy the AI implementation prompt to a destination file or stdout.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=pathlib.Path,
        help="Destination file. Defaults to stdout when omitted.",
    )
    return parser.parse_args()


def open_destination(path: pathlib.Path | None) -> TextIO:
    if path is None or str(path) == "-":
        return sys.stdout
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("w", encoding="utf-8")


def main() -> int:
    if not PROMPT_PATH.exists():
        raise SystemExit(f"Prompt file not found at {PROMPT_PATH}")

    args = parse_args()
    destination = open_destination(args.output)

    with PROMPT_PATH.open("r", encoding="utf-8") as source:
        contents = source.read()

    try:
        destination.write(contents)
    finally:
        if destination is not sys.stdout:
            destination.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
