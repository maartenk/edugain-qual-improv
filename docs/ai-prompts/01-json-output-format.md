# AI Implementation Prompt: JSON Output Format

**Feature ID**: 1.6 from ROADMAP.md
**Priority**: HIGH
**Effort**: 2 days
**Type**: Report

## Objective

Add machine-readable JSON output format to `edugain-analyze` CLI, enabling CI/CD integration and programmatic access to analysis results.

## Context

**Current State**:
- Tool outputs human-readable formats only: terminal summary, CSV, markdown
- No structured API-friendly output format
- Automation requires parsing CSV or markdown (brittle)

**Problem**:
- CI/CD pipelines can't easily extract specific metrics
- Monitoring systems can't consume results programmatically
- Integration with dashboards requires custom parsing

**Use Cases**:
```bash
# Extract specific metrics in CI/CD
edugain-analyze --json | jq '.summary.sps_missing_privacy'

# Monitoring and alerting
edugain-analyze --json | jq '.summary.privacy_coverage_percent < 80'

# Dashboard integration
curl -s api.example.com/edugain-stats | jq '.federations.InCommon'
```

## Requirements

### Core Functionality

1. **New CLI Flag**: `--json`
   - Output complete analysis results as JSON to stdout
   - Mutually exclusive with `--report`, `--csv` (validation error if combined)
   - Compatible with `--validate` and `--source` flags

2. **Optional Flag**: `--json-compact`
   - Single-line compact JSON (no pretty-printing)
   - For streaming/logging scenarios

3. **JSON Structure**:
```json
{
  "metadata": {
    "timestamp": "2026-01-18T12:00:00Z",
    "tool_version": "2.5.0",
    "data_source": "https://mds.edugain.org/edugain-v2.xml",
    "cache_age_hours": 2.3,
    "validation_enabled": false
  },
  "summary": {
    "total_entities": 10234,
    "total_sps": 6145,
    "total_idps": 4089,
    "sps_with_privacy": 4280,
    "sps_missing_privacy": 1865,
    "privacy_coverage_percent": 69.6,
    "entities_with_security": 5678,
    "entities_missing_security": 4556,
    "security_coverage_percent": 55.5,
    "entities_with_sirtfi": 4623,
    "entities_missing_sirtfi": 5611,
    "sirtfi_coverage_percent": 45.2
  },
  "federations": {
    "InCommon": {
      "total_entities": 3450,
      "total_sps": 2100,
      "total_idps": 1350,
      "sps_with_privacy": 1890,
      "sps_missing_privacy": 210,
      "privacy_coverage_percent": 90.0,
      "entities_with_security": 2760,
      "security_coverage_percent": 80.0,
      "entities_with_sirtfi": 1552,
      "sirtfi_coverage_percent": 45.0
    }
  },
  "validation_results": {
    "total_urls_checked": 2683,
    "urls_accessible": 2267,
    "urls_broken": 416,
    "accessibility_percent": 84.5
  }
}
```

### Implementation Details

**Files to Modify**:

1. **`src/edugain_analysis/cli/main.py`**:
   - Add `--json` and `--json-compact` arguments
   - Add validation: mutually exclusive with `--report`, `--csv`
   - Call new JSON formatter after analysis complete

2. **`src/edugain_analysis/formatters/base.py`** (or new `json.py`):
   - Create `format_json_output(stats, federation_stats, metadata)` function
   - Include metadata: timestamp (ISO 8601), tool version, data source, cache age
   - Calculate percentages for all coverage metrics
   - Handle validation results if `--validate` was used
   - Support compact mode (no indentation)

3. **Version Detection**:
   - Add `__version__` to `src/edugain_analysis/__init__.py`
   - Use in JSON metadata section

**Edge Cases**:
- Empty metadata (0 entities): Return valid JSON with zeros
- Cache miss: Set `cache_age_hours` to null
- No validation: Omit `validation_results` section entirely
- Division by zero: Handle 0 total_sps gracefully (return 0.0 percent)

## Acceptance Criteria

### Functional Requirements
- [ ] `edugain-analyze --json` outputs valid JSON to stdout
- [ ] JSON includes all summary statistics from current text output
- [ ] Federation breakdown included with all federations
- [ ] `--json-compact` produces single-line output
- [ ] Validation results included when `--validate` flag used
- [ ] Tool version and timestamp in metadata section
- [ ] Percentages calculated and included (not just raw counts)

### Quality Requirements
- [ ] JSON is valid (parseable by `jq`, `json.loads()`)
- [ ] Schema is consistent (same keys every run)
- [ ] Null values used for missing data (not absent keys)
- [ ] Exit code 0 on success, non-zero on error
- [ ] Error messages go to stderr, not stdout
- [ ] No extraneous output to stdout (only JSON)

### Testing Requirements
- [ ] Unit test: `test_format_json_output()` in `tests/unit/test_formatters.py`
- [ ] Integration test: `test_cli_json_flag()` in `tests/unit/test_cli_main.py`
- [ ] Test compact mode produces single line
- [ ] Test mutually exclusive flags raise error
- [ ] Test validation results included when `--validate` used
- [ ] Test empty metadata scenario (0 entities)

## Testing Strategy

**Unit Tests**:
```python
def test_format_json_output_basic():
    """Test JSON formatter with basic stats."""
    stats = {
        "total_entities": 100,
        "total_sps": 60,
        "total_idps": 40,
        "sps_has_privacy": 45,
        "sps_missing_privacy": 15,
        # ... etc
    }
    result = format_json_output(stats, {}, {})
    parsed = json.loads(result)
    assert parsed["summary"]["total_entities"] == 100
    assert parsed["summary"]["privacy_coverage_percent"] == 75.0
```

**Integration Tests**:
```python
@patch("edugain_analysis.core.metadata.get_metadata")
def test_cli_json_output(mock_metadata, sample_metadata):
    """Test --json flag produces valid JSON."""
    mock_metadata.return_value = sample_metadata
    result = subprocess.run(
        ["edugain-analyze", "--json"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "metadata" in data
    assert "summary" in data
```

## Implementation Guidance

### Step 1: Add Version Info
```python
# src/edugain_analysis/__init__.py
__version__ = "2.5.0"
```

### Step 2: Create JSON Formatter
```python
# src/edugain_analysis/formatters/base.py
import json
from datetime import datetime, timezone
from .. import __version__

def format_json_output(
    stats: dict,
    federation_stats: dict,
    metadata_info: dict | None = None,
    compact: bool = False
) -> str:
    """
    Format analysis results as JSON.

    Args:
        stats: Summary statistics dictionary
        federation_stats: Per-federation statistics
        metadata_info: Metadata (cache age, source URL, etc.)
        compact: If True, output single-line JSON

    Returns:
        JSON string
    """
    output = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_version": __version__,
            "data_source": metadata_info.get("source", "unknown"),
            "cache_age_hours": metadata_info.get("cache_age_hours"),
            "validation_enabled": metadata_info.get("validation_enabled", False)
        },
        "summary": {
            "total_entities": stats["total_entities"],
            # ... calculate percentages
            "privacy_coverage_percent": round(
                (stats["sps_has_privacy"] / stats["total_sps"] * 100)
                if stats["total_sps"] > 0 else 0.0,
                1
            ),
            # ... etc
        },
        "federations": {
            # Transform federation_stats to nested dict
        }
    }

    # Include validation results if present
    if "validation_results" in stats:
        output["validation_results"] = stats["validation_results"]

    indent = None if compact else 2
    return json.dumps(output, indent=indent, ensure_ascii=False)
```

### Step 3: Update CLI
```python
# src/edugain_analysis/cli/main.py

# Add arguments
parser.add_argument(
    "--json",
    action="store_true",
    help="Output results as JSON (machine-readable)"
)
parser.add_argument(
    "--json-compact",
    action="store_true",
    help="Output compact single-line JSON"
)

# Validate mutually exclusive
if args.json and (args.report or args.csv):
    print("Error: --json cannot be combined with --report or --csv", file=sys.stderr)
    sys.exit(1)

# After analysis, check for JSON output
if args.json or args.json_compact:
    from ..formatters.base import format_json_output
    metadata_info = {
        "source": args.source or EDUGAIN_METADATA_URL,
        "cache_age_hours": calculate_cache_age(),  # implement helper
        "validation_enabled": args.validate
    }
    json_output = format_json_output(
        stats,
        federation_stats,
        metadata_info,
        compact=args.json_compact
    )
    print(json_output)
    return
```

## Success Metrics

- JSON output validates against schema
- No breaking changes to existing CLI behavior
- All existing tests still pass
- New tests achieve 100% coverage of JSON formatter
- Documentation updated in README.md

## References

- Current summary output: `src/edugain_analysis/formatters/base.py:print_summary()`
- Current CLI: `src/edugain_analysis/cli/main.py:main()`
- Statistics calculation: `src/edugain_analysis/core/analysis.py:analyze_privacy_security()`
