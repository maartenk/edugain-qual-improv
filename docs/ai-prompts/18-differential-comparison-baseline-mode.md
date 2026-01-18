# AI Implementation Prompt: Differential Comparison & Baseline Mode

**Feature ID**: 3.2 from ROADMAP.md
**Priority**: MEDIUM
**Effort**: 4 weeks
**Type**: Report, Infrastructure
**Dependencies**: Historical Snapshot Storage (Feature 1.4)

## Objective

Implement baseline comparison capabilities to track specific changes between snapshots, enabling precise measurement of intervention effectiveness, campaign ROI, policy impact assessment, and regression investigation.

## Context

**Current State**:
- Tool shows current state only
- No comparison to previous states
- Can't measure intervention effectiveness
- Can't identify which specific entities changed
- No way to tag snapshots for later comparison
- Federation operators can't prove campaign ROI

**Problem Scenarios**:

**Campaign Effectiveness**: "We sent emails to 50 entities last month asking them to add privacy statements. How many actually fixed their issues?"
- Current limitation: Can't answer this question
- Need: Compare current state to pre-campaign baseline

**Policy Impact**: "After requiring SIRTFI compliance for new entities in Q4 2025, how did compliance change?"
- Current limitation: Only see current compliance rate
- Need: Compare Q4 2025 to Q1 2026, identify new entities

**Regression Investigation**: "Our compliance dropped 5% between Tuesday and Wednesday. What changed?"
- Current limitation: Must manually compare CSV exports
- Need: Automated differential analysis

**Current Workflow** (Manual, Error-Prone):
```
1. Export CSV before campaign → baseline.csv
2. Wait for intervention to take effect
3. Export CSV after campaign → current.csv
4. Manually compare files (Excel, diff tool, etc.)
5. Count changed entities by hand
6. Error-prone and time-consuming
```

**Improved Workflow** (Automated):
```
1. Tag snapshot before campaign:
   edugain-analyze --snapshot-tag "pre-email-campaign"

2. Run campaign, wait for changes

3. Compare to tagged baseline:
   edugain-analyze --compare-to-tag "pre-email-campaign"

4. Get detailed change report:
   "12 entities improved (added privacy statements)
    3 entities regressed (removed contacts)
    8 new entities added
    2 entities removed
    Net change: +9 compliant entities (+0.7%)"

5. Export differential CSV with change indicators
```

## Requirements

### Core Functionality

1. **Baseline Selection Methods**:

   ```bash
   # Compare to specific date
   edugain-analyze --baseline 2025-12-01

   # Compare to relative time
   edugain-analyze --baseline 1w   # 1 week ago
   edugain-analyze --baseline 1m   # 1 month ago
   edugain-analyze --baseline 3m   # 3 months ago

   # Compare to tagged snapshot
   edugain-analyze --compare-to-tag "pre-campaign"

   # Compare two specific snapshots (date range)
   edugain-analyze --compare-range 2025-12-01 2026-01-01
   ```

2. **Snapshot Tagging**:

   ```bash
   # Create tagged snapshot
   edugain-analyze --snapshot-tag "pre-email-campaign"

   # List all tagged snapshots
   edugain-analyze --list-tags

   # Show snapshot details
   edugain-analyze --show-tag "pre-email-campaign"

   # Delete tag (keep snapshot)
   edugain-analyze --delete-tag "pre-email-campaign"
   ```

3. **Change Detection**:

   **Improved Entities**:
   - Added privacy statement
   - Added security contact
   - Gained SIRTFI compliance
   - Fixed broken privacy URL

   **Regressed Entities**:
   - Removed privacy statement
   - Removed security contact
   - Lost SIRTFI compliance
   - Privacy URL now broken

   **New Entities**:
   - Present in current, absent in baseline
   - Track: entity_id, type, compliance status

   **Removed Entities**:
   - Present in baseline, absent in current
   - Track: why removed (federation cleanup, etc.)

   **Unchanged Entities**:
   - Still compliant or still non-compliant
   - No action needed

4. **Differential Reports**:

   **Summary Report**:
   ```
   📊 Change Summary (comparing to baseline: 2025-12-01)

   Timeframe: 2025-12-01 to 2026-01-18 (48 days)

   Entity Changes:
     ✅ Improved: 12 entities
     ⚠️  Regressed: 3 entities
     ✦  New: 8 entities
     ✗  Removed: 2 entities
     →  Unchanged: 2,725 entities

   Compliance Change:
     Privacy Coverage:
       Baseline: 77.2% (2,123 / 2,750 SPs)
       Current: 77.9% (2,143 / 2,750 SPs)
       Change: +0.7% (+20 compliant SPs)

     Security Contacts:
       Baseline: 45.1%
       Current: 46.3%
       Change: +1.2%

   Top Improvements:
     1. InCommon: +8 entities fixed privacy statements
     2. GÉANT: +3 entities added security contacts
     3. DFN-AAI: +1 entity gained SIRTFI

   Regressions:
     1. FederationX: -2 entities lost security contacts
     2. FederationY: -1 entity privacy URL now broken
   ```

   **Detailed CSV Export**:
   ```csv
   EntityID,ChangeStatus,ChangeType,Baseline,Current,Details
   https://sp1.edu,improved,privacy,No,Yes,"Added privacy statement"
   https://sp2.org,improved,privacy,No,Yes,"Added privacy statement"
   https://sp3.edu,improved,security,No,Yes,"Added security contact"
   https://sp4.org,regressed,privacy,Yes,No,"Privacy statement removed"
   https://sp5.edu,new,,,,"New entity added (non-compliant)"
   https://sp6.org,removed,,,,"Entity removed from federation"
   https://sp7.edu,unchanged_compliant,,,,"Still compliant (no change)"
   https://sp8.org,unchanged_noncompliant,,,,"Still non-compliant"
   ```

5. **Intervention Attribution**:

   Associate snapshots with interventions:
   ```bash
   # Tag with description
   edugain-analyze --snapshot-tag "post-email-campaign" \
                   --tag-description "After sending privacy statement reminders to 50 SPs"

   # Later, compare and see description
   edugain-analyze --compare-to-tag "post-email-campaign"
   # Output includes: "Comparing to: post-email-campaign (After sending privacy statement reminders...)"
   ```

6. **Filter Change Types**:

   ```bash
   # Show only improved entities
   edugain-analyze --compare-to-tag "baseline" --csv changes --filter improved

   # Show only regressions
   edugain-analyze --compare-to-tag "baseline" --csv changes --filter regressed

   # Show new entities only
   edugain-analyze --compare-to-tag "baseline" --csv changes --filter new
   ```

### Implementation Details

**Files to Create**:

1. **`src/edugain_analysis/core/comparison.py`** (NEW):
   - Differential analysis functions
   - Entity change detection
   - Change classification

2. **`src/edugain_analysis/core/snapshots.py`** (NEW):
   - Snapshot tagging functions
   - Tag management
   - Tag storage in database

3. **`src/edugain_analysis/formatters/diff.py`** (NEW):
   - Differential report formatting
   - Change summary output
   - CSV export with change indicators

4. **`src/edugain_analysis/cli/main.py`**:
   - Add `--baseline`, `--compare-to-tag`, `--compare-range` flags
   - Add `--snapshot-tag`, `--list-tags`, `--show-tag`, `--delete-tag`
   - Add `--csv changes --filter <type>`

**Database Schema Extension** (extend `history.db`):

```sql
-- Snapshot tags
CREATE TABLE snapshot_tags (
    tag_name TEXT PRIMARY KEY,
    snapshot_id INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    description TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
);

CREATE INDEX idx_snapshot_tags_snapshot ON snapshot_tags(snapshot_id);
```

**Edge Cases**:
- No baseline found: Clear error message with available dates
- Baseline same as current: Report "no changes"
- Entity ID changed: Can't track (treat as removed + new)
- Multiple tags point to same snapshot: Allow, warn user
- Tag name conflicts: Prevent, return error
- Baseline from future date: Error (can't compare to future)

## Acceptance Criteria

### Functional Requirements
- [ ] Baseline comparison by date (`--baseline YYYY-MM-DD`)
- [ ] Baseline comparison by relative time (`--baseline 1w`, `1m`, etc.)
- [ ] Snapshot tagging (`--snapshot-tag "name"`)
- [ ] Tag management (list, show, delete tags)
- [ ] Change detection (improved, regressed, new, removed, unchanged)
- [ ] Differential summary report
- [ ] CSV export with change indicators
- [ ] Filter by change type (`--filter improved`, etc.)
- [ ] Tag descriptions for intervention attribution

### Quality Requirements
- [ ] Change detection is accurate (no false positives/negatives)
- [ ] All entity changes tracked correctly
- [ ] Summary statistics match detailed changes
- [ ] Performance acceptable for 10,000+ entities
- [ ] Clear error messages for invalid baselines
- [ ] Tag names are case-insensitive
- [ ] Tags are immutable (can't change target snapshot)

### Testing Requirements
- [ ] Test change detection for each change type
- [ ] Test snapshot tagging and retrieval
- [ ] Test baseline selection methods
- [ ] Test CSV export with change indicators
- [ ] Test filtering by change type
- [ ] Test edge cases (no baseline, no changes, etc.)
- [ ] Integration test with real historical data

## Testing Strategy

**Unit Tests**:
```python
def test_detect_entity_changes():
    """Test change detection."""
    baseline_entities = [
        {"entity_id": "sp1.edu", "has_privacy": False, "has_security_contact": True},
        {"entity_id": "sp2.org", "has_privacy": True, "has_security_contact": False},
        {"entity_id": "sp3.edu", "has_privacy": False, "has_security_contact": False},
    ]

    current_entities = [
        {"entity_id": "sp1.edu", "has_privacy": True, "has_security_contact": True},  # Improved (privacy)
        {"entity_id": "sp2.org", "has_privacy": True, "has_security_contact": True},  # Improved (security)
        {"entity_id": "sp3.edu", "has_privacy": False, "has_security_contact": False},  # Unchanged
        {"entity_id": "sp4.org", "has_privacy": False, "has_security_contact": False},  # New
    ]

    changes = detect_entity_changes(baseline_entities, current_entities)

    assert changes["sp1.edu"]["status"] == "improved"
    assert changes["sp1.edu"]["change_type"] == "privacy"
    assert changes["sp2.org"]["status"] == "improved"
    assert changes["sp2.org"]["change_type"] == "security"
    assert changes["sp3.edu"]["status"] == "unchanged_noncompliant"
    assert changes["sp4.org"]["status"] == "new"

def test_snapshot_tagging():
    """Test snapshot tagging."""
    snapshot_id = 123
    tag_name = "test-campaign"
    description = "After email campaign"

    # Create tag
    create_snapshot_tag(tag_name, snapshot_id, description)

    # Retrieve tag
    tag = get_snapshot_tag(tag_name)

    assert tag["tag_name"] == tag_name
    assert tag["snapshot_id"] == snapshot_id
    assert tag["description"] == description

def test_calculate_change_statistics():
    """Test change statistics calculation."""
    changes = {
        "sp1.edu": {"status": "improved"},
        "sp2.org": {"status": "improved"},
        "sp3.edu": {"status": "regressed"},
        "sp4.org": {"status": "new"},
        "sp5.edu": {"status": "unchanged_compliant"},
    }

    stats = calculate_change_statistics(changes)

    assert stats["improved"] == 2
    assert stats["regressed"] == 1
    assert stats["new"] == 1
    assert stats["unchanged"] == 1
```

## Implementation Guidance

### Step 1: Create Comparison Module

```python
# src/edugain_analysis/core/comparison.py

from typing import Dict, List

def detect_entity_changes(
    baseline_entities: List[Dict],
    current_entities: List[Dict]
) -> Dict[str, Dict]:
    """
    Detect changes between baseline and current entity lists.

    Args:
        baseline_entities: Baseline entity list
        current_entities: Current entity list

    Returns:
        Dictionary mapping entity_id to change information
    """
    changes = {}

    # Index entities by entity_id
    baseline_by_id = {e["entity_id"]: e for e in baseline_entities}
    current_by_id = {e["entity_id"]: e for e in current_entities}

    # Check all current entities
    for entity_id, current in current_by_id.items():
        if entity_id not in baseline_by_id:
            # New entity
            changes[entity_id] = {
                "status": "new",
                "current": current,
            }
        else:
            # Existing entity - check for changes
            baseline = baseline_by_id[entity_id]
            change = detect_entity_change(baseline, current)
            changes[entity_id] = change

    # Check for removed entities
    for entity_id, baseline in baseline_by_id.items():
        if entity_id not in current_by_id:
            changes[entity_id] = {
                "status": "removed",
                "baseline": baseline,
            }

    return changes

def detect_entity_change(baseline: Dict, current: Dict) -> Dict:
    """
    Detect specific changes for an entity.

    Args:
        baseline: Baseline entity data
        current: Current entity data

    Returns:
        Change information dictionary
    """
    change_types = []

    # Check privacy statement
    if not baseline.get("has_privacy") and current.get("has_privacy"):
        change_types.append("privacy_added")
    elif baseline.get("has_privacy") and not current.get("has_privacy"):
        change_types.append("privacy_removed")

    # Check security contact
    if not baseline.get("has_security_contact") and current.get("has_security_contact"):
        change_types.append("security_added")
    elif baseline.get("has_security_contact") and not current.get("has_security_contact"):
        change_types.append("security_removed")

    # Check SIRTFI
    if not baseline.get("has_sirtfi") and current.get("has_sirtfi"):
        change_types.append("sirtfi_gained")
    elif baseline.get("has_sirtfi") and not current.get("has_sirtfi"):
        change_types.append("sirtfi_lost")

    # Determine overall status
    if any("added" in ct or "gained" in ct for ct in change_types):
        status = "improved"
    elif any("removed" in ct or "lost" in ct for ct in change_types):
        status = "regressed"
    else:
        # Unchanged
        is_compliant = current.get("has_privacy") and current.get("has_security_contact")
        status = "unchanged_compliant" if is_compliant else "unchanged_noncompliant"

    return {
        "status": status,
        "change_types": change_types,
        "baseline": baseline,
        "current": current,
    }

def calculate_change_statistics(changes: Dict[str, Dict]) -> Dict:
    """
    Calculate summary statistics from change dictionary.

    Args:
        changes: Dictionary of entity changes

    Returns:
        Statistics dictionary
    """
    stats = {
        "improved": 0,
        "regressed": 0,
        "new": 0,
        "removed": 0,
        "unchanged_compliant": 0,
        "unchanged_noncompliant": 0,
    }

    for change in changes.values():
        status = change["status"]
        if status in stats:
            stats[status] += 1

    stats["total_changed"] = stats["improved"] + stats["regressed"]
    stats["total_unchanged"] = stats["unchanged_compliant"] + stats["unchanged_noncompliant"]

    return stats
```

### Step 2: Create Snapshot Management Module

```python
# src/edugain_analysis/core/snapshots.py

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

def create_snapshot_tag(
    tag_name: str,
    snapshot_id: int,
    description: str = None
):
    """
    Create a named tag for a snapshot.

    Args:
        tag_name: Tag name (unique)
        snapshot_id: Snapshot ID to tag
        description: Optional description
    """
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO snapshot_tags (tag_name, snapshot_id, created_at, description)
            VALUES (?, ?, ?, ?)
        """, (tag_name.lower(), snapshot_id, int(datetime.now().timestamp()), description))

        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"Tag '{tag_name}' already exists")
    finally:
        conn.close()

def get_snapshot_tag(tag_name: str) -> Optional[Dict]:
    """
    Retrieve snapshot tag information.

    Args:
        tag_name: Tag name

    Returns:
        Tag dictionary or None if not found
    """
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tag_name, snapshot_id, created_at, description
        FROM snapshot_tags
        WHERE LOWER(tag_name) = LOWER(?)
    """, (tag_name,))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "tag_name": result[0],
            "snapshot_id": result[1],
            "created_at": result[2],
            "description": result[3],
        }

    return None

def list_snapshot_tags() -> List[Dict]:
    """
    List all snapshot tags.

    Returns:
        List of tag dictionaries
    """
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tag_name, snapshot_id, created_at, description
        FROM snapshot_tags
        ORDER BY created_at DESC
    """)

    results = cursor.fetchall()
    conn.close()

    return [
        {
            "tag_name": r[0],
            "snapshot_id": r[1],
            "created_at": r[2],
            "description": r[3],
        }
        for r in results
    ]

def delete_snapshot_tag(tag_name: str):
    """
    Delete a snapshot tag (snapshot itself remains).

    Args:
        tag_name: Tag name to delete
    """
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM snapshot_tags WHERE LOWER(tag_name) = LOWER(?)", (tag_name,))

    if cursor.rowcount == 0:
        raise ValueError(f"Tag '{tag_name}' not found")

    conn.commit()
    conn.close()

def get_baseline_snapshot(baseline_spec: str) -> Optional[int]:
    """
    Get snapshot ID for baseline specification.

    Args:
        baseline_spec: Baseline specification (date, relative time, or tag)

    Returns:
        Snapshot ID or None if not found
    """
    # Check if it's a tag
    if not baseline_spec[0].isdigit():
        tag = get_snapshot_tag(baseline_spec)
        if tag:
            return tag["snapshot_id"]

    # Check if it's a relative time (1w, 1m, etc.)
    if baseline_spec[-1] in ('w', 'm', 'd'):
        # Parse relative time and find closest snapshot
        # ... implementation ...
        pass

    # Otherwise treat as date
    # ... find snapshot by date ...
    pass
```

### Step 3: Create Differential Formatter

```python
# src/edugain_analysis/formatters/diff.py

def print_change_summary(
    changes: Dict[str, Dict],
    baseline_date: str,
    current_date: str,
    baseline_stats: Dict,
    current_stats: Dict
):
    """
    Print change summary report.

    Args:
        changes: Entity change dictionary
        baseline_date: Baseline date
        current_date: Current date
        baseline_stats: Baseline statistics
        current_stats: Current statistics
    """
    stats = calculate_change_statistics(changes)

    print("\n" + "="*70)
    print(f"📊 Change Summary (comparing to baseline: {baseline_date})")
    print("="*70)

    print(f"\nTimeframe: {baseline_date} to {current_date}")

    print("\nEntity Changes:")
    print(f"  ✅ Improved: {stats['improved']:,} entities")
    print(f"  ⚠️  Regressed: {stats['regressed']:,} entities")
    print(f"  ✦  New: {stats['new']:,} entities")
    print(f"  ✗  Removed: {stats['removed']:,} entities")
    print(f"  →  Unchanged: {stats['total_unchanged']:,} entities")

    # Compliance changes
    print("\nCompliance Change:")

    # Privacy
    baseline_privacy = baseline_stats.get("privacy_coverage", 0)
    current_privacy = current_stats.get("privacy_coverage", 0)
    privacy_delta = current_privacy - baseline_privacy

    print(f"\n  Privacy Coverage:")
    print(f"    Baseline: {baseline_privacy:.1f}%")
    print(f"    Current: {current_privacy:.1f}%")
    print(f"    Change: {privacy_delta:+.1f}%")

    # ... similar for security, SIRTFI ...

def export_changes_csv(changes: Dict[str, Dict], filter_type: str = None):
    """
    Export change report as CSV.

    Args:
        changes: Entity change dictionary
        filter_type: Optional filter (improved, regressed, new, removed)
    """
    import csv
    import sys

    writer = csv.writer(sys.stdout)

    # Headers
    writer.writerow([
        "EntityID",
        "Federation",
        "EntityType",
        "ChangeStatus",
        "ChangeTypes",
        "Details"
    ])

    # Data rows
    for entity_id, change in changes.items():
        status = change["status"]

        # Apply filter
        if filter_type and status != filter_type:
            continue

        writer.writerow([
            entity_id,
            change.get("current", change.get("baseline", {})).get("federation", ""),
            change.get("current", change.get("baseline", {})).get("entity_type", ""),
            status,
            ",".join(change.get("change_types", [])),
            # ... details ...
        ])
```

## Success Metrics

- Campaign effectiveness measurable with precise numbers
- Federation operators can prove ROI of improvement efforts
- Regression investigation takes minutes instead of hours
- All entity changes tracked accurately
- 90% of users find differential reports valuable
- All tests pass with 100% coverage

## References

- Git diff/comparison concepts
- Database snapshot/versioning patterns
- Similar feature in Splunk, DataDog (baseline comparison)

## Dependencies

**Required**:
- Historical Snapshot Storage (Feature 1.4)

**Future Enhancement**:
- Integrate with Automated Alerting (Feature 2.6) to alert on regressions
- Integrate with Enhanced PDF Reports (Feature 2.5) to include change report
