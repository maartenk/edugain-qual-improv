# Migration Guide: v2.x to v3.0

## Overview

Version 3.0 extends privacy statement tracking from Service Providers (SPs) to include Identity Providers (IdPs). This is a **breaking change** affecting CSV structure, filter behavior, and statistics output.

**Key Changes:**
- IdPs now have privacy statements tracked (previously ignored)
- CSV format changes: IdPs show `Yes`/`No` instead of `N/A` for privacy
- New CSV columns in federation exports
- Filter `--csv missing-privacy` now includes IdPs
- Statistics dictionary includes new IdP privacy keys

**Who is affected:**
- CSV parsing scripts and dashboards
- Automated reporting pipelines
- Tools consuming the Python API directly
- Any system expecting SP-only privacy filtering

## Background

Analysis of eduGAIN metadata revealed approximately 23.7% of IdPs publish privacy statements, but the system was not tracking them. Version 3.0 addresses this gap by treating privacy statements as an entity-level attribute rather than SP-only.

## Breaking Changes Detail

### 1. Entity CSV Format (`--csv entities`)

**Before (v2.x):**
```csv
Federation,EntityType,OrganizationName,EntityID,HasPrivacyStatement,PrivacyStatementURL
SWAMID,SP,Example Uni,https://sp.ex.se,Yes,https://ex.se/privacy
SWAMID,IdP,Example Uni IdP,https://idp.ex.se,N/A,N/A
```

**After (v3.0):**
```csv
Federation,EntityType,OrganizationName,EntityID,HasPrivacyStatement,PrivacyStatementURL
SWAMID,SP,Example Uni,https://sp.ex.se,Yes,https://ex.se/privacy
SWAMID,IdP,Example Uni IdP,https://idp.ex.se,Yes,https://ex.se/privacy
```

**Impact:** IdP rows now populate `HasPrivacyStatement` (`Yes`/`No`) and `PrivacyStatementURL` columns instead of showing `N/A`.

**Migration:**
- Remove special-case handling for `N/A` values in IdP rows
- Treat `HasPrivacyStatement` as a boolean field for all entity types
- Update parsers to handle privacy URLs for both SPs and IdPs

### 2. Federation CSV Format (`--csv federations`)

**Before (v2.x):**
```csv
Federation,TotalEntities,TotalSPs,TotalIdPs,SPsWithPrivacy,SPsMissingPrivacy,...
SWAMID,450,250,200,180,70,...
```

**After (v3.0):**
```csv
Federation,TotalEntities,TotalSPs,TotalIdPs,SPsWithPrivacy,SPsMissingPrivacy,IdPsWithPrivacy,IdPsMissingPrivacy,...
SWAMID,450,250,200,180,70,47,153,...
```

**Impact:** Two new columns added after `SPsMissingPrivacy`:
- `IdPsWithPrivacy` - Count of IdPs with privacy statements
- `IdPsMissingPrivacy` - Count of IdPs without privacy statements

**Migration:**

**Option A - Column-name parsing (recommended):**
```python
import csv

with open('federations.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sp_privacy = int(row['SPsWithPrivacy'])
        sp_missing = int(row['SPsMissingPrivacy'])
        idp_privacy = int(row.get('IdPsWithPrivacy', 0))  # Graceful fallback
        idp_missing = int(row.get('IdPsMissingPrivacy', 0))
```

**Option B - Positional parsing (requires update):**
```python
# Update column indices to account for 2 new columns
# Old indices after column 5 must shift by +2
```

### 3. Filter Behavior (`--csv missing-privacy`)

**Before (v2.x):** Returns only SPs without privacy statements

**After (v3.0):** Returns both SPs **and** IdPs without privacy statements

**Migration:**

If you need SP-only results, filter by `EntityType` column:

```bash
# Command-line filtering
edugain-analyze --csv missing-privacy | grep ',SP,' > sp-only-missing.csv

# Python filtering
import csv

with open('missing-privacy.csv') as f:
    reader = csv.DictReader(f)
    sp_only = [row for row in reader if row['EntityType'] == 'SP']
```

### 4. Statistics Dictionary (Python API)

**Before (v2.x):**
```python
stats = {
    'sps_has_privacy': 1234,
    'sps_missing_privacy': 567,
    # ... no IdP privacy keys
}
```

**After (v3.0):**
```python
stats = {
    'sps_has_privacy': 1234,
    'sps_missing_privacy': 567,
    'idps_has_privacy': 89,        # NEW
    'idps_missing_privacy': 345,   # NEW
    # ...
}
```

**Migration:**

Use defensive key access:

```python
from edugain_analysis.core import analyze_privacy_security

stats, _, _ = analyze_privacy_security(root)

# Defensive access (compatible with both versions)
idp_privacy = stats.get('idps_has_privacy', 0)
idp_missing = stats.get('idps_missing_privacy', 0)

# Calculate combined metrics
total_privacy = stats['sps_has_privacy'] + idp_privacy
total_missing = stats['sps_missing_privacy'] + idp_missing
```

### 5. Broken Privacy Tool (`edugain-broken-privacy`)

**Before (v2.x):** Validates only SP privacy URLs

**After (v3.0):** Validates both SP and IdP privacy URLs

**Migration:**

Output CSV now includes IdP rows. Filter if SP-only validation required:

```bash
# Get broken links for SPs only
edugain-broken-privacy | grep ',SP,' > sp-broken-links.csv
```

## Summary Statistics Display Changes

The terminal summary output now shows combined privacy coverage with entity-type breakdown:

**v3.0 Output:**
```
📊 Privacy Statement URL Coverage: 🟢 2,345/5,234 (44.8%)
  ├─ SPs: 🟡 1,890/3,849 (49.1%)
  └─ IdPs: 🔴 455/1,385 (32.8%)
❌ Missing: 2,889/5,234 (55.2%)
```

This replaces the v2.x "SPs only" privacy section. No action required unless you parse terminal output programmatically.

## Dashboard and Reporting Updates

### Required Changes

1. **Add IdP Privacy Metrics**
   - Display IdP privacy coverage KPI alongside SP metrics
   - Update charts to show comparative SP vs IdP privacy coverage
   - Add federation-level IdP privacy statistics

2. **Update Existing Metrics**
   - Change "SP Privacy Coverage" labels to "Privacy Coverage" or "SP Privacy Coverage (SPs only)"
   - Add combined entity-level privacy metrics
   - Provide entity-type toggle or filter for drill-down analysis

3. **Alert Thresholds**
   - Review thresholds for privacy coverage alerts
   - Add separate thresholds for IdP privacy if needed
   - Update notification templates to reference both entity types

### Recommended Enhancements

- **Split Views**: Allow users to toggle between combined/SP-only/IdP-only views
- **Trend Analysis**: Track IdP privacy adoption over time (previously not tracked)
- **Gap Analysis**: Highlight federations with low IdP privacy coverage
- **Comparative Metrics**: Show SP vs IdP privacy coverage side-by-side

## Validation Steps

After upgrading to v3.0, verify your integration:

### 1. CSV Structure Verification

```bash
# Check entity CSV has IdP privacy data
edugain-analyze --csv entities | grep ',IdP,' | head -5

# Verify federation CSV has new columns
edugain-analyze --csv federations | head -1
# Should contain: IdPsWithPrivacy,IdPsMissingPrivacy
```

### 2. Filter Behavior Testing

```bash
# Verify missing-privacy includes IdPs
edugain-analyze --csv missing-privacy | grep ',IdP,' | wc -l
# Should return non-zero count
```

### 3. Python API Testing

```python
from edugain_analysis.core import get_metadata, analyze_privacy_security
import xml.etree.ElementTree as ET

xml_data = get_metadata()
root = ET.fromstring(xml_data)
stats, _, _ = analyze_privacy_security(root)

# Verify new keys exist
assert 'idps_has_privacy' in stats
assert 'idps_missing_privacy' in stats
print(f"IdPs with privacy: {stats['idps_has_privacy']}")
print(f"IdPs missing privacy: {stats['idps_missing_privacy']}")
```

### 4. Dashboard Verification

- Load updated CSV exports into dashboard
- Verify IdP privacy metrics display correctly
- Check that entity-type filters work as expected
- Test alert rules fire correctly with new data structure

## Rollback Plan

If issues arise, rollback to v2.4.3:

```bash
pip install edugain-analysis==2.4.3
```

Or pin to v2.x in `requirements.txt`:

```
edugain-analysis>=2.4,<3.0
```

This maintains SP-only privacy tracking behavior while you update integrations.

## Timeline Recommendations

**Week 1-2:**
- Test v3.0 in staging environment
- Update CSV parsing scripts
- Modify dashboard queries

**Week 3:**
- Deploy to production with monitoring
- Update documentation and runbooks
- Train operators on new IdP privacy metrics

**Week 4:**
- Verify alert rules function correctly
- Collect feedback from operators
- Fine-tune visualizations

## Support

If you encounter migration issues:

1. Check [CHANGELOG.md](../CHANGELOG.md) for detailed change list
2. Review [README.md](../README.md) for updated CSV column documentation
3. Open an issue at [GitHub Issues](https://github.com/maartenk/edugain-qual-improv/issues)

## Example Code Snippets

### Robust CSV Parsing

```python
import csv
from typing import List, Dict

def parse_entities_csv(filepath: str) -> List[Dict[str, str]]:
    """Parse entity CSV compatible with v2.x and v3.0."""
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        entities = []
        for row in reader:
            # Handle both 'Yes'/'No' and 'N/A' gracefully
            has_privacy = row.get('HasPrivacyStatement', 'No')
            if has_privacy not in ['Yes', 'No', 'N/A']:
                has_privacy = 'No'

            entities.append({
                'federation': row['Federation'],
                'entity_type': row['EntityType'],
                'organization': row['OrganizationName'],
                'entity_id': row['EntityID'],
                'has_privacy': has_privacy == 'Yes',
                'privacy_url': row.get('PrivacyStatementURL', ''),
            })
        return entities
```

### Filtering by Entity Type

```python
def filter_sps_missing_privacy(entities: List[Dict]) -> List[Dict]:
    """Extract SPs without privacy from combined results."""
    return [
        e for e in entities
        if e['entity_type'] == 'SP' and not e['has_privacy']
    ]
```

### Federation Statistics with IdP Privacy

```python
def calculate_federation_stats(entities: List[Dict]) -> Dict:
    """Calculate federation stats including IdP privacy."""
    stats = {
        'total_entities': len(entities),
        'total_sps': sum(1 for e in entities if e['entity_type'] == 'SP'),
        'total_idps': sum(1 for e in entities if e['entity_type'] == 'IdP'),
        'sps_with_privacy': sum(1 for e in entities if e['entity_type'] == 'SP' and e['has_privacy']),
        'idps_with_privacy': sum(1 for e in entities if e['entity_type'] == 'IdP' and e['has_privacy']),
    }

    # Calculate combined metrics
    stats['total_with_privacy'] = stats['sps_with_privacy'] + stats['idps_with_privacy']
    stats['privacy_coverage_pct'] = (
        stats['total_with_privacy'] / stats['total_entities'] * 100
        if stats['total_entities'] > 0 else 0
    )

    return stats
```
