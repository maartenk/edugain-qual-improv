# AI Implementation Prompt: Duplicate Entity ID Detection

**Feature ID**: 1.9 from ROADMAP.md
**Priority**: HIGH (CRITICAL)
**Effort**: 2 days
**Type**: Check

## Objective

Detect and handle duplicate entity IDs in metadata to prevent artificially inflated statistics and data quality issues.

## Context

**Current State**:
- Tool silently processes duplicate entity IDs without detection
- Duplicate entities counted multiple times in statistics
- CSV exports contain duplicate rows
- No warning to federation operators about metadata errors

**Problem**:
- **Stats artificially inflated**: 100 entities reported when only 95 are unique
- **Hidden metadata errors**: Federation operators unaware of duplicates
- **Data quality issues**: Downstream consumers confused by duplicates
- **Compliance violations**: Some federations prohibit duplicate entity IDs

**Real-World Scenario**:
```
Federation accidentally publishes same entity twice:
- entityID="https://sp.example.edu" appears at line 1234
- entityID="https://sp.example.edu" appears at line 5678
  (different metadata, same ID)

Current behavior: Both counted → inflated stats
Desired behavior: Detect, warn, deduplicate
```

## Requirements

### Core Functionality

1. **Duplicate Detection**:
   - Track seen entity IDs during metadata parsing
   - Detect when entity ID appears more than once
   - Count total duplicates and occurrences per ID

2. **Warning System**:
   - Emit warning to stderr for each duplicate found
   - Include entity ID and occurrence number
   - Format: `Warning: Duplicate entity ID found: https://sp.example.edu (occurrence #2)`

3. **CLI Flags**:
   ```bash
   --deduplicate              # Keep only first occurrence, continue processing
   --fail-on-duplicates       # Exit with error if duplicates found
   --show-duplicates          # Print duplicate summary at end
   ```

4. **Statistics**:
   - Add to summary: `Duplicate entities detected: 5 (unique IDs: 3)`
   - Track in stats dict: `duplicate_count`, `unique_duplicate_ids`

5. **CSV Export**:
   - New export mode: `--csv duplicates` shows only duplicate entities
   - Columns: EntityID, OccurrenceNumber, Federation, EntityType, Organization

6. **Deduplication Strategy**:
   - Default: Keep first occurrence, skip subsequent
   - Optional: Keep last occurrence with `--deduplicate-keep-last`
   - Log which occurrence was kept

### Output Examples

**Warning Messages** (stderr):
```
Warning: Duplicate entity ID found: https://sp.example.edu (occurrence #2)
Warning: Duplicate entity ID found: https://sp.example.edu (occurrence #3)
Warning: Duplicate entity ID found: https://idp.university.org (occurrence #2)
```

**Summary** (with `--show-duplicates`):
```
⚠️  Duplicate Entity IDs Detected:
  Total duplicate entities: 5
  Unique entity IDs with duplicates: 3

  Duplicated Entity IDs:
    - https://sp.example.edu (3 occurrences)
    - https://idp.university.org (2 occurrences)
    - https://test.federation.org (2 occurrences)
```

**CSV Export** (`--csv duplicates`):
```csv
EntityID,OccurrenceNumber,Federation,EntityType,OrganizationName
https://sp.example.edu,1,InCommon,SP,Example University
https://sp.example.edu,2,InCommon,SP,Example University (duplicate)
https://sp.example.edu,3,InCommon,SP,Example University (duplicate)
```

### Implementation Details

**Files to Modify**:

1. **`src/edugain_analysis/core/analysis.py`**:
   - Add duplicate tracking set/dict
   - Emit warnings when duplicate found
   - Implement deduplication logic
   - Add duplicate statistics

2. **`src/edugain_analysis/cli/main.py`**:
   - Add CLI flags
   - Handle `--fail-on-duplicates` exit logic
   - Display duplicate summary
   - Add `--csv duplicates` export mode

3. **`src/edugain_analysis/formatters/base.py`**:
   - Add duplicate summary formatter
   - Add duplicate CSV export function

**Edge Cases**:
- Empty entity ID: Skip, don't count as duplicate
- Case sensitivity: Entity IDs are case-sensitive (don't normalize)
- Multiple federations: Same entity ID in different federations is NOT a duplicate (expected)
- Whitespace: Trim entity IDs before comparison
- URL encoding: Normalize URL-encoded entity IDs

## Acceptance Criteria

### Functional Requirements
- [ ] Duplicate detection during metadata parsing
- [ ] Warning to stderr for each duplicate found
- [ ] `--deduplicate` keeps first occurrence, skips rest
- [ ] `--fail-on-duplicates` exits with code 1 if duplicates present
- [ ] `--show-duplicates` displays summary
- [ ] Statistics include duplicate count
- [ ] `--csv duplicates` exports only duplicate entities
- [ ] Deduplication doesn't affect other statistics accuracy

### Quality Requirements
- [ ] Zero false positives (unique entities flagged as duplicates)
- [ ] All duplicates detected (100% recall)
- [ ] Clear, actionable warning messages
- [ ] Performance overhead < 5% (hashtable lookups are fast)
- [ ] No breaking changes to existing outputs

### Testing Requirements
- [ ] Test duplicate detection with sample metadata
- [ ] Test `--deduplicate` flag behavior
- [ ] Test `--fail-on-duplicates` exit code
- [ ] Test duplicate summary display
- [ ] Test CSV duplicates export
- [ ] Test edge cases (empty IDs, whitespace, URL encoding)
- [ ] Integration test with real metadata sample

## Testing Strategy

**Unit Tests**:
```python
def test_duplicate_detection():
    """Test duplicate entity ID detection."""
    metadata_xml = """
    <EntitiesDescriptor>
        <EntityDescriptor entityID="https://sp.example.edu">
            <SPSSODescriptor>...</SPSSODescriptor>
        </EntityDescriptor>
        <EntityDescriptor entityID="https://sp.example.edu">
            <SPSSODescriptor>...</SPSSODescriptor>
        </EntityDescriptor>
        <EntityDescriptor entityID="https://idp.test.org">
            <IDPSSODescriptor>...</IDPSSODescriptor>
        </EntityDescriptor>
    </EntitiesDescriptor>
    """
    root = ET.fromstring(metadata_xml)
    stats, entities, duplicates = analyze_privacy_security(root)

    assert duplicates["duplicate_count"] == 1  # One duplicate occurrence
    assert len(duplicates["duplicate_ids"]) == 1  # One unique ID duplicated
    assert "https://sp.example.edu" in duplicates["duplicate_ids"]
    assert duplicates["duplicate_ids"]["https://sp.example.edu"] == 2  # 2 occurrences

def test_deduplicate_keeps_first():
    """Test deduplication keeps first occurrence."""
    # ... metadata with duplicates ...
    stats, entities, duplicates = analyze_privacy_security(
        root, deduplicate=True
    )

    # Should have 2 entities (sp.example.edu deduplicated)
    assert len(entities) == 2
    # Stats should reflect deduplicated count
    assert stats["total_entities"] == 2

def test_fail_on_duplicates_exit_code():
    """Test --fail-on-duplicates exits with code 1."""
    result = subprocess.run(
        ["edugain-analyze", "--fail-on-duplicates"],
        capture_output=True,
        # Use sample metadata with duplicates
    )
    assert result.returncode == 1
    assert b"Duplicate entity ID" in result.stderr
```

## Implementation Guidance

### Step 1: Add Duplicate Tracking

```python
# src/edugain_analysis/core/analysis.py

def analyze_privacy_security(
    root: ET.Element,
    deduplicate: bool = False,
    deduplicate_keep_last: bool = False
) -> tuple[dict, list, dict]:
    """
    Analyze with duplicate detection.

    Args:
        root: Parsed XML metadata
        deduplicate: If True, keep only one occurrence per entity ID
        deduplicate_keep_last: If True, keep last occurrence (not first)

    Returns:
        Tuple of (statistics, entities_list, duplicates_info)
    """
    stats = {
        # ... existing stats ...
    }

    entities_list = []

    # Duplicate tracking
    seen_entity_ids = {}  # entity_id -> occurrence_count
    duplicate_entities = []  # List of duplicate entity info

    for entity_elem in root.findall(".//md:EntityDescriptor", ns):
        # Extract entity ID
        entity_id = entity_elem.get("entityID")

        if not entity_id or not entity_id.strip():
            continue  # Skip empty entity IDs

        entity_id = entity_id.strip()

        # Check for duplicate
        if entity_id in seen_entity_ids:
            # Duplicate found!
            occurrence = seen_entity_ids[entity_id] + 1
            seen_entity_ids[entity_id] = occurrence

            # Emit warning to stderr
            import sys
            print(
                f"Warning: Duplicate entity ID found: {entity_id} "
                f"(occurrence #{occurrence})",
                file=sys.stderr
            )

            # Store duplicate info
            duplicate_entities.append({
                "entity_id": entity_id,
                "occurrence": occurrence,
                # ... extract other fields for CSV export ...
            })

            # Handle deduplication
            if deduplicate and not deduplicate_keep_last:
                # Skip this duplicate (keep first)
                continue
            elif deduplicate and deduplicate_keep_last:
                # Remove previous occurrence, keep this one
                # Find and remove previous entity from entities_list
                entities_list = [
                    e for e in entities_list
                    if e["entity_id"] != entity_id
                ]
        else:
            # First occurrence
            seen_entity_ids[entity_id] = 1

        # ... rest of entity parsing ...

        entity_data = {
            "entity_id": entity_id,
            # ... other fields ...
        }
        entities_list.append(entity_data)

    # Calculate duplicate statistics
    duplicate_ids = {
        eid: count for eid, count in seen_entity_ids.items()
        if count > 1
    }

    duplicates_info = {
        "duplicate_count": len(duplicate_entities),
        "unique_duplicate_ids": len(duplicate_ids),
        "duplicate_ids": duplicate_ids,  # {entity_id: occurrence_count}
        "duplicate_entities": duplicate_entities  # For CSV export
    }

    return stats, entities_list, duplicates_info
```

### Step 2: Add CLI Flags

```python
# src/edugain_analysis/cli/main.py

parser.add_argument(
    "--deduplicate",
    action="store_true",
    help="Keep only first occurrence of duplicate entity IDs"
)
parser.add_argument(
    "--deduplicate-keep-last",
    action="store_true",
    help="Keep last occurrence instead of first (requires --deduplicate)"
)
parser.add_argument(
    "--fail-on-duplicates",
    action="store_true",
    help="Exit with error if duplicate entity IDs found"
)
parser.add_argument(
    "--show-duplicates",
    action="store_true",
    help="Display duplicate entity summary"
)

def main():
    args = parser.parse_args()

    # Validate flags
    if args.deduplicate_keep_last and not args.deduplicate:
        print("Error: --deduplicate-keep-last requires --deduplicate", file=sys.stderr)
        sys.exit(2)

    # ... metadata parsing ...

    # Analyze with duplicate detection
    stats, entities_list, duplicates_info = analyze_privacy_security(
        root,
        deduplicate=args.deduplicate,
        deduplicate_keep_last=args.deduplicate_keep_last
    )

    # Check for duplicates
    if duplicates_info["duplicate_count"] > 0:
        # Show duplicate summary if requested
        if args.show_duplicates:
            from ..formatters.base import print_duplicate_summary
            print_duplicate_summary(duplicates_info)

        # Fail if requested
        if args.fail_on_duplicates:
            print(
                f"\nError: {duplicates_info['duplicate_count']} duplicate "
                f"entity ID(s) found. Use --deduplicate to continue anyway.",
                file=sys.stderr
            )
            sys.exit(1)

    # Handle --csv duplicates export
    if args.csv == "duplicates":
        from ..formatters.base import export_duplicates_csv
        export_duplicates_csv(duplicates_info["duplicate_entities"])
        return

    # ... rest of normal processing ...
```

### Step 3: Add Formatters

```python
# src/edugain_analysis/formatters/base.py

def print_duplicate_summary(duplicates_info: dict):
    """
    Print duplicate entity summary.

    Args:
        duplicates_info: Duplicates information dictionary
    """
    if duplicates_info["duplicate_count"] == 0:
        print("\n✅ No duplicate entity IDs detected.")
        return

    print("\n⚠️  Duplicate Entity IDs Detected:")
    print(f"  Total duplicate entities: {duplicates_info['duplicate_count']}")
    print(f"  Unique entity IDs with duplicates: {duplicates_info['unique_duplicate_ids']}")
    print()
    print("  Duplicated Entity IDs:")

    # Sort by occurrence count (most duplicates first)
    sorted_duplicates = sorted(
        duplicates_info["duplicate_ids"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    for entity_id, count in sorted_duplicates:
        print(f"    - {entity_id} ({count} occurrences)")

def export_duplicates_csv(duplicate_entities: list[dict]):
    """
    Export duplicate entities to CSV.

    Args:
        duplicate_entities: List of duplicate entity dictionaries
    """
    import csv
    import sys

    writer = csv.writer(sys.stdout)

    # Headers
    writer.writerow([
        "EntityID",
        "OccurrenceNumber",
        "Federation",
        "EntityType",
        "OrganizationName"
    ])

    # Data rows
    for entity in duplicate_entities:
        writer.writerow([
            entity["entity_id"],
            entity["occurrence"],
            entity.get("federation", ""),
            entity.get("entity_type", ""),
            entity.get("organization", "")
        ])
```

### Step 4: Add to Summary Stats

```python
# src/edugain_analysis/formatters/base.py

def print_summary(stats: dict, duplicates_info: dict):
    """
    Print summary with duplicate information.
    """
    # ... existing summary ...

    # Add duplicate warning if present
    if duplicates_info["duplicate_count"] > 0:
        print(f"\n⚠️  Duplicate Entities: {duplicates_info['duplicate_count']} "
              f"({duplicates_info['unique_duplicate_ids']} unique IDs)")
        print("   Run with --show-duplicates for details")
```

## Success Metrics

- All duplicate entity IDs detected (100% recall)
- Zero false positives on unique entities
- Clear warnings help operators fix metadata errors
- Deduplication produces accurate statistics
- `--fail-on-duplicates` catches quality issues in CI/CD
- All tests pass with 100% coverage

## References

- Current entity parsing: `src/edugain_analysis/core/analysis.py`
- SAML metadata spec: Entity IDs must be unique within aggregate
- Similar pattern: SQL DISTINCT, pandas drop_duplicates()
