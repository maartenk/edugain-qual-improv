# AI Implementation Prompt: Entity Freshness & Activity Tracking

**Feature ID**: 3.4 from ROADMAP.md
**Priority**: LOW
**Effort**: 2-3 weeks
**Type**: Check

## Objective

Implement entity age and update frequency tracking to identify stale, abandoned, or unmaintained entities, enabling federations to clean up their metadata and maintain a healthy, actively-maintained entity roster.

## Context

**Current State**:
- Tool treats all entities equally regardless of age or maintenance status
- No visibility into entity registration dates or last update times
- Can't identify stale or abandoned entities
- No metrics for entity freshness or activity
- Federation operators don't know which entities to investigate for cleanup

**Problem Scenarios**:

**Abandoned Entities**: "We have entities that were registered 5 years ago, haven't been updated since, and their URLs are all broken. How do we find them?"
- Current limitation: Must manually check each entity
- Need: Automated stale entity detection

**Federation Cleanup**: "Which entities should we consider removing from our federation metadata?"
- Current limitation: No data-driven cleanup criteria
- Need: Entity age, activity, and health scoring

**Metadata Quality**: "What percentage of our entities are actively maintained vs. neglected?"
- Current limitation: No freshness metrics
- Need: Federation health dashboard

**Current Workflow** (Manual, Time-Consuming):
```
1. Export entity list
2. Manually check each entity's registration date (if available)
3. Try to access entity URLs
4. Check if technical contacts still respond
5. Make subjective judgment about "stale" vs. "active"
6. Time-consuming and inconsistent
```

**Improved Workflow** (Automated):
```
1. Run tool with freshness analysis:
   edugain-analyze --freshness-analysis

2. Get automated report:
   "456 entities (16.6%) are stale (not updated in 2+ years)
    89 entities (3.2%) are likely abandoned (stale + broken URLs)
    1,234 entities (44.9%) are mature (3-5 years old)

    Cleanup Candidates:
    - sp1.edu: 5 years old, last update 4 years ago, broken privacy URL
    - sp2.org: 6 years old, last update 5 years ago, no security contact
    ..."

3. Export cleanup candidates CSV
4. Contact entity operators or initiate removal process
```

## Requirements

### Core Functionality

1. **Entity Age Tracking**:

   Extract `registrationInstant` from `<RegistrationInfo>`:
   ```xml
   <mdrpi:RegistrationInfo registrationAuthority="http://ukfederation.org.uk"
                           registrationInstant="2015-03-24T12:00:00Z">
   ```

   Calculate entity age in days/years and categorize:
   ```python
   age_categories = {
       "new": "< 90 days",
       "recent": "90 days - 1 year",
       "established": "1-3 years",
       "mature": "3-5 years",
       "old": "> 5 years"
   }
   ```

2. **Last Updated Tracking**:

   Track when entity metadata was last modified:
   - Option 1: Use `validUntil` attribute (if available)
   - Option 2: Historical comparison (requires Feature 1.4)
   - Option 3: Track in metadata processing timestamp

   Calculate staleness:
   ```python
   staleness_thresholds = {
       "fresh": "< 6 months since update",
       "aging": "6-12 months since update",
       "stale": "12-24 months since update",
       "very_stale": "> 24 months since update"
   }
   ```

3. **Abandonment Detection**:

   Combine multiple signals to identify likely abandoned entities:
   ```python
   abandonment_indicators = {
       "stale_metadata": "Not updated in 2+ years",
       "broken_urls": "Privacy URL returns 404/timeout",
       "missing_contacts": "No technical or support contact",
       "old_age": "Entity > 5 years old",
       "inaccessible_org_url": "Organization URL broken"
   }

   # Abandonment score (0-5 points)
   abandonment_score = sum([
       2 if stale_metadata else 0,
       1 if broken_urls else 0,
       1 if missing_contacts else 0,
       1 if old_age else 0,
       1 if inaccessible_org_url else 0
   ])

   # Likely abandoned if score >= 3
   ```

4. **Statistics Tracking**:

   **Per-Entity**:
   - Registration date
   - Entity age (days, years)
   - Age category (new/recent/established/mature/old)
   - Last update date (if available)
   - Staleness status (fresh/aging/stale/very_stale)
   - Abandonment score (0-5)
   - Abandonment status (likely_abandoned / needs_attention / active)

   **Per-Federation**:
   - Average entity age
   - Age distribution (% in each category)
   - Stale entity count and percentage
   - Abandoned entity count and percentage
   - Freshness score (0-100)

5. **CSV Export**:

   Add columns:
   - `RegistrationDate` (YYYY-MM-DD)
   - `EntityAgeYears` (decimal)
   - `AgeCategory` (new/recent/established/mature/old)
   - `LastUpdateDate` (YYYY-MM-DD, if available)
   - `StalenessStatus` (fresh/aging/stale/very_stale)
   - `AbandonmentScore` (0-5)
   - `IsLikelyAbandoned` (Yes/No)

   New export modes:
   ```bash
   # Export stale entities only
   --csv stale-entities

   # Export cleanup candidates (abandonment score >= 3)
   --csv cleanup-candidates

   # Export by age category
   --csv entities --filter-age-category old
   ```

6. **Summary Output**:

   ```
   📅 Entity Freshness & Activity:

   Age Distribution:
     New (< 90d): 234 entities (8.5%)
     Recent (90d-1y): 456 entities (16.6%)
     Established (1-3y): 892 entities (32.4%)
     Mature (3-5y): 678 entities (24.6%)
     Old (> 5y): 490 entities (17.8%)

   Staleness Analysis:
     Fresh (< 6mo): 1,234 entities (44.9%)
     Aging (6-12mo): 567 entities (20.6%)
     Stale (12-24mo): 345 entities (12.5%)
     Very Stale (> 24mo): 604 entities (22.0%)

   Abandonment Detection:
     Likely Abandoned (score >= 3): 89 entities (3.2%)
     Needs Attention (score = 2): 156 entities (5.7%)
     Active: 2,505 entities (91.1%)

   Cleanup Candidates (Top 10 by abandonment score):
     1. sp1.edu (score: 5) - 6y old, 4y stale, broken URLs
     2. sp2.org (score: 5) - 7y old, 5y stale, no contacts
     ...

   Federation Health Score: 78/100
     (Based on: avg age, staleness, abandonment rate)
   ```

7. **Federation Health Score**:

   Calculate 0-100 health score based on:
   ```python
   health_score = (
       (1 - stale_percentage) * 40 +           # 40 points: low staleness
       (1 - abandoned_percentage) * 30 +       # 30 points: few abandoned
       (fresh_percentage) * 20 +               # 20 points: high freshness
       (1 - very_old_percentage) * 10          # 10 points: not too old
   )
   ```

### Implementation Details

**Files to Create**:

1. **`src/edugain_analysis/core/freshness.py`** (NEW):
   - Registration date parsing
   - Age calculation and categorization
   - Staleness detection
   - Abandonment scoring
   - Health score calculation

2. **`src/edugain_analysis/core/analysis.py`**:
   - Call freshness analysis during entity parsing
   - Extract `registrationInstant` from metadata
   - Calculate and store freshness metrics

3. **`src/edugain_analysis/formatters/base.py`**:
   - Add freshness summary section
   - Display age distribution
   - Show cleanup candidates
   - Export freshness CSV

4. **`src/edugain_analysis/cli/main.py`**:
   - Add `--freshness-analysis` flag
   - Add `--csv stale-entities`, `--csv cleanup-candidates`
   - Add `--filter-age-category` flag

**Edge Cases**:
- Missing `registrationInstant`: Treat as "unknown age" (don't categorize)
- Future registration date: Flag as error (invalid metadata)
- `validUntil` not present: Use historical comparison if available
- No historical data: Can't determine staleness (skip)
- Broken URLs during validation: Factor into abandonment score

## Acceptance Criteria

### Functional Requirements
- [ ] Registration date extracted from metadata
- [ ] Entity age calculated correctly (days and years)
- [ ] Age categorization (new/recent/established/mature/old)
- [ ] Staleness detection (if historical data available)
- [ ] Abandonment scoring (0-5 based on multiple indicators)
- [ ] Federation health score (0-100)
- [ ] CSV export includes all freshness columns
- [ ] `--csv cleanup-candidates` exports entities with high abandonment scores
- [ ] Summary shows age distribution and staleness statistics

### Quality Requirements
- [ ] Age calculations are accurate (timezone-aware)
- [ ] Abandonment scoring is reasonable and consistent
- [ ] No false positives (active entities flagged as abandoned)
- [ ] Health score correlates with actual federation quality
- [ ] Performance overhead < 3%
- [ ] Works without historical data (limited features)

### Testing Requirements
- [ ] Test registration date parsing
- [ ] Test age calculation with various dates
- [ ] Test age categorization boundaries
- [ ] Test abandonment scoring logic
- [ ] Test health score calculation
- [ ] Test CSV export with freshness columns
- [ ] Integration test with real metadata sample

## Testing Strategy

**Unit Tests**:
```python
def test_calculate_entity_age():
    """Test entity age calculation."""
    from datetime import datetime, timedelta

    # Entity registered 3.5 years ago
    registration_date = datetime.now() - timedelta(days=365*3.5)
    age_days, age_years = calculate_entity_age(registration_date.isoformat())

    assert age_days == pytest.approx(365*3.5, rel=1)
    assert age_years == pytest.approx(3.5, rel=0.1)

def test_categorize_entity_age():
    """Test age categorization."""
    assert categorize_age(50) == "new"          # 50 days = new
    assert categorize_age(200) == "recent"      # 200 days = recent
    assert categorize_age(730) == "established" # 2 years = established
    assert categorize_age(1460) == "mature"     # 4 years = mature
    assert categorize_age(2190) == "old"        # 6 years = old

def test_calculate_abandonment_score():
    """Test abandonment scoring."""
    entity_data = {
        "age_years": 6,                    # Old: +1 point
        "staleness_status": "very_stale",  # Very stale: +2 points
        "privacy_url_accessible": False,   # Broken URL: +1 point
        "has_security_contact": False,     # No contact: +1 point
        "org_url_accessible": True,        # OK: 0 points
    }

    score = calculate_abandonment_score(entity_data)

    # Should be 5 (old + very_stale*2 + broken_url + no_contact)
    assert score == 5

def test_calculate_health_score():
    """Test federation health score."""
    stats = {
        "stale_percentage": 10.0,        # 10% stale
        "abandoned_percentage": 2.0,     # 2% abandoned
        "fresh_percentage": 60.0,        # 60% fresh
        "very_old_percentage": 15.0,     # 15% very old
    }

    health_score = calculate_health_score(stats)

    # (1-0.1)*40 + (1-0.02)*30 + 0.6*20 + (1-0.15)*10 = 36 + 29.4 + 12 + 8.5 = 85.9
    assert health_score == pytest.approx(85.9, rel=0.1)
```

## Implementation Guidance

### Step 1: Create Freshness Analysis Module

```python
# src/edugain_analysis/core/freshness.py

from datetime import datetime, timezone
from typing import Dict, Tuple

def parse_registration_date(registration_instant: str) -> datetime | None:
    """
    Parse ISO 8601 registration instant to datetime.

    Args:
        registration_instant: ISO 8601 timestamp string

    Returns:
        Datetime object or None if invalid
    """
    if not registration_instant:
        return None

    try:
        # Handle both with and without timezone
        if 'Z' in registration_instant:
            dt = datetime.fromisoformat(registration_instant.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(registration_instant)

        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    except (ValueError, AttributeError):
        return None

def calculate_entity_age(registration_date: datetime) -> Tuple[int, float]:
    """
    Calculate entity age in days and years.

    Args:
        registration_date: Registration datetime

    Returns:
        Tuple of (age_days, age_years)
    """
    if not registration_date:
        return (0, 0.0)

    now = datetime.now(timezone.utc)
    delta = now - registration_date

    age_days = delta.days
    age_years = age_days / 365.25  # Account for leap years

    return (age_days, age_years)

def categorize_age(age_days: int) -> str:
    """
    Categorize entity age.

    Args:
        age_days: Entity age in days

    Returns:
        Age category string
    """
    if age_days < 90:
        return "new"
    elif age_days < 365:
        return "recent"
    elif age_days < 365 * 3:
        return "established"
    elif age_days < 365 * 5:
        return "mature"
    else:
        return "old"

def calculate_staleness(
    last_update_date: datetime | None,
    current_date: datetime = None
) -> str:
    """
    Calculate staleness based on last update date.

    Args:
        last_update_date: Last update datetime
        current_date: Current date (defaults to now)

    Returns:
        Staleness status string
    """
    if not last_update_date:
        return "unknown"

    if current_date is None:
        current_date = datetime.now(timezone.utc)

    delta = current_date - last_update_date
    days_stale = delta.days

    if days_stale < 180:  # 6 months
        return "fresh"
    elif days_stale < 365:  # 1 year
        return "aging"
    elif days_stale < 730:  # 2 years
        return "stale"
    else:
        return "very_stale"

def calculate_abandonment_score(entity_data: Dict) -> int:
    """
    Calculate abandonment score (0-5).

    Args:
        entity_data: Entity metadata dictionary

    Returns:
        Abandonment score (higher = more likely abandoned)
    """
    score = 0

    # Very stale metadata (2+ years): +2 points
    if entity_data.get("staleness_status") == "very_stale":
        score += 2

    # Old entity (5+ years): +1 point
    if entity_data.get("age_years", 0) >= 5:
        score += 1

    # Broken privacy URL: +1 point
    if not entity_data.get("privacy_url_accessible", True):
        score += 1

    # Missing contacts: +1 point
    if not entity_data.get("has_security_contact") and not entity_data.get("has_support_contact"):
        score += 1

    # Broken organization URL: +1 point (rare, only if checked)
    if "org_url_accessible" in entity_data and not entity_data["org_url_accessible"]:
        score += 1

    return min(score, 5)  # Cap at 5

def categorize_abandonment(score: int) -> str:
    """
    Categorize abandonment status.

    Args:
        score: Abandonment score (0-5)

    Returns:
        Abandonment category
    """
    if score >= 3:
        return "likely_abandoned"
    elif score >= 2:
        return "needs_attention"
    else:
        return "active"

def calculate_health_score(federation_stats: Dict) -> float:
    """
    Calculate federation health score (0-100).

    Args:
        federation_stats: Federation statistics with percentages

    Returns:
        Health score (0-100)
    """
    stale_pct = federation_stats.get("stale_percentage", 0) / 100
    abandoned_pct = federation_stats.get("abandoned_percentage", 0) / 100
    fresh_pct = federation_stats.get("fresh_percentage", 0) / 100
    very_old_pct = federation_stats.get("very_old_percentage", 0) / 100

    # Weighted health score
    health = (
        (1 - stale_pct) * 40 +        # Low staleness: 40 points
        (1 - abandoned_pct) * 30 +    # Few abandoned: 30 points
        fresh_pct * 20 +              # High freshness: 20 points
        (1 - very_old_pct) * 10       # Not too old: 10 points
    )

    return round(health, 1)
```

### Step 2: Integrate with Analysis

```python
# src/edugain_analysis/core/analysis.py

from .freshness import (
    parse_registration_date,
    calculate_entity_age,
    categorize_age,
    calculate_staleness,
    calculate_abandonment_score,
    categorize_abandonment,
    calculate_health_score
)

def analyze_privacy_security(root: ET.Element) -> tuple[dict, list]:
    """
    Analyze with freshness tracking.
    """
    stats = {
        # ... existing stats ...

        # Freshness statistics
        "age_distribution": {"new": 0, "recent": 0, "established": 0, "mature": 0, "old": 0},
        "staleness_distribution": {"fresh": 0, "aging": 0, "stale": 0, "very_stale": 0, "unknown": 0},
        "abandonment_distribution": {"likely_abandoned": 0, "needs_attention": 0, "active": 0},
    }

    entities_list = []

    for entity_elem in root.findall(".//md:EntityDescriptor", ns):
        # ... existing entity parsing ...

        # Extract registration info
        reg_info = entity_elem.find(".//mdrpi:RegistrationInfo", ns)
        registration_date = None
        if reg_info is not None:
            reg_instant = reg_info.get("registrationInstant")
            if reg_instant:
                registration_date = parse_registration_date(reg_instant)

        # Calculate age
        age_days, age_years = calculate_entity_age(registration_date) if registration_date else (0, 0.0)
        age_category = categorize_age(age_days) if registration_date else "unknown"

        # Calculate staleness (requires historical data - optional)
        staleness_status = "unknown"  # Default if no historical data
        # TODO: Integrate with historical snapshot storage

        # Calculate abandonment
        entity_metadata = {
            "age_years": age_years,
            "staleness_status": staleness_status,
            "privacy_url_accessible": entity_data.get("privacy_url_accessible", True),
            "has_security_contact": entity_data.get("has_security_contact", False),
        }
        abandonment_score = calculate_abandonment_score(entity_metadata)
        abandonment_status = categorize_abandonment(abandonment_score)

        # Update statistics
        if age_category != "unknown":
            stats["age_distribution"][age_category] += 1
        stats["staleness_distribution"][staleness_status] += 1
        stats["abandonment_distribution"][abandonment_status] += 1

        # Store in entity data
        entity_data = {
            # ... existing fields ...
            "registration_date": registration_date.isoformat() if registration_date else None,
            "age_days": age_days,
            "age_years": age_years,
            "age_category": age_category,
            "staleness_status": staleness_status,
            "abandonment_score": abandonment_score,
            "abandonment_status": abandonment_status,
        }

        entities_list.append(entity_data)

    return stats, entities_list
```

### Step 3: Update Summary Output

```python
# src/edugain_analysis/formatters/base.py

def print_freshness_summary(stats: dict, entities: list[dict]):
    """
    Print entity freshness summary.

    Args:
        stats: Statistics dictionary
        entities: Entity list for cleanup candidates
    """
    print("\n📅 Entity Freshness & Activity:")

    # Age distribution
    print("\n  Age Distribution:")
    total = sum(stats["age_distribution"].values())
    for category, count in stats["age_distribution"].items():
        pct = (count / total * 100) if total > 0 else 0
        print(f"    {category.title()}: {count:,} entities ({pct:.1f}%)")

    # Staleness
    print("\n  Staleness Analysis:")
    for status, count in stats["staleness_distribution"].items():
        if status != "unknown":
            pct = (count / total * 100) if total > 0 else 0
            print(f"    {status.title().replace('_', ' ')}: {count:,} entities ({pct:.1f}%)")

    # Abandonment
    print("\n  Abandonment Detection:")
    for status, count in stats["abandonment_distribution"].items():
        pct = (count / total * 100) if total > 0 else 0
        print(f"    {status.title().replace('_', ' ')}: {count:,} entities ({pct:.1f}%)")

    # Cleanup candidates
    cleanup_candidates = [
        e for e in entities
        if e.get("abandonment_score", 0) >= 3
    ]

    if cleanup_candidates:
        print(f"\n  Cleanup Candidates (Top 10 by abandonment score):")
        cleanup_candidates.sort(key=lambda e: e.get("abandonment_score", 0), reverse=True)

        for i, entity in enumerate(cleanup_candidates[:10], start=1):
            age = entity.get("age_years", 0)
            score = entity.get("abandonment_score", 0)
            print(f"    {i}. {entity['entity_id']} (score: {score}) - {age:.1f}y old")

    # Health score
    health_score = calculate_health_score({
        "stale_percentage": stats["staleness_distribution"].get("stale", 0) / total * 100,
        "abandoned_percentage": stats["abandonment_distribution"].get("likely_abandoned", 0) / total * 100,
        "fresh_percentage": stats["staleness_distribution"].get("fresh", 0) / total * 100,
        "very_old_percentage": stats["age_distribution"].get("old", 0) / total * 100,
    })

    print(f"\n  Federation Health Score: {health_score:.0f}/100")
```

## Success Metrics

- Stale entities identified accurately (> 90% accuracy)
- Abandonment detection has < 10% false positive rate
- Federation operators use cleanup recommendations
- Average federation health score improves over time
- Reduction in unmaintained entities across eduGAIN
- All tests pass with 100% coverage

## References

- ISO 8601 date/time format for `registrationInstant`
- MDRPI (Metadata Registration Practice Info) specification
- Entity lifecycle management best practices

## Dependencies

**Optional**:
- Historical Snapshot Storage (Feature 1.4) for staleness detection
- Privacy URL Content Quality (Feature 1.8) for URL accessibility data

**Future Enhancement**:
- Integrate with Alerting System (Feature 2.6) to alert on abandoned entities
- Integrate with PDF Reports (Feature 2.5) to include freshness analysis
