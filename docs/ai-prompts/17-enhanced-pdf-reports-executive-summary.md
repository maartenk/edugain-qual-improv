# AI Implementation Prompt: Enhanced PDF Reports with Executive Summary

**Feature ID**: 2.5 from ROADMAP.md
**Priority**: MEDIUM
**Effort**: 3 weeks
**Type**: Report
**Dependencies**: Merge `feature/pdf-graphical-reports` branch (already merged to main)

## Objective

Enhance existing PDF reports with executive-friendly features including 1-page executive summary, traffic-light indicators, year-over-year comparisons, automated recommendations, cost-benefit analysis, and compliance forecasting to make reports suitable for leadership presentations and strategic planning.

## Context

**Current State**:
- PDF reports exist in main branch (merged from feature/pdf-graphical-reports)
- Reports contain detailed statistics and charts
- Focused on technical/operator audience
- Lacks executive summary for leadership
- No strategic recommendations or forecasting
- No year-over-year comparison capabilities

**Current PDF Structure**:
```
1. Metadata Overview (entity counts, federation breakdown)
2. Privacy Statement Analysis (charts, statistics)
3. Security Contact Analysis
4. SIRTFI Compliance
5. Per-Federation Statistics (tables)
```

**Enhanced PDF Structure**:
```
1. **Executive Summary** (NEW - 1 page)
   - Traffic-light status indicators
   - Overall federation grade (A-F)
   - Key trends (if historical data available)
   - Top 3 priorities for next quarter

2. Metadata Overview
   - Enhanced with YoY comparison (if available)
   - Progress toward goals

3. Privacy Statement Analysis
   - Enhanced with recommendations

4. Security Contact Analysis
   - Enhanced with recommendations

5. SIRTFI Compliance
   - Enhanced with recommendations

6. Per-Federation Statistics

7. **Recommendations & Action Plan** (NEW)
   - Prioritized action items
   - Cost-benefit analysis
   - Pareto charts (20% effort, 80% impact)

8. **Compliance Forecast** (NEW - if historical data)
   - Linear projection
   - Goal tracking
   - Timeline to targets
```

**Problem**:
- **Not executive-friendly**: Too detailed for leadership review
- **No actionable guidance**: Operators don't know what to do next
- **No strategic context**: Missing "so what?" and "what's next?"
- **Can't demonstrate progress**: No year-over-year comparison
- **No prioritization**: All issues presented equally

## Requirements

### Core Functionality

1. **1-Page Executive Summary**:

   **Traffic-Light Indicators**:
   ```python
   indicators = {
       "privacy_coverage": {
           "green": ">= 85%",
           "yellow": "70-84%",
           "red": "< 70%"
       },
       "security_contacts": {
           "green": ">= 80%",
           "yellow": "60-79%",
           "red": "< 60%"
       },
       "sirtfi_compliance": {
           "green": ">= 50%",
           "yellow": "30-49%",
           "red": "< 30%"
       }
   }
   ```

   **Overall Grade Calculation**:
   ```python
   # Weighted grade based on all metrics
   grade = calculate_overall_grade(
       privacy_weight=0.40,
       security_weight=0.35,
       sirtfi_weight=0.25
   )
   # Result: A/B/C/D/F
   ```

   **Key Trends** (if historical data available):
   - "▲ Privacy up 5.2% this quarter"
   - "▼ Security contacts down 2.1% this month"
   - "→ SIRTFI stable (no change)"

   **Top 3 Priorities**:
   - Auto-generated based on gaps and impact
   - "Fix 23 entities to reach 80% privacy coverage"
   - "Add security contacts to 156 entities"
   - "Investigate bot protection issues (15% validation failure)"

2. **Year-over-Year Comparison** (if historical data available):
   - Side-by-side comparison charts: 2025 vs. 2026
   - Improvement percentages with up/down arrows
   - Progress toward 80% compliance goal
   - Entities added/removed year-over-year

3. **Automated Recommendations Section**:

   **Rule-Based Recommendations**:
   ```python
   recommendations = [
       {
           "priority": "HIGH",
           "category": "Privacy",
           "action": "Add privacy statements to 23 SPs",
           "impact": "Increases coverage from 77% to 80% (+3%)",
           "effort": "LOW (template available)",
           "entities": ["sp1.edu", "sp2.org", ...]
       },
       {
           "priority": "MEDIUM",
           "category": "Security",
           "action": "Add security contacts to 156 entities",
           "impact": "Increases coverage from 45% to 60% (+15%)",
           "effort": "MEDIUM (requires coordination)",
       }
   ]
   ```

   **Prioritization Criteria**:
   - High impact, low effort = Priority 1
   - High impact, medium effort = Priority 2
   - Low impact or high effort = Priority 3

4. **Cost-Benefit Analysis**:
   - Pareto chart: "20% of effort → 80% of improvement"
   - Entity impact ranking:
     ```
     Top 10 Entities for Maximum Impact:
     1. sp1.edu - Missing: privacy, security contact (2 issues)
     2. sp2.org - Missing: privacy, security contact (2 issues)
     ...
     Fixing these 10 entities addresses 45% of all gaps
     ```

5. **Compliance Forecast** (if historical data available):
   - Linear regression: "At current rate, 80% coverage by Q3 2026"
   - Time-to-target calculation:
     ```
     Current: 77% privacy coverage
     Target: 85% coverage
     Trend: +1.2% per month
     Estimate: 6.7 months to target (Aug 2026)
     ```
   - Goal tracking:
     - 🟢 On track
     - 🟡 Behind schedule
     - 🔴 Not improving

6. **Enhanced Formatting**:
   - Professional branding (configurable federation logo)
   - Color-coded sections by status
   - Callout boxes for key findings
   - Footer with report date and version
   - Table of contents with hyperlinks

7. **CLI Flags**:
   ```bash
   # Generate enhanced PDF report
   edugain-analyze --pdf report.pdf --executive-summary

   # Include YoY comparison (requires historical data)
   edugain-analyze --pdf report.pdf --executive-summary --yoy-comparison

   # Custom branding
   edugain-analyze --pdf report.pdf --federation-logo logo.png

   # Recommendations only (no detailed analysis)
   edugain-analyze --pdf recommendations.pdf --recommendations-only
   ```

### Implementation Details

**Files to Modify**:

1. **`src/edugain_analysis/formatters/pdf.py`**:
   - Add `generate_executive_summary()` function
   - Add `generate_recommendations()` function
   - Add `generate_forecast()` function
   - Enhance existing sections with recommendations

2. **`src/edugain_analysis/core/recommendations.py`** (NEW):
   - Recommendation generation logic
   - Prioritization algorithms
   - Cost-benefit analysis

3. **`src/edugain_analysis/core/forecasting.py`** (NEW):
   - Linear regression for trend forecasting
   - Time-to-target calculations
   - Goal tracking logic

4. **`src/edugain_analysis/cli/main.py`**:
   - Add `--executive-summary` flag
   - Add `--yoy-comparison` flag
   - Add `--federation-logo` flag
   - Add `--recommendations-only` flag

**ReportLab Layout** (PDF generation):
```python
# Executive summary page
def generate_executive_summary(pdf_canvas, stats, historical_stats=None):
    # Title
    pdf_canvas.setFont("Helvetica-Bold", 24)
    pdf_canvas.drawString(50, 750, "Executive Summary")

    # Traffic lights (circles with colors)
    draw_traffic_light(pdf_canvas, x=50, y=650,
                      label="Privacy Coverage",
                      value=stats["privacy_coverage"],
                      thresholds={"green": 85, "yellow": 70})

    # Overall grade (large, prominent)
    grade = calculate_overall_grade(stats)
    pdf_canvas.setFont("Helvetica-Bold", 72)
    pdf_canvas.drawString(400, 650, grade)

    # Key trends (if available)
    if historical_stats:
        draw_trend_indicators(pdf_canvas, x=50, y=500,
                             current=stats, baseline=historical_stats)

    # Top 3 priorities
    pdf_canvas.setFont("Helvetica-Bold", 16)
    pdf_canvas.drawString(50, 400, "Top 3 Priorities:")
    # ... draw priorities
```

**Edge Cases**:
- No historical data: Skip YoY comparison, trends, and forecasting
- Single metric improved: Don't show "all metrics" language
- Perfect compliance (100%): Congratulatory message, no recommendations
- Very poor compliance (< 30%): Different recommendation strategy (focus on fundamentals)

## Acceptance Criteria

### Functional Requirements
- [ ] 1-page executive summary with traffic lights
- [ ] Overall grade (A-F) calculated and displayed prominently
- [ ] Recommendations section with prioritized actions
- [ ] Cost-benefit analysis (Pareto chart)
- [ ] YoY comparison (if historical data available)
- [ ] Compliance forecast (if historical data available)
- [ ] Traffic-light thresholds configurable
- [ ] Custom branding (federation logo)
- [ ] Professional PDF formatting with ToC
- [ ] `--recommendations-only` exports just recommendations

### Quality Requirements
- [ ] Executive summary fits on 1 page
- [ ] Recommendations are actionable and specific
- [ ] Prioritization algorithm produces sensible results
- [ ] Forecast is based on sound statistical methods
- [ ] PDF is professional and readable
- [ ] Colors are accessible (not just red/green)
- [ ] Performance overhead < 15% (PDF generation is slow)

### Testing Requirements
- [ ] Test executive summary generation
- [ ] Test recommendation prioritization
- [ ] Test forecast calculations
- [ ] Test YoY comparison (with mock historical data)
- [ ] Test PDF generation with all sections
- [ ] Test custom branding
- [ ] Visual review of PDF output

## Testing Strategy

**Unit Tests**:
```python
def test_calculate_overall_grade():
    """Test overall grade calculation."""
    stats = {
        "privacy_coverage": 85.0,  # Good
        "security_contact_coverage": 70.0,  # OK
        "sirtfi_compliance": 40.0,  # Low
    }

    grade = calculate_overall_grade(stats,
                                    weights={"privacy": 0.4, "security": 0.35, "sirtfi": 0.25})

    # Weighted average: 85*0.4 + 70*0.35 + 40*0.25 = 72.5 → C
    assert grade == "C"

def test_generate_recommendations():
    """Test recommendation generation."""
    stats = {
        "privacy_coverage": 77.0,  # Close to 80% threshold
        "entities_missing_privacy": 23,
        "security_contact_coverage": 45.0,
        "entities_missing_security": 156,
    }

    recommendations = generate_recommendations(stats)

    # Should prioritize privacy (closer to threshold, fewer entities)
    assert recommendations[0]["priority"] == "HIGH"
    assert recommendations[0]["category"] == "Privacy"
    assert recommendations[0]["action"].startswith("Add privacy statements")

def test_forecast_compliance():
    """Test compliance forecasting."""
    # Historical data showing 1% improvement per month
    historical = [
        {"date": "2025-09-01", "privacy_coverage": 71.0},
        {"date": "2025-10-01", "privacy_coverage": 72.0},
        {"date": "2025-11-01", "privacy_coverage": 73.0},
        {"date": "2025-12-01", "privacy_coverage": 74.0},
        {"date": "2026-01-01", "privacy_coverage": 75.0},
    ]

    forecast = forecast_time_to_target(
        historical_data=historical,
        current_value=75.0,
        target_value=85.0,
        metric="privacy_coverage"
    )

    # Should be ~10 months to reach 85%
    assert 9 <= forecast["months_to_target"] <= 11
    assert forecast["target_date"] is not None
```

## Implementation Guidance

### Step 1: Create Recommendations Module

```python
# src/edugain_analysis/core/recommendations.py

from typing import Dict, List

def generate_recommendations(stats: Dict, entities: List[Dict]) -> List[Dict]:
    """
    Generate prioritized recommendations.

    Args:
        stats: Statistics dictionary
        entities: List of entity dictionaries

    Returns:
        List of recommendation dictionaries, sorted by priority
    """
    recommendations = []

    # Privacy recommendation
    if stats["privacy_coverage"] < 85.0:
        missing_count = stats.get("entities_missing_privacy", 0)
        current_pct = stats["privacy_coverage"]

        # Calculate impact
        total_sps = stats.get("total_sps", 1)
        target_pct = 85.0
        entities_needed = int((target_pct - current_pct) / 100 * total_sps)

        recommendations.append({
            "priority": "HIGH" if entities_needed < 50 else "MEDIUM",
            "category": "Privacy",
            "action": f"Add privacy statements to {entities_needed} SPs",
            "current": f"{current_pct:.1f}%",
            "target": "85%",
            "impact": f"+{target_pct - current_pct:.1f}%",
            "effort": "LOW" if entities_needed < 30 else "MEDIUM",
            "details": "Focus on entities without privacy statements",
        })

    # Security contact recommendation
    if stats["security_contact_coverage"] < 80.0:
        # ... similar logic

    # SIRTFI recommendation
    # ... similar logic

    # Sort by priority (HIGH → MEDIUM → LOW)
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    recommendations.sort(key=lambda r: priority_order.get(r["priority"], 3))

    return recommendations

def calculate_pareto_entities(entities: List[Dict]) -> List[Dict]:
    """
    Identify entities that provide maximum impact (80/20 rule).

    Args:
        entities: List of entity dictionaries

    Returns:
        Sorted list of entities by impact potential
    """
    # Count issues per entity
    entity_impact = []

    for entity in entities:
        issues = []

        if not entity.get("has_privacy"):
            issues.append("privacy")

        if not entity.get("has_security_contact"):
            issues.append("security_contact")

        if not entity.get("has_sirtfi") and entity.get("entity_type") == "SP":
            issues.append("sirtfi")

        if issues:
            entity_impact.append({
                "entity_id": entity["entity_id"],
                "organization": entity.get("organization", ""),
                "issue_count": len(issues),
                "issues": issues,
            })

    # Sort by issue count (descending)
    entity_impact.sort(key=lambda e: e["issue_count"], reverse=True)

    return entity_impact[:20]  # Top 20
```

### Step 2: Create Forecasting Module

```python
# src/edugain_analysis/core/forecasting.py

from typing import Dict, List
from datetime import datetime, timedelta
import statistics

def forecast_time_to_target(
    historical_data: List[Dict],
    current_value: float,
    target_value: float,
    metric: str
) -> Dict:
    """
    Forecast time to reach target based on historical trend.

    Args:
        historical_data: List of historical snapshots
        current_value: Current metric value
        target_value: Target metric value
        metric: Metric name

    Returns:
        Forecast dictionary with months_to_target, target_date, trend_rate
    """
    if len(historical_data) < 2:
        return {"error": "Insufficient historical data"}

    # Extract values and calculate trend
    values = [snapshot[metric] for snapshot in historical_data if metric in snapshot]

    if len(values) < 2:
        return {"error": "Insufficient data points"}

    # Calculate linear trend (simple: delta / time)
    first_value = values[0]
    last_value = values[-1]

    first_date = datetime.fromisoformat(historical_data[0]["date"])
    last_date = datetime.fromisoformat(historical_data[-1]["date"])

    months_elapsed = (last_date - first_date).days / 30.0

    if months_elapsed == 0:
        return {"error": "No time elapsed"}

    # Trend rate (per month)
    trend_rate = (last_value - first_value) / months_elapsed

    if trend_rate <= 0:
        return {
            "status": "not_improving",
            "trend_rate": trend_rate,
            "message": "Metric is not improving"
        }

    # Calculate months to target
    gap = target_value - current_value
    months_to_target = gap / trend_rate

    # Calculate target date
    target_date = datetime.now() + timedelta(days=months_to_target * 30)

    return {
        "months_to_target": months_to_target,
        "target_date": target_date.strftime("%Y-%m-%d"),
        "trend_rate": trend_rate,
        "status": "on_track"
    }
```

### Step 3: Enhance PDF Generation

```python
# src/edugain_analysis/formatters/pdf.py

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(
    stats: Dict,
    entities: List[Dict],
    output_path: str,
    include_executive_summary: bool = True,
    historical_stats: Dict = None,
    federation_logo: str = None
):
    """
    Generate enhanced PDF report.

    Args:
        stats: Current statistics
        entities: Entity list
        output_path: PDF output path
        include_executive_summary: Include exec summary page
        historical_stats: Historical stats for YoY comparison
        federation_logo: Path to federation logo
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []

    # Executive summary (if enabled)
    if include_executive_summary:
        story.extend(generate_executive_summary_content(stats, historical_stats))
        story.append(PageBreak())

    # ... rest of existing report sections ...

    # Recommendations section (new)
    story.extend(generate_recommendations_content(stats, entities))
    story.append(PageBreak())

    # Build PDF
    doc.build(story)

def generate_executive_summary_content(stats: Dict, historical_stats: Dict = None) -> List:
    """Generate executive summary page content."""
    content = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366')
    )
    content.append(Paragraph("Executive Summary", title_style))
    content.append(Spacer(1, 20))

    # Traffic lights table
    traffic_lights = [
        ["Metric", "Status", "Value"],
        ["Privacy Coverage", get_traffic_light(stats["privacy_coverage"], 85, 70), f"{stats['privacy_coverage']:.1f}%"],
        ["Security Contacts", get_traffic_light(stats.get("security_contact_coverage", 0), 80, 60), f"{stats.get('security_contact_coverage', 0):.1f}%"],
    ]

    traffic_table = Table(traffic_lights, colWidths=[200, 100, 100])
    traffic_table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    content.append(traffic_table)

    # Overall grade
    grade = calculate_overall_grade(stats)
    content.append(Spacer(1, 20))
    content.append(Paragraph(f"<b>Overall Grade: {grade}</b>", styles['Heading2']))

    return content

def get_traffic_light(value: float, green_threshold: float, yellow_threshold: float) -> str:
    """Get traffic light emoji based on value and thresholds."""
    if value >= green_threshold:
        return "🟢"
    elif value >= yellow_threshold:
        return "🟡"
    else:
        return "🔴"

def calculate_overall_grade(stats: Dict) -> str:
    """Calculate overall grade based on weighted metrics."""
    # Weighted average
    privacy_weight = 0.40
    security_weight = 0.35
    sirtfi_weight = 0.25

    score = (
        stats.get("privacy_coverage", 0) * privacy_weight +
        stats.get("security_contact_coverage", 0) * security_weight +
        stats.get("sirtfi_compliance", 0) * sirtfi_weight
    )

    # Convert to grade
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
```

## Success Metrics

- Executive summary fits on 1 page and is readable by non-technical leadership
- Federation operators use recommendations to prioritize work
- Reports used in funding requests and strategic planning
- Positive feedback from federation leadership
- 50%+ of federations request custom branding
- Forecasts are accurate within 20% margin

## References

- ReportLab documentation: https://www.reportlab.com/docs/reportlab-userguide.pdf
- Executive dashboard best practices
- Traffic-light KPI visualizations

## Dependencies

**Required**:
- Existing PDF report generation (already in main)
- ReportLab library (already used)

**Optional**:
- Historical Snapshot Storage (Feature 1.4) for YoY comparison and forecasting
- Metadata Completeness Scoring (Feature 2.2) for grade calculation
