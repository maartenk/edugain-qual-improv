# AI Implementation Prompt: Federation Benchmarking & Peer Comparison

**Feature ID**: 1.13 from ROADMAP.md
**Priority**: HIGH
**Effort**: 2 weeks
**Type**: Report

## Objective

Implement federation-to-federation benchmarking to help operators understand how their federation performs compared to peers, identify best practices, and discover improvement opportunities.

## Context

**Current State**:
- Tool shows per-federation statistics in isolation
- No comparison between federations
- No ranking or percentile information
- Operators can't identify best-in-class federations
- No guidance on realistic improvement targets

**Current Output** (Isolated Stats):
```
📊 Per-Federation Statistics:

InCommon:
  Total entities: 1,234 (SPs: 856, IdPs: 378)
  Privacy coverage: 78.5%
  Security contacts: 45.2%
  SIRTFI compliance: 23.1%

GÉANT:
  Total entities: 892 (SPs: 623, IdPs: 269)
  Privacy coverage: 82.3%
  Security contacts: 52.8%
  SIRTFI compliance: 31.4%
```

**Improved Output** (With Benchmarking):
```
📊 Federation Benchmarking Report:

Privacy Statement Coverage:
  🥇 Best: GÉANT (82.3%)
  🥈 2nd: InCommon (78.5%)
  🥉 3rd: DFN-AAI (75.2%)
  ...
  📊 Your federation (InCommon): 78.5% (rank #2 / 45 federations)
     - Above average (+8.2 percentage points)
     - Percentile: 94th (better than 94% of federations)
     - Gap to #1: -3.8 pp
     - Potential: Could reach 82% with 31 more compliant SPs

Security Contact Coverage:
  🥇 Best: SWITCH (68.4%)
  📊 Your federation (InCommon): 45.2% (rank #18 / 45)
     - Below average (-5.3 pp)
     - Percentile: 60th
     - Improvement target: +23.2 pp to match leader

Key Insights:
  ✅ Strong performer in privacy statements
  ⚠️  Opportunity for improvement in security contacts
  💡 Study best practices from: SWITCH, GÉANT, DFN-AAI
```

**Problem**:
- **No context**: Operators don't know if 78% is good or bad
- **Missed opportunities**: Can't identify areas for improvement
- **No motivation**: No competitive element or targets
- **Isolated silos**: Can't learn from high-performing peers

## Requirements

### Core Functionality

1. **Federation Rankings**:
   - Rank federations by each quality metric (privacy, security, SIRTFI)
   - Show top 5 and bottom 5 performers
   - Calculate percentile rankings (e.g., "better than 85% of federations")
   - Include federation's own ranking if not in top/bottom 5

2. **Benchmark Metrics**:
   ```python
   metrics = {
       "privacy_coverage": "% of SPs with privacy statements",
       "valid_privacy_urls": "% of SPs with valid (non-placeholder) privacy URLs",
       "security_contact_coverage": "% of entities with security contacts",
       "sirtfi_compliance": "% of entities with SIRTFI",
       "bot_protection_rate": "% of SPs with bot protection",
       "overall_quality_score": "Weighted composite score (0-100)"
   }
   ```

3. **Statistical Analysis**:
   - Mean, median, standard deviation for each metric
   - Quartiles: 25th, 50th, 75th percentiles
   - Outlier detection (federations >2 std dev from mean)
   - Distribution visualization (ASCII histogram or sparkline)

4. **Peer Comparison**:
   - Compare federation against average
   - Show gap to leader (best performer)
   - Identify "peer group" (similar-sized federations)
   - Compare against peer group average

5. **Actionable Insights**:
   - Calculate "potential" (how many entities need improvement to reach target)
   - Suggest realistic improvement targets (e.g., reach median, reach 75th percentile)
   - Identify "quick wins" (metrics where small effort = big ranking improvement)

6. **CLI Flags**:
   ```bash
   --benchmark [FEDERATION]     # Show benchmarking for specific federation
   --benchmark-all              # Show full benchmarking report for all federations
   --benchmark-metric [METRIC]  # Benchmark specific metric only
   --benchmark-top N            # Show top N performers (default: 5)
   --json-benchmark             # Export benchmark data as JSON
   ```

7. **Output Formats**:
   - **Terminal**: Human-readable benchmark report with rankings
   - **CSV**: `--csv benchmark` exports full federation comparison table
   - **JSON**: `--json-benchmark` exports structured benchmark data

### Ranking System

**Simple Rankings** (by single metric):
```
Privacy Statement Coverage Rankings:
  🥇 #1: GÉANT (82.3%) - 623 SPs
  🥈 #2: InCommon (78.5%) - 856 SPs
  🥉 #3: DFN-AAI (75.2%) - 412 SPs
  4. SWITCH (73.8%) - 289 SPs
  5. SURFconext (71.4%) - 534 SPs
  ...
  41. FederationX (12.3%) - 45 SPs
  42. FederationY (8.7%) - 23 SPs

  📊 Statistics:
     Mean: 52.3%
     Median: 48.5%
     Std Dev: 18.7%
     Your federation (InCommon): 94th percentile
```

**Composite Quality Score** (weighted):
```python
quality_score = (
    privacy_coverage * 0.35 +
    security_contact_coverage * 0.30 +
    sirtfi_compliance * 0.20 +
    valid_privacy_urls * 0.10 +
    bot_protection_rate * 0.05
)
```

### Peer Group Comparison

**Size-Based Peer Groups**:
- Small: < 100 entities
- Medium: 100-500 entities
- Large: 500-1,000 entities
- Extra Large: > 1,000 entities

**Peer Comparison Example**:
```
Your Federation: InCommon (1,234 entities)
Peer Group: Extra Large Federations (5 total)

Privacy Coverage:
  Peer average: 76.2%
  Your federation: 78.5% (above average +2.3 pp)
  Peer leader: GÉANT (82.3%)
  Peer gap: -3.8 pp

Security Contacts:
  Peer average: 48.9%
  Your federation: 45.2% (below average -3.7 pp)
  Peer leader: NationalFed (55.3%)
  Peer gap: -10.1 pp
```

### Implementation Details

**Files to Modify**:

1. **`src/edugain_analysis/core/benchmarking.py`** (NEW):
   - Federation ranking functions
   - Statistical analysis (mean, median, percentiles)
   - Peer group identification
   - Quality score calculation

2. **`src/edugain_analysis/formatters/benchmark.py`** (NEW):
   - Benchmark report formatting
   - ASCII ranking tables
   - Peer comparison output
   - CSV/JSON export for benchmarks

3. **`src/edugain_analysis/core/analysis.py`**:
   - Ensure per-federation stats are collected correctly
   - Add composite quality score calculation

4. **`src/edugain_analysis/cli/main.py`**:
   - Add `--benchmark` CLI flags
   - Integrate benchmark report generation
   - Handle CSV/JSON benchmark exports

**Edge Cases**:
- Single federation: No benchmarking possible (warn user)
- Federations with < 10 entities: Flag as "too small for reliable comparison"
- Missing data: Handle federations without certain metrics (e.g., no SIRTFI data)
- Zero values: Don't rank federations with 0% (exclude from rankings)
- Tied rankings: Show equal rank (e.g., "#2 (tied)")

## Acceptance Criteria

### Functional Requirements
- [ ] Federation rankings by each quality metric
- [ ] Top N and bottom N performers displayed
- [ ] Percentile rankings calculated correctly
- [ ] Statistical analysis (mean, median, std dev)
- [ ] Peer group comparison (size-based)
- [ ] Composite quality score calculation
- [ ] `--benchmark [FEDERATION]` shows single federation report
- [ ] `--benchmark-all` shows full rankings
- [ ] CSV export: `--csv benchmark`
- [ ] JSON export: `--json-benchmark`

### Quality Requirements
- [ ] Rankings are accurate and consistent
- [ ] Statistical calculations are correct
- [ ] Peer groups are meaningful (similar sizes)
- [ ] Clear, actionable insights provided
- [ ] Performance overhead < 5%
- [ ] Works with 1+ federations (graceful degradation)

### Testing Requirements
- [ ] Test ranking with sample data (known order)
- [ ] Test statistical calculations (mean, median, percentiles)
- [ ] Test peer group assignment
- [ ] Test composite quality score
- [ ] Test edge cases (single federation, ties, missing data)
- [ ] Integration test with real metadata sample

## Testing Strategy

**Unit Tests**:
```python
def test_federation_rankings():
    """Test federation ranking by metric."""
    federation_stats = {
        "FedA": {"privacy_coverage": 85.0},
        "FedB": {"privacy_coverage": 92.0},
        "FedC": {"privacy_coverage": 78.0},
    }

    rankings = rank_federations(federation_stats, "privacy_coverage")

    assert rankings[0] == ("FedB", 92.0)  # Rank #1
    assert rankings[1] == ("FedA", 85.0)  # Rank #2
    assert rankings[2] == ("FedC", 78.0)  # Rank #3

def test_percentile_calculation():
    """Test percentile ranking calculation."""
    values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

    # 90 is in 90th percentile (better than 90% of values)
    assert calculate_percentile(90, values) == 90

    # 50 is in 50th percentile (median)
    assert calculate_percentile(50, values) == 50

def test_peer_group_assignment():
    """Test peer group assignment by size."""
    federation_stats = {
        "SmallFed": {"total_entities": 50},
        "MediumFed": {"total_entities": 250},
        "LargeFed": {"total_entities": 750},
        "XLFed": {"total_entities": 1500},
    }

    peer_groups = assign_peer_groups(federation_stats)

    assert peer_groups["SmallFed"] == "Small"
    assert peer_groups["MediumFed"] == "Medium"
    assert peer_groups["LargeFed"] == "Large"
    assert peer_groups["XLFed"] == "Extra Large"

def test_quality_score_calculation():
    """Test composite quality score."""
    federation_data = {
        "privacy_coverage": 80.0,
        "security_contact_coverage": 50.0,
        "sirtfi_compliance": 30.0,
        "valid_privacy_urls": 75.0,
        "bot_protection_rate": 20.0,
    }

    score = calculate_quality_score(federation_data)

    # Weighted: 80*0.35 + 50*0.30 + 30*0.20 + 75*0.10 + 20*0.05
    # = 28 + 15 + 6 + 7.5 + 1 = 57.5
    assert score == 57.5
```

## Implementation Guidance

### Step 1: Create Benchmarking Module

```python
# src/edugain_analysis/core/benchmarking.py

from typing import Dict, List, Tuple
import statistics

def rank_federations(
    federation_stats: Dict[str, Dict],
    metric: str,
    reverse: bool = True
) -> List[Tuple[str, float]]:
    """
    Rank federations by a specific metric.

    Args:
        federation_stats: Dictionary of federation stats
        metric: Metric to rank by (e.g., "privacy_coverage")
        reverse: If True, higher is better (default)

    Returns:
        List of (federation_name, metric_value) tuples, sorted by rank
    """
    # Extract metric values
    metric_data = []
    for fed_name, stats in federation_stats.items():
        if metric in stats and stats[metric] is not None:
            metric_data.append((fed_name, stats[metric]))

    # Sort by metric value
    metric_data.sort(key=lambda x: x[1], reverse=reverse)

    return metric_data

def calculate_percentile(value: float, all_values: List[float]) -> int:
    """
    Calculate percentile ranking for a value.

    Args:
        value: The value to rank
        all_values: List of all values to compare against

    Returns:
        Percentile (0-100)
    """
    if not all_values:
        return 0

    # Count how many values are below this value
    below_count = sum(1 for v in all_values if v < value)

    # Percentile = (count below / total count) * 100
    percentile = int((below_count / len(all_values)) * 100)

    return percentile

def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate statistical measures for a list of values.

    Args:
        values: List of numeric values

    Returns:
        Dictionary with mean, median, std_dev, quartiles
    """
    if not values:
        return {}

    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
        "min": min(values),
        "max": max(values),
        "q25": statistics.quantiles(values, n=4)[0] if len(values) >= 4 else None,
        "q50": statistics.median(values),
        "q75": statistics.quantiles(values, n=4)[2] if len(values) >= 4 else None,
    }

def assign_peer_groups(federation_stats: Dict[str, Dict]) -> Dict[str, str]:
    """
    Assign federations to peer groups based on size.

    Args:
        federation_stats: Dictionary of federation stats

    Returns:
        Dictionary mapping federation name to peer group
    """
    peer_groups = {}

    for fed_name, stats in federation_stats.items():
        total_entities = stats.get("total_entities", 0)

        if total_entities < 100:
            peer_group = "Small"
        elif total_entities < 500:
            peer_group = "Medium"
        elif total_entities < 1000:
            peer_group = "Large"
        else:
            peer_group = "Extra Large"

        peer_groups[fed_name] = peer_group

    return peer_groups

def calculate_quality_score(federation_data: Dict[str, float]) -> float:
    """
    Calculate composite quality score for a federation.

    Args:
        federation_data: Dictionary with quality metrics

    Returns:
        Composite quality score (0-100)
    """
    # Weights for each metric
    weights = {
        "privacy_coverage": 0.35,
        "security_contact_coverage": 0.30,
        "sirtfi_compliance": 0.20,
        "valid_privacy_urls": 0.10,
        "bot_protection_rate": 0.05,
    }

    score = 0.0
    total_weight = 0.0

    for metric, weight in weights.items():
        if metric in federation_data and federation_data[metric] is not None:
            score += federation_data[metric] * weight
            total_weight += weight

    # Normalize if some metrics are missing
    if total_weight > 0:
        score = score / total_weight * 100

    return round(score, 1)

def generate_benchmark_report(
    federation_stats: Dict[str, Dict],
    target_federation: str = None,
    top_n: int = 5
) -> Dict:
    """
    Generate comprehensive benchmark report.

    Args:
        federation_stats: Dictionary of all federation stats
        target_federation: Specific federation to focus on (optional)
        top_n: Number of top performers to show

    Returns:
        Benchmark report dictionary
    """
    metrics = [
        "privacy_coverage",
        "security_contact_coverage",
        "sirtfi_compliance",
    ]

    report = {
        "rankings": {},
        "statistics": {},
        "peer_comparison": None,
    }

    # Generate rankings for each metric
    for metric in metrics:
        rankings = rank_federations(federation_stats, metric)

        # Calculate statistics
        values = [v for _, v in rankings]
        stats = calculate_statistics(values)

        report["rankings"][metric] = {
            "top_performers": rankings[:top_n],
            "bottom_performers": rankings[-top_n:] if len(rankings) > top_n else [],
            "all_rankings": rankings,
        }

        report["statistics"][metric] = stats

        # Add target federation info
        if target_federation:
            for rank, (fed, value) in enumerate(rankings, start=1):
                if fed == target_federation:
                    percentile = calculate_percentile(value, values)

                    report["rankings"][metric]["target_federation"] = {
                        "rank": rank,
                        "value": value,
                        "percentile": percentile,
                        "gap_to_leader": rankings[0][1] - value if rankings else 0,
                        "gap_to_mean": value - stats["mean"],
                    }
                    break

    # Peer group comparison
    if target_federation:
        peer_groups = assign_peer_groups(federation_stats)
        target_peer_group = peer_groups.get(target_federation)

        if target_peer_group:
            # Find all federations in same peer group
            peers = [
                (fed, stats) for fed, stats in federation_stats.items()
                if peer_groups[fed] == target_peer_group
            ]

            report["peer_comparison"] = {
                "peer_group": target_peer_group,
                "peer_count": len(peers),
                "metrics": {},
            }

            # Compare metrics against peer average
            for metric in metrics:
                peer_values = [
                    stats[metric] for _, stats in peers
                    if metric in stats and stats[metric] is not None
                ]

                if peer_values:
                    peer_mean = statistics.mean(peer_values)
                    target_value = federation_stats[target_federation].get(metric, 0)

                    report["peer_comparison"]["metrics"][metric] = {
                        "peer_average": peer_mean,
                        "your_value": target_value,
                        "gap_to_average": target_value - peer_mean,
                        "peer_leader": max(peer_values),
                    }

    return report
```

### Step 2: Create Benchmark Formatter

```python
# src/edugain_analysis/formatters/benchmark.py

import sys
from typing import Dict

def print_benchmark_report(
    report: Dict,
    target_federation: str = None,
    show_all: bool = False
):
    """
    Print human-readable benchmark report.

    Args:
        report: Benchmark report from generate_benchmark_report()
        target_federation: Federation name to highlight
        show_all: Show full rankings (not just top/bottom)
    """
    print("\n" + "="*70)
    print("📊 Federation Benchmarking Report")
    print("="*70)

    # Medal emojis for top 3
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    # Privacy Coverage Rankings
    print("\n🔒 Privacy Statement Coverage:")
    privacy_rankings = report["rankings"]["privacy_coverage"]

    for rank, (fed, value) in enumerate(privacy_rankings["top_performers"], start=1):
        medal = medals.get(rank, f"{rank}.")
        highlight = " ← YOUR FEDERATION" if fed == target_federation else ""
        print(f"  {medal} {fed}: {value:.1f}%{highlight}")

    if not show_all and len(privacy_rankings["all_rankings"]) > 10:
        print("  ...")
        for rank, (fed, value) in enumerate(
            privacy_rankings["bottom_performers"],
            start=len(privacy_rankings["all_rankings"]) - len(privacy_rankings["bottom_performers"]) + 1
        ):
            highlight = " ← YOUR FEDERATION" if fed == target_federation else ""
            print(f"  {rank}. {fed}: {value:.1f}%{highlight}")

    # Statistics
    stats = report["statistics"]["privacy_coverage"]
    print(f"\n  📊 Statistics:")
    print(f"     Mean: {stats['mean']:.1f}%")
    print(f"     Median: {stats['median']:.1f}%")
    print(f"     Std Dev: {stats['std_dev']:.1f}%")

    # Target federation details
    if target_federation and "target_federation" in privacy_rankings:
        target = privacy_rankings["target_federation"]
        print(f"\n  📍 Your Federation ({target_federation}):")
        print(f"     Rank: #{target['rank']} / {len(privacy_rankings['all_rankings'])}")
        print(f"     Value: {target['value']:.1f}%")
        print(f"     Percentile: {target['percentile']}th")

        gap_symbol = "+" if target['gap_to_mean'] >= 0 else ""
        print(f"     Gap to mean: {gap_symbol}{target['gap_to_mean']:.1f} pp")
        print(f"     Gap to leader: -{target['gap_to_leader']:.1f} pp")

    # Similar sections for other metrics...
    # (Security contacts, SIRTFI, etc.)

    # Peer Comparison
    if report.get("peer_comparison"):
        peer = report["peer_comparison"]
        print(f"\n{'='*70}")
        print(f"👥 Peer Group Comparison ({peer['peer_group']} Federations)")
        print(f"{'='*70}")

        for metric, data in peer["metrics"].items():
            metric_name = metric.replace("_", " ").title()
            print(f"\n{metric_name}:")
            print(f"  Peer average: {data['peer_average']:.1f}%")
            print(f"  Your value: {data['your_value']:.1f}%")

            gap = data['gap_to_average']
            if gap >= 0:
                print(f"  ✅ Above average (+{gap:.1f} pp)")
            else:
                print(f"  ⚠️  Below average ({gap:.1f} pp)")

def export_benchmark_csv(report: Dict):
    """
    Export benchmark data as CSV.

    Args:
        report: Benchmark report dictionary
    """
    import csv

    writer = csv.writer(sys.stdout)

    # Headers
    writer.writerow([
        "Federation",
        "PrivacyCoverage",
        "PrivacyRank",
        "SecurityContactCoverage",
        "SecurityContactRank",
        "SIRTFICompliance",
        "SIRTFIRank",
        "CompositeScore",
        "PeerGroup"
    ])

    # Data rows
    # ... (combine all ranking data into CSV rows)

def export_benchmark_json(report: Dict) -> str:
    """
    Export benchmark data as JSON.

    Args:
        report: Benchmark report dictionary

    Returns:
        JSON string
    """
    import json
    return json.dumps(report, indent=2)
```

### Step 3: CLI Integration

```python
# src/edugain_analysis/cli/main.py

parser.add_argument(
    "--benchmark",
    metavar="FEDERATION",
    help="Show benchmarking report for specific federation"
)
parser.add_argument(
    "--benchmark-all",
    action="store_true",
    help="Show full benchmarking report for all federations"
)
parser.add_argument(
    "--benchmark-top",
    type=int,
    default=5,
    metavar="N",
    help="Number of top performers to show (default: 5)"
)
parser.add_argument(
    "--json-benchmark",
    action="store_true",
    help="Export benchmark data as JSON"
)

def main():
    args = parser.parse_args()

    # ... metadata parsing and analysis ...

    # Generate benchmark report if requested
    if args.benchmark or args.benchmark_all:
        from ..core.benchmarking import generate_benchmark_report
        from ..formatters.benchmark import (
            print_benchmark_report,
            export_benchmark_csv,
            export_benchmark_json
        )

        report = generate_benchmark_report(
            federation_stats,
            target_federation=args.benchmark,
            top_n=args.benchmark_top
        )

        if args.json_benchmark:
            print(export_benchmark_json(report))
        elif args.csv == "benchmark":
            export_benchmark_csv(report)
        else:
            print_benchmark_report(
                report,
                target_federation=args.benchmark,
                show_all=args.benchmark_all
            )
```

## Success Metrics

- Federation operators can identify their competitive position
- Clear identification of improvement opportunities
- Peer comparison provides realistic targets
- Federations can track ranking changes over time (with historical data)
- "Best practice" federations identified for study
- All statistical calculations are accurate
- Performance overhead < 5%

## References

- Percentile calculation: https://en.wikipedia.org/wiki/Percentile
- Composite scoring: Similar to credit score models
- Peer benchmarking: Common in business intelligence tools
- Similar tools: AWS Trusted Advisor, Google Cloud Recommender

## Dependencies

**Optional Enhancement**: Combine with Historical Snapshot Storage (Feature 1.4) to track:
- Ranking changes over time
- Progress toward targets
- Peer group movement

**Future Extension**:
- Add "improvement simulator" (what-if analysis)
- Add "best practice extraction" (learn from top performers)
- Add "trend forecasting" (predict future rankings)
