#!/bin/bash
# Development linting script

set -e

echo "Running ruff check..."
ruff check src/ tests/

echo "Running ruff format check..."
ruff format --check src/ tests/

echo "All linting checks passed!"
