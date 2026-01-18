# AI Implementation Prompt: Dry-Run Mode for Validation

**Feature ID**: 1.8 from ROADMAP.md
**Priority**: MEDIUM-HIGH
**Effort**: 2 days
**Type**: Infrastructure

## Objective

Add dry-run mode that previews URL validation operations without making actual HTTP requests, helping users estimate time, network cost, and cache utilization before running expensive validations.

## Context

**Current State**:
- `--validate` flag immediately starts validating all privacy URLs
- No preview of what will be validated
- Users surprised by long validation times or network usage
- No way to estimate time/cost before committing to validation

**Problem**:
- Validation can take 5-10 minutes for thousands of URLs
- Network costs on metered connections
- Unexpected load on remote servers
- No visibility into cache hit rates before validation

**Use Cases**:
```bash
# Preview what will be validated
edugain-analyze --validate --dry-run

# Check cache status before validation
edugain-analyze --validate --dry-run --federation InCommon

# Estimate time for federation-specific validation
edugain-analyze --validate --dry-run | grep "Estimated time"
```

## Requirements

### Core Functionality

1. **New CLI Flag**: `--dry-run`
   - Must be combined with `--validate` (error if used alone)
   - Shows preview of validation plan without making HTTP requests
   - Displays cache statistics and estimates
   - Exit code 0 (no actual validation performed)

2. **Preview Output**:
   ```
   🔍 URL Validation Preview (Dry-Run Mode)
   ══════════════════════════════════════════════════════════════

   📊 Validation Scope:
     Total privacy URLs: 2,683
     URLs already cached: 2,150 (80.1%)
     URLs to validate: 533 (19.9%)

   ⏱️  Estimated Time:
     Cached lookups: ~0.5 seconds
     New validations: ~53 seconds (100 URLs @ 0.5s each with 10 threads)
     Total: ~54 seconds

   💾 Cache Statistics:
     Cache location: ~/.cache/edugain-analysis/url_validation.json
     Cache age: 3.2 hours
     Cache size: 1.2 MB
     Oldest entry: 2026-01-15 09:30:00
     Newest entry: 2026-01-18 10:45:00

   🌍 Federation Breakdown:
     InCommon: 350 URLs (280 cached, 70 new)
     DFN-AAI: 180 URLs (150 cached, 30 new)
     SWAMID: 120 URLs (100 cached, 20 new)
     ...

   💡 Tips:
     - Run validation during off-peak hours to reduce server load
     - Consider --federation flag to validate one federation at a time
     - Cache expires after 7 days

   ══════════════════════════════════════════════════════════════
   ℹ️  This was a dry-run. No URLs were validated.
   ℹ️  Remove --dry-run to perform actual validation.
   ```

3. **Edge Cases**:
   - `--dry-run` without `--validate`: Error message + exit 2
   - Empty cache: Show "0 cached, all will be validated"
   - All URLs cached: Show "100% cache hit rate, validation will be fast"
   - Expired cache entries: Count as "needs validation"

### Implementation Details

**Files to Modify**:

1. **`src/edugain_analysis/cli/main.py`**:
   - Add `--dry-run` argument
   - Validate must be combined with `--validate`
   - Call dry-run preview function instead of actual validation

2. **`src/edugain_analysis/core/validation.py`**:
   - Add `preview_validation(urls, cache)` function
   - Calculate cache hit rate
   - Estimate validation time based on thread count
   - Generate federation breakdown

3. **Helper Functions**:
   - `estimate_validation_time(url_count, threads, delay)`: Calculate time estimate
   - `analyze_cache_status(cache_data)`: Cache age, size, entry count
   - `group_urls_by_federation(entities)`: Federation breakdown

## Acceptance Criteria

### Functional Requirements
- [ ] `--dry-run` requires `--validate` (error if not)
- [ ] Preview shows total URLs, cached count, new validations
- [ ] Estimated time calculated based on thread count and delay
- [ ] Cache statistics displayed (location, age, size)
- [ ] Federation breakdown shown (cached vs. new per federation)
- [ ] No HTTP requests made during dry-run
- [ ] Exit code 0 after dry-run preview
- [ ] Clear message that this was a preview

### Quality Requirements
- [ ] Time estimates accurate within ±20%
- [ ] Cache hit rate calculation correct
- [ ] Federation breakdown matches actual analysis
- [ ] Preview completes in < 1 second
- [ ] Output is clear and actionable

### Testing Requirements
- [ ] Test `--dry-run` without `--validate` fails
- [ ] Test preview with empty cache
- [ ] Test preview with 100% cache hits
- [ ] Test preview with mixed cache status
- [ ] Test federation breakdown accuracy
- [ ] Test time estimation calculation
- [ ] Test no HTTP requests made during dry-run

## Testing Strategy

**Unit Tests**:
```python
def test_estimate_validation_time():
    """Test validation time estimation."""
    # 100 URLs, 10 threads, 0.5s delay = ~10s
    time_est = estimate_validation_time(
        url_count=100,
        threads=10,
        delay=0.5
    )
    assert 9 <= time_est <= 11  # Allow some variance

def test_preview_validation_with_cache():
    """Test preview with partial cache hits."""
    urls = [
        "https://example1.org/privacy",
        "https://example2.org/privacy",
        "https://example3.org/privacy"
    ]
    cache = {
        "https://example1.org/privacy": {"timestamp": "...", "accessible": True},
        "https://example2.org/privacy": {"timestamp": "...", "accessible": False}
    }

    preview = preview_validation(urls, cache, cache_days=7)
    assert preview["total_urls"] == 3
    assert preview["cached_count"] == 2
    assert preview["new_validations"] == 1
    assert preview["cache_hit_rate"] == 66.7

def test_dry_run_no_http_requests(monkeypatch):
    """Test dry-run makes no HTTP requests."""
    request_count = 0

    def mock_request(*args, **kwargs):
        nonlocal request_count
        request_count += 1
        raise AssertionError("HTTP request made during dry-run!")

    monkeypatch.setattr("requests.get", mock_request)

    # Run dry-run
    result = subprocess.run(
        ["edugain-analyze", "--validate", "--dry-run"],
        capture_output=True
    )

    assert result.returncode == 0
    assert request_count == 0  # No requests made
    assert b"dry-run" in result.stdout.lower()
```

**Integration Tests**:
```python
@patch("edugain_analysis.core.metadata.get_metadata")
def test_cli_dry_run_preview(mock_metadata, sample_metadata):
    """Test --dry-run shows preview output."""
    mock_metadata.return_value = sample_metadata

    result = subprocess.run(
        ["edugain-analyze", "--validate", "--dry-run"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Dry-Run Mode" in result.stdout
    assert "Total privacy URLs:" in result.stdout
    assert "Estimated Time:" in result.stdout
    assert "Cache Statistics:" in result.stdout
    assert "No URLs were validated" in result.stdout

def test_dry_run_without_validate_fails():
    """Test --dry-run without --validate fails."""
    result = subprocess.run(
        ["edugain-analyze", "--dry-run"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 2
    assert "requires --validate" in result.stderr
```

## Implementation Guidance

### Step 1: Add Helper Functions

```python
# src/edugain_analysis/core/validation.py

from pathlib import Path
from datetime import datetime, timezone, timedelta

def estimate_validation_time(
    url_count: int,
    threads: int = 10,
    delay_per_url: float = 0.5
) -> float:
    """
    Estimate time required to validate URLs.

    Args:
        url_count: Number of URLs to validate
        threads: Number of parallel threads
        delay_per_url: Average time per URL (seconds)

    Returns:
        Estimated time in seconds
    """
    if url_count == 0:
        return 0.0

    # Parallel execution: divide by threads, add overhead
    batches = (url_count + threads - 1) // threads  # Ceiling division
    return batches * delay_per_url * 1.1  # Add 10% overhead

def analyze_cache_status(cache_file: Path, cache_days: int = 7) -> dict:
    """
    Analyze URL validation cache status.

    Args:
        cache_file: Path to cache file
        cache_days: Cache expiry in days

    Returns:
        Dictionary with cache statistics
    """
    if not cache_file.exists():
        return {
            "exists": False,
            "size_mb": 0,
            "entry_count": 0,
            "oldest_entry": None,
            "newest_entry": None,
            "expired_count": 0
        }

    import json
    with open(cache_file, "r") as f:
        cache_data = json.load(f)

    size_mb = cache_file.stat().st_size / (1024 * 1024)
    cutoff = datetime.now(timezone.utc) - timedelta(days=cache_days)

    timestamps = []
    expired_count = 0

    for url, data in cache_data.items():
        if "timestamp" in data:
            ts = datetime.fromisoformat(data["timestamp"])
            timestamps.append(ts)
            if ts < cutoff:
                expired_count += 1

    return {
        "exists": True,
        "size_mb": round(size_mb, 2),
        "entry_count": len(cache_data),
        "oldest_entry": min(timestamps) if timestamps else None,
        "newest_entry": max(timestamps) if timestamps else None,
        "expired_count": expired_count
    }

def preview_validation(
    urls: list[str],
    cache_data: dict,
    cache_days: int = 7,
    threads: int = 10
) -> dict:
    """
    Preview validation plan without making HTTP requests.

    Args:
        urls: List of URLs to potentially validate
        cache_data: Current cache data
        cache_days: Cache expiry in days
        threads: Number of parallel threads

    Returns:
        Dictionary with preview statistics
    """
    total_urls = len(urls)
    cached_count = 0
    expired_count = 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=cache_days)

    for url in urls:
        if url in cache_data:
            # Check if cache entry is still valid
            timestamp = cache_data[url].get("timestamp")
            if timestamp:
                ts = datetime.fromisoformat(timestamp)
                if ts >= cutoff:
                    cached_count += 1
                else:
                    expired_count += 1

    new_validations = total_urls - cached_count
    cache_hit_rate = (cached_count / total_urls * 100) if total_urls > 0 else 0

    estimated_time = estimate_validation_time(new_validations, threads)

    return {
        "total_urls": total_urls,
        "cached_count": cached_count,
        "expired_count": expired_count,
        "new_validations": new_validations,
        "cache_hit_rate": round(cache_hit_rate, 1),
        "estimated_time": estimated_time
    }

def format_dry_run_preview(
    preview: dict,
    cache_stats: dict,
    federation_breakdown: dict
) -> str:
    """
    Format dry-run preview as user-friendly output.

    Args:
        preview: Preview statistics from preview_validation()
        cache_stats: Cache statistics from analyze_cache_status()
        federation_breakdown: Per-federation URL counts

    Returns:
        Formatted preview string
    """
    lines = []
    lines.append("🔍 URL Validation Preview (Dry-Run Mode)")
    lines.append("=" * 66)
    lines.append("")

    # Validation scope
    lines.append("📊 Validation Scope:")
    lines.append(f"  Total privacy URLs: {preview['total_urls']:,}")
    lines.append(f"  URLs already cached: {preview['cached_count']:,} ({preview['cache_hit_rate']:.1f}%)")
    lines.append(f"  URLs to validate: {preview['new_validations']:,}")
    if preview['expired_count'] > 0:
        lines.append(f"  Expired cache entries: {preview['expired_count']:,}")
    lines.append("")

    # Time estimate
    lines.append("⏱️  Estimated Time:")
    lines.append(f"  Cached lookups: ~0.5 seconds")
    if preview['new_validations'] > 0:
        lines.append(f"  New validations: ~{preview['estimated_time']:.0f} seconds")
    total_time = preview['estimated_time'] + 0.5
    lines.append(f"  Total: ~{total_time:.0f} seconds")
    lines.append("")

    # Cache statistics
    if cache_stats['exists']:
        lines.append("💾 Cache Statistics:")
        lines.append(f"  Cache size: {cache_stats['size_mb']} MB")
        lines.append(f"  Total entries: {cache_stats['entry_count']:,}")
        if cache_stats['oldest_entry']:
            lines.append(f"  Oldest entry: {cache_stats['oldest_entry'].strftime('%Y-%m-%d %H:%M')}")
        if cache_stats['newest_entry']:
            lines.append(f"  Newest entry: {cache_stats['newest_entry'].strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

    # Federation breakdown (top 10)
    if federation_breakdown:
        lines.append("🌍 Federation Breakdown (Top 10):")
        sorted_feds = sorted(
            federation_breakdown.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )[:10]

        for federation, counts in sorted_feds:
            lines.append(
                f"  {federation}: {counts['total']} URLs "
                f"({counts['cached']} cached, {counts['new']} new)"
            )
        lines.append("")

    # Tips
    lines.append("💡 Tips:")
    lines.append("  - Run validation during off-peak hours to reduce server load")
    lines.append("  - Consider --federation flag to validate one federation at a time")
    lines.append(f"  - Cache expires after 7 days")
    lines.append("")

    lines.append("=" * 66)
    lines.append("ℹ️  This was a dry-run. No URLs were validated.")
    lines.append("ℹ️  Remove --dry-run to perform actual validation.")

    return "\n".join(lines)
```

### Step 2: Update CLI

```python
# src/edugain_analysis/cli/main.py

parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Preview validation plan without making HTTP requests (requires --validate)"
)

def main():
    args = parser.parse_args()

    # Validate --dry-run requires --validate
    if args.dry_run and not args.validate:
        print("Error: --dry-run requires --validate", file=sys.stderr)
        sys.exit(2)

    # ... existing analysis code to get entities and privacy URLs ...

    # Dry-run preview mode
    if args.dry_run and args.validate:
        from ..core.validation import (
            preview_validation,
            analyze_cache_status,
            format_dry_run_preview
        )

        # Load cache
        cache_file = get_url_validation_cache_path()
        cache_data = load_url_validation_cache(cache_file) if cache_file.exists() else {}

        # Collect privacy URLs
        privacy_urls = [
            entity["privacy_url"]
            for entity in entities_list
            if entity.get("privacy_url")
        ]

        # Generate preview
        preview = preview_validation(
            urls=privacy_urls,
            cache_data=cache_data,
            cache_days=URL_VALIDATION_CACHE_DAYS,
            threads=URL_VALIDATION_THREADS
        )

        # Get cache stats
        cache_stats = analyze_cache_status(cache_file, URL_VALIDATION_CACHE_DAYS)

        # Federation breakdown
        federation_breakdown = {}
        for entity in entities_list:
            if entity.get("privacy_url"):
                fed = entity["federation"]
                if fed not in federation_breakdown:
                    federation_breakdown[fed] = {"total": 0, "cached": 0, "new": 0}

                federation_breakdown[fed]["total"] += 1
                if entity["privacy_url"] in cache_data:
                    federation_breakdown[fed]["cached"] += 1
                else:
                    federation_breakdown[fed]["new"] += 1

        # Format and print preview
        preview_output = format_dry_run_preview(preview, cache_stats, federation_breakdown)
        print(preview_output)

        # Exit without running actual validation
        return

    # ... rest of normal execution ...
```

## Success Metrics

- Preview completes in < 1 second for 10,000 URLs
- Time estimates accurate within ±20% of actual validation
- Zero HTTP requests made during dry-run (verified by tests)
- Users report dry-run helps them plan validation runs
- All tests pass with 100% coverage

## References

- Current validation: `src/edugain_analysis/core/validation.py`
- Cache handling: `src/edugain_analysis/core/metadata.py`
- Time estimation: Based on thread pool behavior
