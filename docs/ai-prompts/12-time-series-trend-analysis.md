# AI Implementation Prompt: Time-Series Trend Analysis & Reporting

**Feature ID**: 2.1 from ROADMAP.md
**Priority**: HIGH
**Effort**: 3-4 weeks
**Type**: Report
**Dependencies**: Phase 1.4 (Historical Snapshot Storage)

## Objective

Visualize quality metrics over time to track improvements, identify regressions, and demonstrate ROI of quality improvement efforts.

## Context

**Current State**:
- Analysis shows current state only (snapshot in time)
- No historical tracking of compliance metrics
- Can't answer: "How has privacy coverage changed over 6 months?"
- No evidence of improvement for leadership presentations

**Problem**:
- Federation operators can't demonstrate progress
- Regressions not detected until too late
- No data-driven planning for future improvements
- Missing compelling narrative for funding requests

**Dependencies**:
- Requires `history.db` from Phase 1.4 (Historical Snapshot Storage)
- Needs at least 7-30 days of data for meaningful trends
- Works best with 90+ days of historical data

## Requirements

### Core Functionality

1. **Trend Graphs** (Multiple Formats):

   **A. Terminal Sparklines** (Unicode):
   ```
   Privacy Coverage (30 days): ▁▂▂▃▄▅▆▇█ 68% → 75% (+7%)
   Security Coverage (30 days): ▃▃▄▄▅▅▆▆▇ 52% → 58% (+6%)
   SIRTFI Coverage (30 days): ▂▂▂▂▃▃▃▃▄ 42% → 45% (+3%)
   ```

   **B. Matplotlib Charts** (PNG/PDF):
   - Line charts for coverage trends
   - Bar charts for week-over-week changes
   - Multi-line charts comparing multiple federations
   - Export to `artifacts/trends/` directory

   **C. CSV Export**:
   - Time-series data for external analysis
   - Columns: Date, Metric, Value, Change, PercentChange

2. **Change Detection**:

   **Week-over-Week**:
   ```
   📈 This Week vs. Last Week:
     Privacy coverage: 75.2% (+2.3%)
     Security coverage: 58.1% (+1.2%)
     SIRTFI coverage: 45.3% (+0.8%)

     🎉 12 entities fixed privacy statements
     ⚠️  3 entities lost security contacts (regression)
   ```

   **Month-over-Month**:
   ```
   📈 This Month vs. Last Month:
     Privacy coverage: 75.2% (+8.1%)
     Total entities improved: 45
     Top improving federation: InCommon (+12%)
   ```

3. **Improvement Rankings**:
   ```
   🏆 Top 5 Most Improved Federations (30 days):
     1. InCommon: +12% privacy coverage
     2. DFN-AAI: +9% security contacts
     3. SWAMID: +7% SIRTFI certification
     4. AAF: +6% privacy coverage
     5. GARR: +5% security contacts
   ```

4. **Regression Detection**:
   ```
   ⚠️  Federations Needing Attention:
     - Federation X: Privacy coverage dropped 5% this week
     - Federation Y: 3 entities lost SIRTFI certification
   ```

5. **Predictive Analytics**:
   ```
   🔮 Compliance Forecast:
     Current privacy coverage: 75%
     30-day trend: +2.3% per week
     Projected 80% coverage by: March 15, 2026 (4 weeks)

     To reach 80% coverage faster:
     - Fix 23 entities → reach goal in 2 weeks
     - Focus on federations with <70% coverage
   ```

6. **CLI Commands**:
   ```bash
   # 30-day trend summary
   edugain-analyze --trends 30d

   # 90-day trends with sparklines
   edugain-analyze --trends 90d

   # Compare current vs. specific date
   edugain-analyze --compare 2025-12-01

   # Export trends to CSV
   edugain-analyze --trends 90d --csv trends

   # Generate trend charts (PNG)
   edugain-analyze --trends 90d --chart png

   # Per-federation trends
   edugain-analyze --trends 30d --federation InCommon
   ```

### Output Examples

**Terminal Summary**:
```
══════════════════════════════════════════════════════════════
  📈 Quality Trends (Last 30 Days)
══════════════════════════════════════════════════════════════

Overall Compliance Trends:
  Privacy Coverage:   ▁▂▂▃▄▅▆▇█  68.5% → 75.2% (+6.7%)
  Security Coverage:  ▃▃▄▄▅▅▆▆▇  52.1% → 58.3% (+6.2%)
  SIRTFI Coverage:    ▂▂▂▂▃▃▃▃▄  42.3% → 45.1% (+2.8%)

Change Summary:
  ✅ 45 entities improved
  ❌ 8 entities regressed
  ➕ 12 new entities added
  ➖ 3 entities removed

Week-over-Week:
  Last 7 days: +2.3% privacy, +1.2% security, +0.8% SIRTFI
  Previous 7 days: +1.8% privacy, +0.9% security, +0.5% SIRTFI
  Trend: ▲ Accelerating improvement

Top Movers:
  🏆 Most improved: InCommon (+12% privacy)
  ⚠️  Needs attention: FederationX (-5% privacy)

Forecast:
  At current rate, 80% privacy coverage by: 2026-03-15
  To reach goal faster: Fix 23 more entities

══════════════════════════════════════════════════════════════
```

**CSV Export** (`--trends 30d --csv trends`):
```csv
Date,Metric,Value,Change,PercentChange,Federation
2026-01-01,privacy_coverage,68.5,0.0,0.0,Overall
2026-01-02,privacy_coverage,69.2,0.7,1.02,Overall
2026-01-03,privacy_coverage,70.1,0.9,1.30,Overall
...
2026-01-30,privacy_coverage,75.2,0.4,0.53,Overall
```

### Implementation Details

**Files to Create**:

1. **`src/edugain_analysis/core/trends.py`**:
   - `load_historical_data(start_date, end_date)`: Query history.db
   - `calculate_trends(timeseries_data)`: Compute changes, rates
   - `detect_regressions(trends)`: Identify drops > threshold
   - `forecast_coverage(trends, target)`: Predict when target reached
   - `identify_top_movers(federation_trends)`: Rank improvements

2. **`src/edugain_analysis/formatters/trends.py`**:
   - `format_sparkline(values)`: Unicode sparkline generation
   - `generate_trend_chart(data, output_path)`: Matplotlib charts
   - `export_trends_csv(trends)`: CSV time-series export
   - `format_trend_summary(trends)`: Terminal summary

3. **Files to Modify**:
   - `src/edugain_analysis/cli/main.py`: Add `--trends`, `--compare` flags
   - `src/edugain_analysis/formatters/pdf.py`: Add trend section to PDFs

**Dependencies** (New):
- `matplotlib`: For chart generation (optional)
- Alternatively: Use `termgraph` for ASCII charts (no matplotlib needed)

**Edge Cases**:
- Insufficient data: Need at least 2 snapshots for trends
- Missing snapshots: Interpolate or show gaps
- Data quality: Handle outliers (e.g., sudden 50% drop = likely error)
- Time zones: Normalize to UTC for consistency
- Leap days, DST changes: Handle date math correctly

## Acceptance Criteria

### Functional Requirements
- [ ] `--trends N` loads last N days of historical data
- [ ] Sparklines rendered correctly in terminal
- [ ] Week-over-week and month-over-month changes calculated
- [ ] Top movers (improved/regressed) identified
- [ ] Forecast calculates ETA to reach target coverage
- [ ] `--chart` generates PNG/PDF trend visualizations
- [ ] `--csv trends` exports time-series data
- [ ] Per-federation trends with `--federation` flag

### Quality Requirements
- [ ] Accurate trend calculations (verified against manual computation)
- [ ] Sparklines render correctly in 95%+ terminals
- [ ] Charts readable and professionally formatted
- [ ] Performance: Trends computed in < 5s for 365 days of data
- [ ] Graceful handling of missing data points

### Testing Requirements
- [ ] Test trend calculation with sample historical data
- [ ] Test sparkline generation
- [ ] Test change detection (week-over-week, month-over-month)
- [ ] Test forecast accuracy
- [ ] Test CSV export format
- [ ] Test chart generation (if matplotlib available)
- [ ] Integration test with real history.db

## Testing Strategy

**Unit Tests**:
```python
def test_calculate_trends():
    """Test trend calculation from time-series data."""
    data = [
        {"date": "2026-01-01", "privacy_coverage": 68.5},
        {"date": "2026-01-08", "privacy_coverage": 70.2},
        {"date": "2026-01-15", "privacy_coverage": 72.8},
        {"date": "2026-01-22", "privacy_coverage": 74.1},
        {"date": "2026-01-29", "privacy_coverage": 75.2},
    ]

    trends = calculate_trends(data, metric="privacy_coverage")

    assert trends["start_value"] == 68.5
    assert trends["end_value"] == 75.2
    assert trends["total_change"] == pytest.approx(6.7, abs=0.1)
    assert trends["percent_change"] == pytest.approx(9.78, abs=0.1)
    assert trends["weekly_rate"] > 0  # Positive trend

def test_generate_sparkline():
    """Test sparkline generation."""
    values = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    sparkline = generate_sparkline(values)

    # Should use Unicode block characters
    assert any(c in sparkline for c in "▁▂▃▄▅▆▇█")
    assert len(sparkline) == len(values)

def test_forecast_coverage():
    """Test coverage forecast calculation."""
    trends = {
        "current_value": 75.0,
        "weekly_rate": 2.5  # +2.5% per week
    }
    target = 80.0

    eta = forecast_coverage(trends, target)

    # Should take 2 weeks: (80 - 75) / 2.5 = 2
    assert eta["weeks"] == 2
    assert eta["date"] == "2026-02-12"  # (assuming today is 2026-01-29)
```

## Implementation Guidance

### Step 1: Load Historical Data

```python
# src/edugain_analysis/core/trends.py

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

def load_historical_data(
    start_date: datetime,
    end_date: datetime,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Load historical snapshots from database.

    Args:
        start_date: Start date for time range
        end_date: End date for time range
        db_path: Path to history.db

    Returns:
        List of snapshot dictionaries with stats
    """
    if db_path is None:
        from ..core.history import get_history_db_path
        db_path = get_history_db_path()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dicts

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            timestamp,
            total_entities,
            total_sps,
            total_idps,
            sps_with_privacy,
            privacy_coverage_percent,
            entities_with_security,
            security_coverage_percent,
            entities_with_sirtfi,
            sirtfi_coverage_percent
        FROM snapshots
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
    """, (start_date.isoformat(), end_date.isoformat()))

    snapshots = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return snapshots

def load_federation_trends(
    start_date: datetime,
    end_date: datetime,
    federation: Optional[str] = None,
    db_path: Optional[Path] = None
) -> list[dict]:
    """
    Load federation-specific historical data.

    Args:
        start_date: Start date
        end_date: End date
        federation: Optional specific federation name
        db_path: Path to history.db

    Returns:
        List of federation snapshot dictionaries
    """
    if db_path is None:
        from ..core.history import get_history_db_path
        db_path = get_history_db_path()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    if federation:
        cursor.execute("""
            SELECT *
            FROM federation_history
            WHERE timestamp BETWEEN ? AND ?
              AND federation = ?
            ORDER BY timestamp ASC
        """, (start_date.isoformat(), end_date.isoformat(), federation))
    else:
        cursor.execute("""
            SELECT *
            FROM federation_history
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC, federation ASC
        """, (start_date.isoformat(), end_date.isoformat()))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results
```

### Step 2: Calculate Trends

```python
# src/edugain_analysis/core/trends.py

def calculate_trends(snapshots: list[dict], metric: str = "privacy_coverage_percent") -> dict:
    """
    Calculate trends from historical snapshots.

    Args:
        snapshots: List of snapshot dictionaries
        metric: Metric to analyze

    Returns:
        Trend statistics dictionary
    """
    if len(snapshots) < 2:
        return {"error": "Insufficient data (need at least 2 snapshots)"}

    # Extract values
    values = [s[metric] for s in snapshots]
    dates = [datetime.fromisoformat(s["timestamp"]) for s in snapshots]

    # Calculate changes
    start_value = values[0]
    end_value = values[-1]
    total_change = end_value - start_value
    percent_change = (total_change / start_value * 100) if start_value > 0 else 0

    # Calculate rate (change per week)
    time_span = (dates[-1] - dates[0]).days
    weeks = time_span / 7.0
    weekly_rate = (total_change / weeks) if weeks > 0 else 0

    # Detect trend direction
    if total_change > 0.5:
        trend = "improving"
    elif total_change < -0.5:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "metric": metric,
        "start_date": dates[0].isoformat(),
        "end_date": dates[-1].isoformat(),
        "start_value": start_value,
        "end_value": end_value,
        "total_change": total_change,
        "percent_change": percent_change,
        "weekly_rate": weekly_rate,
        "trend": trend,
        "values": values,
        "dates": dates
    }

def detect_regressions(federation_trends: list[dict], threshold: float = 5.0) -> list[dict]:
    """
    Detect federations with significant coverage drops.

    Args:
        federation_trends: List of federation trend dicts
        threshold: Percentage drop threshold for regression

    Returns:
        List of regressions
    """
    regressions = []

    for fed_trend in federation_trends:
        if fed_trend.get("percent_change", 0) < -threshold:
            regressions.append({
                "federation": fed_trend["federation"],
                "metric": fed_trend["metric"],
                "drop": abs(fed_trend["percent_change"]),
                "start_value": fed_trend["start_value"],
                "end_value": fed_trend["end_value"]
            })

    return sorted(regressions, key=lambda x: x["drop"], reverse=True)

def forecast_coverage(trends: dict, target: float) -> dict:
    """
    Forecast when target coverage will be reached.

    Args:
        trends: Trend statistics dictionary
        target: Target coverage percentage

    Returns:
        Forecast dictionary with ETA
    """
    current_value = trends["end_value"]
    weekly_rate = trends["weekly_rate"]

    if weekly_rate <= 0:
        return {
            "reachable": False,
            "reason": "No positive trend (rate ≤ 0)"
        }

    if current_value >= target:
        return {
            "reachable": True,
            "already_reached": True
        }

    # Calculate weeks to target
    remaining = target - current_value
    weeks_to_target = remaining / weekly_rate

    # Calculate date
    from datetime import timedelta
    end_date = datetime.fromisoformat(trends["end_date"])
    eta_date = end_date + timedelta(weeks=weeks_to_target)

    return {
        "reachable": True,
        "weeks": round(weeks_to_target, 1),
        "days": round(weeks_to_target * 7),
        "eta_date": eta_date.date().isoformat(),
        "current_value": current_value,
        "target_value": target,
        "weekly_rate": weekly_rate
    }
```

### Step 3: Generate Sparklines

```python
# src/edugain_analysis/formatters/trends.py

def generate_sparkline(values: list[float]) -> str:
    """
    Generate Unicode sparkline from values.

    Args:
        values: List of numeric values

    Returns:
        Sparkline string using Unicode block characters
    """
    if not values:
        return ""

    # Unicode sparkline characters (8 levels)
    chars = "▁▂▃▄▅▆▇█"

    # Normalize values to 0-7 range
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val

    if range_val == 0:
        # All values the same
        return chars[4] * len(values)

    sparkline = ""
    for val in values:
        normalized = (val - min_val) / range_val
        index = int(normalized * 7)  # 0-7
        sparkline += chars[index]

    return sparkline
```

### Step 4: Format Trend Summary

```python
# src/edugain_analysis/formatters/trends.py

def format_trend_summary(
    overall_trends: dict,
    federation_trends: list[dict],
    changes: dict
) -> str:
    """
    Format trend summary for terminal output.
    """
    lines = []
    lines.append("=" * 66)
    lines.append("  📈 Quality Trends (Last 30 Days)")
    lines.append("=" * 66)
    lines.append("")

    # Overall compliance trends with sparklines
    lines.append("Overall Compliance Trends:")

    for metric_name, trend in overall_trends.items():
        sparkline = generate_sparkline(trend["values"])
        start = trend["start_value"]
        end = trend["end_value"]
        change = trend["total_change"]
        sign = "+" if change >= 0 else ""

        lines.append(
            f"  {metric_name:18} {sparkline}  {start:.1f}% → {end:.1f}% "
            f"({sign}{change:.1f}%)"
        )

    # ... rest of summary ...

    return "\n".join(lines)
```

### Step 5: CLI Integration

```python
# src/edugain_analysis/cli/main.py

parser.add_argument(
    "--trends",
    metavar="PERIOD",
    help="Show trends over period (e.g., 30d, 90d, 1y)"
)
parser.add_argument(
    "--compare",
    metavar="DATE",
    help="Compare current state to specific date (YYYY-MM-DD)"
)
parser.add_argument(
    "--chart",
    choices=["png", "pdf", "svg"],
    help="Generate trend chart (requires matplotlib)"
)

def main():
    args = parser.parse_args()

    # Handle trends mode
    if args.trends:
        from ..core.trends import load_historical_data, calculate_trends
        from ..formatters.trends import format_trend_summary

        # Parse period (30d, 90d, 1y)
        if args.trends.endswith('d'):
            days = int(args.trends[:-1])
        elif args.trends.endswith('w'):
            days = int(args.trends[:-1]) * 7
        elif args.trends.endswith('y'):
            days = int(args.trends[:-1]) * 365
        else:
            print("Error: Invalid period format (use 30d, 90d, 1y)", file=sys.stderr)
            sys.exit(2)

        # Load historical data
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        snapshots = load_historical_data(start_date, end_date)

        if len(snapshots) < 2:
            print(f"Error: Insufficient historical data (found {len(snapshots)} snapshots)",
                  file=sys.stderr)
            sys.exit(1)

        # Calculate trends
        privacy_trend = calculate_trends(snapshots, "privacy_coverage_percent")
        security_trend = calculate_trends(snapshots, "security_coverage_percent")
        sirtfi_trend = calculate_trends(snapshots, "sirtfi_coverage_percent")

        # Format and print
        summary = format_trend_summary({
            "Privacy Coverage": privacy_trend,
            "Security Coverage": security_trend,
            "SIRTFI Coverage": sirtfi_trend
        })
        print(summary)

        return
```

## Success Metrics

- Trends accurately reflect historical changes
- Sparklines render correctly in terminals
- Forecast predictions accurate within ±10%
- Federation operators use trends for planning
- Leadership uses trend reports for decision-making
- All tests pass with >90% coverage

## References

- Sparklines: https://en.wikipedia.org/wiki/Sparkline
- Matplotlib: https://matplotlib.org/
- SQLite date/time functions: https://www.sqlite.org/lang_datefunc.html
- Similar tools: GitHub contribution graphs, stock market charts
