# AI Implementation Prompt: Exit Codes for Quality Thresholds

**Feature ID**: 1.7 from ROADMAP.md
**Priority**: HIGH
**Effort**: 1 day
**Type**: Infrastructure

## Objective

Add support for quality threshold validation with non-zero exit codes, enabling fail-fast behavior in CI/CD pipelines and automated quality gates.

## Context

**Current State**:
- `edugain-analyze` always exits with code 0 (success), regardless of quality metrics
- No built-in way to fail CI/CD pipelines when compliance drops
- Users must parse output and implement custom threshold checking

**Problem**:
- CI/CD pipelines can't catch compliance regressions automatically
- No automated quality gates without custom scripting
- Difficult to enforce minimum quality standards

**Use Cases**:
```bash
# Fail CI/CD if privacy coverage drops below 80%
edugain-analyze --min-privacy-coverage 80 || exit 1

# Enforce multiple thresholds
edugain-analyze \
  --min-privacy-coverage 75 \
  --min-security-coverage 60 \
  --min-sirtfi-coverage 45 \
  || notify_team "Quality threshold not met"

# Block deployment if any privacy URLs are broken
edugain-analyze --validate --fail-on-broken-urls || exit 1

# Pre-commit hook
edugain-analyze --min-privacy-coverage 80 --quiet
```

## Requirements

### Core Functionality

1. **Exit Codes**:
   - `0`: Success (all thresholds met or no thresholds specified)
   - `1`: Quality threshold not met
   - `2`: Validation/processing error (network failure, parse error, etc.)

2. **New CLI Flags**:
   ```bash
   --min-privacy-coverage PERCENT      # Minimum SP privacy coverage (0-100)
   --min-security-coverage PERCENT     # Minimum security contact coverage (0-100)
   --min-sirtfi-coverage PERCENT       # Minimum SIRTFI certification coverage (0-100)
   --fail-on-broken-urls               # Fail if any privacy URLs are broken (requires --validate)
   --quiet                             # Suppress normal output, only show threshold failures
   ```

3. **Behavior**:
   - All specified thresholds must pass (AND logic)
   - Print clear failure reason to stderr before exiting with code 1
   - Still output normal results to stdout (unless `--quiet`)
   - Summary at end: "✅ All thresholds met" or "❌ Thresholds not met"

4. **Error Messages** (to stderr):
   ```
   ❌ Quality threshold not met:
     - Privacy coverage: 68.5% (threshold: 80.0%)
     - SIRTFI coverage: 42.1% (threshold: 45.0%)

   Exit code: 1
   ```

### Implementation Details

**Files to Modify**:

1. **`src/edugain_analysis/cli/main.py`**:
   - Add new argument flags
   - Validate threshold values (0-100)
   - After analysis, check thresholds
   - Print failures to stderr
   - Exit with appropriate code

2. **`src/edugain_analysis/core/analysis.py`** (optional helper):
   - Add `check_quality_thresholds(stats, thresholds)` function
   - Returns list of failures or empty list if all pass

**Edge Cases**:
- `--fail-on-broken-urls` without `--validate`: Error message + exit 2
- Threshold value < 0 or > 100: Error message + exit 2
- Multiple threshold failures: List all failures, not just first
- Zero entities: 0.0% coverage, likely fails most thresholds
- `--quiet` mode: Suppress normal output but show threshold failures

## Acceptance Criteria

### Functional Requirements
- [ ] Exit code 0 when all thresholds met or no thresholds specified
- [ ] Exit code 1 when at least one threshold not met
- [ ] Exit code 2 for processing errors (invalid args, network failures)
- [ ] All threshold flags validate input range (0-100)
- [ ] Multiple thresholds can be specified simultaneously
- [ ] `--fail-on-broken-urls` requires `--validate` (error if not)
- [ ] Failure messages clearly state which thresholds failed
- [ ] `--quiet` suppresses normal output but shows failures

### Quality Requirements
- [ ] Clear, actionable error messages to stderr
- [ ] Normal output still goes to stdout (unless `--quiet`)
- [ ] Threshold checking doesn't impact performance
- [ ] Works with all output formats (CSV, markdown, JSON)
- [ ] Backward compatible: no flags = always exit 0

### Testing Requirements
- [ ] Test exit 0 when no thresholds specified (backward compat)
- [ ] Test exit 1 when privacy coverage below threshold
- [ ] Test exit 1 when multiple thresholds fail
- [ ] Test exit 0 when all thresholds met
- [ ] Test exit 2 for invalid threshold values
- [ ] Test `--fail-on-broken-urls` without `--validate` fails
- [ ] Test `--quiet` mode suppresses normal output
- [ ] Integration test: full CLI run with thresholds

## Testing Strategy

**Unit Tests**:
```python
def test_check_quality_thresholds_all_pass():
    """Test threshold checking when all thresholds met."""
    stats = {
        "total_sps": 100,
        "sps_has_privacy": 85,
        "sps_missing_privacy": 15,
        "total_entities": 200,
        "entities_with_security": 130,
        "entities_with_sirtfi": 100
    }
    thresholds = {
        "min_privacy_coverage": 80.0,
        "min_security_coverage": 60.0,
        "min_sirtfi_coverage": 45.0
    }
    failures = check_quality_thresholds(stats, thresholds)
    assert failures == []

def test_check_quality_thresholds_some_fail():
    """Test threshold checking when some fail."""
    stats = {
        "total_sps": 100,
        "sps_has_privacy": 70,  # 70% < 80%
        "total_entities": 200,
        "entities_with_sirtfi": 80  # 40% < 45%
    }
    thresholds = {
        "min_privacy_coverage": 80.0,
        "min_sirtfi_coverage": 45.0
    }
    failures = check_quality_thresholds(stats, thresholds)
    assert len(failures) == 2
    assert "Privacy coverage: 70.0%" in failures[0]
    assert "SIRTFI coverage: 40.0%" in failures[1]
```

**Integration Tests**:
```python
def test_cli_exit_code_threshold_met(sample_metadata):
    """Test CLI exits 0 when threshold met."""
    with patch("edugain_analysis.core.metadata.get_metadata") as mock:
        mock.return_value = sample_metadata
        result = subprocess.run(
            ["edugain-analyze", "--min-privacy-coverage", "50"],
            capture_output=True
        )
        assert result.returncode == 0

def test_cli_exit_code_threshold_not_met(sample_metadata):
    """Test CLI exits 1 when threshold not met."""
    with patch("edugain_analysis.core.metadata.get_metadata") as mock:
        mock.return_value = sample_metadata  # 68% privacy coverage
        result = subprocess.run(
            ["edugain-analyze", "--min-privacy-coverage", "80"],
            capture_output=True
        )
        assert result.returncode == 1
        assert b"threshold not met" in result.stderr
```

## Implementation Guidance

### Step 1: Add Helper Function
```python
# src/edugain_analysis/core/analysis.py

def check_quality_thresholds(
    stats: dict,
    min_privacy: float | None = None,
    min_security: float | None = None,
    min_sirtfi: float | None = None,
    fail_on_broken_urls: bool = False
) -> list[str]:
    """
    Check if quality metrics meet specified thresholds.

    Args:
        stats: Analysis statistics dictionary
        min_privacy: Minimum privacy coverage percentage (SP-only)
        min_security: Minimum security contact coverage percentage
        min_sirtfi: Minimum SIRTFI certification coverage percentage
        fail_on_broken_urls: Fail if any broken URLs detected

    Returns:
        List of failure messages (empty if all pass)
    """
    failures = []

    # Privacy coverage (SPs only)
    if min_privacy is not None:
        total = stats.get("total_sps", 0)
        with_privacy = stats.get("sps_has_privacy", 0)
        coverage = (with_privacy / total * 100) if total > 0 else 0.0
        if coverage < min_privacy:
            failures.append(
                f"Privacy coverage: {coverage:.1f}% (threshold: {min_privacy:.1f}%)"
            )

    # Security coverage (all entities)
    if min_security is not None:
        total = stats.get("total_entities", 0)
        with_security = stats.get("entities_with_security", 0)
        coverage = (with_security / total * 100) if total > 0 else 0.0
        if coverage < min_security:
            failures.append(
                f"Security coverage: {coverage:.1f}% (threshold: {min_security:.1f}%)"
            )

    # SIRTFI coverage (all entities)
    if min_sirtfi is not None:
        total = stats.get("total_entities", 0)
        with_sirtfi = stats.get("entities_with_sirtfi", 0)
        coverage = (with_sirtfi / total * 100) if total > 0 else 0.0
        if coverage < min_sirtfi:
            failures.append(
                f"SIRTFI coverage: {coverage:.1f}% (threshold: {min_sirtfi:.1f}%)"
            )

    # Broken URLs check
    if fail_on_broken_urls:
        broken = stats.get("urls_broken", 0)
        if broken > 0:
            failures.append(
                f"Broken privacy URLs detected: {broken}"
            )

    return failures
```

### Step 2: Update CLI Arguments
```python
# src/edugain_analysis/cli/main.py

# Add threshold arguments
threshold_group = parser.add_argument_group("quality thresholds")
threshold_group.add_argument(
    "--min-privacy-coverage",
    type=float,
    metavar="PERCENT",
    help="Minimum SP privacy statement coverage percentage (0-100)"
)
threshold_group.add_argument(
    "--min-security-coverage",
    type=float,
    metavar="PERCENT",
    help="Minimum security contact coverage percentage (0-100)"
)
threshold_group.add_argument(
    "--min-sirtfi-coverage",
    type=float,
    metavar="PERCENT",
    help="Minimum SIRTFI certification coverage percentage (0-100)"
)
threshold_group.add_argument(
    "--fail-on-broken-urls",
    action="store_true",
    help="Fail if any privacy URLs are broken (requires --validate)"
)
parser.add_argument(
    "--quiet",
    action="store_true",
    help="Suppress normal output, only show threshold failures"
)
```

### Step 3: Validate and Check Thresholds
```python
# src/edugain_analysis/cli/main.py

def main():
    args = parser.parse_args()

    # Validate threshold ranges
    for threshold_name in ["min_privacy_coverage", "min_security_coverage", "min_sirtfi_coverage"]:
        threshold = getattr(args, threshold_name)
        if threshold is not None and (threshold < 0 or threshold > 100):
            print(f"Error: {threshold_name} must be between 0 and 100", file=sys.stderr)
            sys.exit(2)

    # Validate --fail-on-broken-urls requires --validate
    if args.fail_on_broken_urls and not args.validate:
        print("Error: --fail-on-broken-urls requires --validate", file=sys.stderr)
        sys.exit(2)

    # ... existing analysis code ...

    # Check quality thresholds
    from ..core.analysis import check_quality_thresholds

    failures = check_quality_thresholds(
        stats,
        min_privacy=args.min_privacy_coverage,
        min_security=args.min_security_coverage,
        min_sirtfi=args.min_sirtfi_coverage,
        fail_on_broken_urls=args.fail_on_broken_urls
    )

    if failures:
        print("\n❌ Quality threshold not met:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        print("\nExit code: 1", file=sys.stderr)
        sys.exit(1)
    elif any([args.min_privacy_coverage, args.min_security_coverage,
              args.min_sirtfi_coverage, args.fail_on_broken_urls]):
        if not args.quiet:
            print("\n✅ All quality thresholds met")
```

## Success Metrics

- Exit codes work correctly in CI/CD pipelines
- Zero false positives (incorrect failures)
- Clear error messages guide users to fix issues
- All existing tests still pass
- New threshold tests achieve 100% coverage
- Documentation updated with examples

## References

- Current CLI: `src/edugain_analysis/cli/main.py:main()`
- Statistics calculation: `src/edugain_analysis/core/analysis.py:analyze_privacy_security()`
- Similar pattern: Git exit codes, pytest exit codes
