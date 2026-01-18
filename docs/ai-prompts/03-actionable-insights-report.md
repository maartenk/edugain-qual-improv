# AI Implementation Prompt: Actionable Insights Report Generator

**Feature ID**: 1.3 from ROADMAP.md
**Priority**: HIGH
**Effort**: 1 week
**Type**: Report

## Objective

Generate "Top N" priority lists that guide federation operators on what to fix first, turning raw data into actionable recommendations.

## Context

**Current State**:
- Tool provides comprehensive data about compliance gaps
- No guidance on prioritization or action planning
- Operators frequently ask: "What should I fix first?"

**Problem**:
- Data overload: CSV exports can have thousands of rows
- No clear prioritization framework
- Effort vs. impact not quantified
- No federation-specific action plans

**Use Cases**:
```bash
# Generate quick wins list
edugain-analyze --actionable-insights

# Customize priority list size
edugain-analyze --actionable-insights --top-n 20

# Export contact emails for outreach campaign
edugain-analyze --actionable-insights --export-contacts
```

## Requirements

### Core Functionality

1. **New CLI Flag**: `--actionable-insights`
   - Generate prioritized action lists instead of normal output
   - Can combine with `--validate` for broken URL detection
   - Mutually exclusive with `--csv`, `--report`, `--json`

2. **Optional Flags**:
   ```bash
   --top-n N                    # Number of entities per category (default: 10)
   --export-contacts            # Export technical contact emails for outreach
   --federation FEDERATION      # Limit insights to specific federation
   ```

3. **Report Sections**:

   **A. Critical Issues** (highest priority, requires immediate action):
   - SIRTFI compliance violations (entities with SIRTFI but no security contact)
   - Broken privacy URLs (user-facing, requires --validate)
   - Large SPs missing privacy statements (high user impact)

   **B. Quick Wins** (low effort, high completion rate):
   - Entities missing only 1 requirement (privacy OR security)
   - Entities with security contacts but no SIRTFI (certification candidates)
   - Recently fixed entities (validation cache shows recent 200 status)

   **C. Federation-Specific Action Plans**:
   - Per-federation gap analysis: "To reach 80% privacy coverage, fix N entities"
   - Cost-benefit: "Fix these 5 entities to improve coverage by 10%"
   - Progress tracking: Federation comparison with targets

   **D. Contact Export** (with `--export-contacts`):
   - CSV of technical contact emails for outreach campaigns
   - Include entity ID, organization, issues, federation
   - Template text for entity notifications

### Output Format

**Terminal Output**:
```
====================================================================
  📊 eduGAIN Quality Improvement: Actionable Insights Report
====================================================================

🚨 CRITICAL ISSUES (Requires Immediate Action)
──────────────────────────────────────────────────────────────────

1. SIRTFI Compliance Violations (5 entities)
   ❌ These entities claim SIRTFI but lack security contacts:

   Federation       | Entity ID                          | Organization
   ──────────────────────────────────────────────────────────────────
   InCommon         | https://sp1.example.edu            | Example University
   DFN-AAI          | https://idp.test.de                | Test Institute
   ...

   💡 ACTION: Add security contact or remove SIRTFI assertion

2. Broken Privacy URLs (12 SPs)
   🔗 User-facing privacy statements returning HTTP errors:

   Federation       | Organization          | URL                  | Error
   ──────────────────────────────────────────────────────────────────
   InCommon         | Sample College        | https://...          | 404
   ...

   💡 ACTION: Fix or update privacy statement URLs

──────────────────────────────────────────────────────────────────

✨ QUICK WINS (Low Effort, High Impact)
──────────────────────────────────────────────────────────────────

3. Missing Only Privacy Statement (23 SPs)
   ✅ Have security contact + SIRTFI, just need privacy URL:

   Federation       | Organization          | Entity ID
   ──────────────────────────────────────────────────────────────────
   InCommon         | Quick Win University  | https://...
   ...

   💡 ACTION: Add privacy statement URL to metadata

4. SIRTFI Certification Candidates (45 entities)
   ✅ Have security contacts but not yet SIRTFI certified:

   Federation       | Organization          | Entity Type
   ──────────────────────────────────────────────────────────────────
   DFN-AAI          | Ready Institute       | IdP
   ...

   💡 ACTION: Apply for SIRTFI certification

──────────────────────────────────────────────────────────────────

🎯 FEDERATION ACTION PLANS
──────────────────────────────────────────────────────────────────

InCommon (Currently: 85.2% privacy coverage, Target: 90%)
  📈 Fix these 12 SPs to reach 90% coverage:
     1. Entity A (100 users) - Add privacy URL
     2. Entity B (50 users) - Fix broken URL
     ...
  💪 Impact: +4.8% coverage with ~2 hours effort

DFN-AAI (Currently: 62.3% privacy coverage, Target: 80%)
  📈 Fix these 35 SPs to reach 80% coverage:
     Top 5 highest-impact entities:
     1. Large SP (1000 users) - Add privacy URL
     ...
  💪 Impact: +17.7% coverage with ~10 hours effort

──────────────────────────────────────────────────────────────────
📧 Contact Export: Run with --export-contacts to generate
   outreach CSV for technical contacts
====================================================================
```

**CSV Export** (with `--export-contacts`):
```csv
Federation,EntityType,OrganizationName,EntityID,TechnicalContact,IssueType,IssueDescription,ActionRequired
InCommon,SP,Example University,https://sp.example.edu,tech@example.edu,missing-privacy,No privacy statement URL,Add PrivacyStatementURL to metadata
DFN-AAI,IdP,Test Institute,https://idp.test.de,admin@test.de,sirtfi-violation,SIRTFI assertion without security contact,Add security contact or remove SIRTFI
```

### Implementation Details

**Files to Create**:

1. **`src/edugain_analysis/formatters/actionable.py`**:
   - `generate_actionable_insights(stats, entities, federation_stats)`: Main function
   - `find_critical_issues(entities)`: SIRTFI violations, broken URLs
   - `find_quick_wins(entities)`: Missing only 1 requirement
   - `generate_federation_plans(federation_stats, target_coverage)`: Gap analysis
   - `export_contacts(entities_with_issues)`: Contact CSV generation

2. **Files to Modify**:
   - `src/edugain_analysis/cli/main.py`: Add flags, call actionable formatter
   - `src/edugain_analysis/core/analysis.py`: Track per-entity details for ranking

**Ranking Algorithms**:

1. **Critical Issues**: SIRTFI violations first, then broken URLs, then large SPs
2. **Quick Wins**: Sort by "completeness" (entities with 2/3 requirements beat 1/3)
3. **Federation Plans**: Sort federations by "distance from target" (closest to 80% first)
4. **Entity Size**: Prioritize larger SPs (estimate by user count if available, else by domains)

**Edge Cases**:
- No critical issues: Show "🎉 No critical issues found!"
- Empty quick wins: Show alternative suggestions
- Federation already at target: Show "✅ Already meeting target"
- No technical contacts: Skip contact export, show warning

## Acceptance Criteria

### Functional Requirements
- [ ] `--actionable-insights` generates prioritized action lists
- [ ] Critical issues section identifies SIRTFI violations
- [ ] Quick wins section shows low-hanging fruit
- [ ] Federation action plans show gap to target coverage
- [ ] `--export-contacts` generates CSV with contact emails
- [ ] `--top-n` limits number of entities per category
- [ ] `--federation` filters to single federation
- [ ] Mutually exclusive with `--csv`, `--report`, `--json`

### Quality Requirements
- [ ] Output is readable and actionable (not just data dump)
- [ ] Recommendations are specific and implementable
- [ ] Impact quantified (e.g., "+4.8% coverage")
- [ ] Effort estimated (e.g., "~2 hours")
- [ ] Contact export includes all necessary fields
- [ ] No sensitive data exposed unintentionally

### Testing Requirements
- [ ] Test critical issues detection (SIRTFI violations)
- [ ] Test quick wins identification
- [ ] Test federation gap analysis
- [ ] Test contact export CSV format
- [ ] Test `--top-n` limits correctly
- [ ] Test `--federation` filters correctly
- [ ] Test empty scenarios (no issues found)

## Testing Strategy

**Unit Tests**:
```python
def test_find_critical_issues_sirtfi_violations():
    """Test detection of SIRTFI violations."""
    entities = [
        {
            "entity_id": "https://sp1.example.edu",
            "has_sirtfi": True,
            "has_security_contact": False,
            "organization": "Example University"
        },
        {
            "entity_id": "https://sp2.example.edu",
            "has_sirtfi": True,
            "has_security_contact": True,
            "organization": "Good University"
        }
    ]
    critical = find_critical_issues(entities)
    assert len(critical["sirtfi_violations"]) == 1
    assert "sp1.example.edu" in critical["sirtfi_violations"][0]["entity_id"]

def test_find_quick_wins_missing_one():
    """Test identification of entities missing only one requirement."""
    entities = [
        {
            "has_privacy": False,
            "has_security_contact": True,
            "has_sirtfi": True,
            "entity_type": "SP"
        },  # Quick win: needs only privacy
        {
            "has_privacy": False,
            "has_security_contact": False,
            "has_sirtfi": False,
            "entity_type": "SP"
        }  # Not a quick win: needs all 3
    ]
    quick_wins = find_quick_wins(entities)
    assert len(quick_wins["missing_only_privacy"]) == 1
```

## Implementation Guidance

### Step 1: Create Actionable Formatter

```python
# src/edugain_analysis/formatters/actionable.py

def find_critical_issues(entities: list[dict], validation_results: dict | None = None) -> dict:
    """
    Identify critical issues requiring immediate action.

    Args:
        entities: List of entity dictionaries
        validation_results: Optional URL validation results

    Returns:
        Dictionary with categorized critical issues
    """
    critical = {
        "sirtfi_violations": [],
        "broken_privacy_urls": [],
        "large_sps_no_privacy": []
    }

    for entity in entities:
        # SIRTFI violations
        if entity.get("has_sirtfi") and not entity.get("has_security_contact"):
            critical["sirtfi_violations"].append(entity)

        # Broken privacy URLs
        if validation_results and entity.get("privacy_url"):
            url_status = validation_results.get(entity["privacy_url"], {})
            if not url_status.get("accessible"):
                critical["broken_privacy_urls"].append({
                    **entity,
                    "url_error": url_status.get("error", "Unknown")
                })

        # Large SPs without privacy (estimate: assume large if well-known domains)
        if (entity.get("entity_type") == "SP" and
            not entity.get("has_privacy") and
            is_large_entity(entity)):  # Implement heuristic
            critical["large_sps_no_privacy"].append(entity)

    return critical

def find_quick_wins(entities: list[dict]) -> dict:
    """
    Identify low-effort, high-impact improvements.

    Returns:
        Dictionary with categorized quick wins
    """
    quick_wins = {
        "missing_only_privacy": [],
        "missing_only_security": [],
        "sirtfi_candidates": []
    }

    for entity in entities:
        # Missing only privacy (have security + SIRTFI)
        if (entity.get("entity_type") == "SP" and
            not entity.get("has_privacy") and
            entity.get("has_security_contact") and
            entity.get("has_sirtfi")):
            quick_wins["missing_only_privacy"].append(entity)

        # Missing only security (have privacy + SIRTFI)
        elif (not entity.get("has_security_contact") and
              entity.get("has_privacy") and
              entity.get("has_sirtfi")):
            quick_wins["missing_only_security"].append(entity)

        # SIRTFI candidates (have security, no SIRTFI)
        elif (entity.get("has_security_contact") and
              not entity.get("has_sirtfi")):
            quick_wins["sirtfi_candidates"].append(entity)

    return quick_wins

def generate_actionable_insights(
    stats: dict,
    entities: list[dict],
    federation_stats: dict,
    validation_results: dict | None = None,
    top_n: int = 10,
    target_coverage: float = 80.0
) -> str:
    """
    Generate actionable insights report.

    Args:
        stats: Overall statistics
        entities: List of all entities
        federation_stats: Per-federation statistics
        validation_results: Optional URL validation results
        top_n: Number of entities per category
        target_coverage: Target coverage percentage for federation plans

    Returns:
        Formatted report string
    """
    output = []
    output.append("=" * 68)
    output.append("  📊 eduGAIN Quality Improvement: Actionable Insights Report")
    output.append("=" * 68)
    output.append("")

    # Critical Issues
    critical = find_critical_issues(entities, validation_results)
    output.append("🚨 CRITICAL ISSUES (Requires Immediate Action)")
    output.append("─" * 68)
    # ... format critical issues ...

    # Quick Wins
    quick_wins = find_quick_wins(entities)
    output.append("✨ QUICK WINS (Low Effort, High Impact)")
    output.append("─" * 68)
    # ... format quick wins ...

    # Federation Plans
    output.append("🎯 FEDERATION ACTION PLANS")
    output.append("─" * 68)
    # ... generate federation plans ...

    return "\n".join(output)
```

### Step 2: Update CLI

```python
# src/edugain_analysis/cli/main.py

parser.add_argument(
    "--actionable-insights",
    action="store_true",
    help="Generate actionable insights report with prioritized recommendations"
)
parser.add_argument(
    "--top-n",
    type=int,
    default=10,
    metavar="N",
    help="Number of entities per category in insights report (default: 10)"
)
parser.add_argument(
    "--export-contacts",
    action="store_true",
    help="Export technical contact emails for outreach (with --actionable-insights)"
)

# ... after analysis ...

if args.actionable_insights:
    from ..formatters.actionable import generate_actionable_insights, export_contacts

    # Need entity-level data, not just aggregated stats
    # Modify analyze_privacy_security to return entities list
    insights_report = generate_actionable_insights(
        stats=stats,
        entities=entities_list,
        federation_stats=federation_stats,
        validation_results=url_validation_results if args.validate else None,
        top_n=args.top_n
    )
    print(insights_report)

    if args.export_contacts:
        contacts_csv = export_contacts(entities_list)
        # Write to file or stdout
        print(contacts_csv)
```

## Success Metrics

- Operators report insights are actionable and useful
- Reduction in "what do I fix first?" support requests
- Measured compliance improvement after using insights
- Contact export used in real outreach campaigns
- All tests pass with >90% coverage

## References

- Entity data structure: `src/edugain_analysis/core/analysis.py:analyze_privacy_security()`
- Current formatters: `src/edugain_analysis/formatters/base.py`
- SIRTFI detection: XPath in analysis.py
