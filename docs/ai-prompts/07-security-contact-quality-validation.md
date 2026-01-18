# AI Implementation Prompt: Security Contact Quality Validation

**Feature ID**: 1.2 from ROADMAP.md
**Priority**: HIGH
**Effort**: 1-2 weeks
**Type**: Check

## Objective

Validate the quality and usability of security contact information, not just presence, ensuring contacts are actionable during actual security incidents.

## Context

**Current State**:
- Tool checks for security contact presence only (binary: Yes/No)
- No validation of contact format or quality
- Placeholders and invalid emails counted as "valid"
- No detection of dummy or non-functional contacts

**Problem**:
- Security contacts may be present but unusable:
  - Invalid email formats: `security` (no domain)
  - Placeholders: `noreply@example.org`, `changeme@localhost`
  - Defunct domains: `@myspace.com`, `@geocities.com`
  - Empty mailto: `mailto:` with no address
- False sense of security: 80% have contacts, but how many work?
- Wasted effort during incidents: contacting non-functional addresses

**Real-World Impact**:
- Security incidents delayed by invalid contacts
- Federation operators can't reach entity administrators
- Compliance violations (SIRTFI requires functional contacts)

## Requirements

### Core Functionality

1. **Validation Rules**:

   **A. Email Format Validation**:
   - Valid email regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
   - Reject missing `@` symbol
   - Reject missing domain
   - Reject missing TLD

   **B. Placeholder Detection**:
   - Common prefixes: `noreply`, `no-reply`, `donotreply`, `changeme`, `example`, `test`
   - Common domains: `example.org`, `example.com`, `localhost`, `local`, `test.org`
   - Special case: `security@example.org` (SAML metadata example)

   **C. Empty/Missing Detection**:
   - Empty `mailto:` tags
   - Blank ContactPerson elements
   - Whitespace-only values

   **D. Redundancy Check** (optional):
   - Single contact = single point of failure
   - Recommend 2+ contacts for critical services

   **E. Deprecated Domains** (optional):
   - Known defunct services: `geocities.com`, `angelfire.com`, `myspace.com`
   - Academic domains that have changed

2. **Quality Scores**:
   ```python
   quality_levels = {
       "valid": "Proper email format, not a placeholder",
       "suspicious": "Valid format but suspicious pattern",
       "placeholder": "Common placeholder or example domain",
       "invalid": "Malformed email or empty",
       "missing": "No security contact provided"
   }
   ```

3. **Updated Statistics**:
   ```python
   stats = {
       # Existing
       "entities_with_security": 5678,
       "entities_missing_security": 4556,

       # New quality breakdown
       "security_contacts_valid": 4850,
       "security_contacts_suspicious": 320,
       "security_contacts_placeholder": 408,
       "security_contacts_invalid": 100,

       # Quality metrics
       "security_contact_quality_percent": 85.4,  # valid / with_security
   }
   ```

4. **CSV Export Changes**:
   - Add `SecurityContactQuality` column: `valid|suspicious|placeholder|invalid|missing`
   - Add `SecurityContactIssues` column: Comma-separated list of issues
   - Keep existing `HasSecurityContact` for backward compatibility

5. **Output Examples**:

   **Summary (Terminal)**:
   ```
   🛡️  Security Contact Coverage & Quality:
     Total Entities: 10,234
       ✅ With security contacts: 5,678 (55.5%)
       ❌ Missing security contacts: 4,556 (44.5%)

     Security Contact Quality:
       ✅ Valid contacts: 4,850 (85.4%)
       ⚠️  Suspicious contacts: 320 (5.6%)
       🚫 Placeholder contacts: 408 (7.2%)
       ❌ Invalid format: 100 (1.8%)

     Top Issues:
       - example.org domain: 215 entities
       - noreply addresses: 145 entities
       - Missing @ symbol: 68 entities
       - Single point of failure: 2,340 entities (only 1 contact)
   ```

   **Actionable Report**:
   ```
   🚨 INVALID SECURITY CONTACTS (Requires Immediate Action)

   Federation       | Organization         | Contact              | Issue
   ─────────────────────────────────────────────────────────────────────────
   InCommon         | Example University   | security             | Missing domain
   DFN-AAI          | Test Institute       | admin@localhost      | Placeholder domain
   SWAMID           | Sample College       | noreply@example.org  | Placeholder address
   ```

### Implementation Details

**Files to Create**:

1. **`src/edugain_analysis/core/contact_validation.py`**:
   - `validate_email_format(email)`: Email regex validation
   - `is_placeholder_email(email)`: Detect common placeholders
   - `is_deprecated_domain(email)`: Check for defunct domains
   - `validate_security_contact(contact)`: Main validation function
   - `get_quality_score(contact)`: Return quality level

2. **Files to Modify**:
   - `src/edugain_analysis/core/analysis.py`: Call validation during analysis
   - `src/edugain_analysis/formatters/base.py`: Show quality statistics
   - `src/edugain_analysis/cli/main.py`: Add `--validate-contacts` flag

**Edge Cases**:
- Multiple contacts: Validate each separately, report worst quality
- Non-email contacts (URLs, phone): Currently not supported, mark as "suspicious"
- International domains (IDN): Support Unicode via `idna` library
- Case sensitivity: Normalize to lowercase before validation

## Acceptance Criteria

### Functional Requirements
- [ ] Email format validation using regex
- [ ] Placeholder detection for common patterns
- [ ] Empty/missing contact detection
- [ ] Quality score assigned to each contact
- [ ] CSV export includes quality and issues columns
- [ ] Summary shows quality breakdown
- [ ] Actionable report lists invalid contacts
- [ ] Federation statistics include quality metrics

### Quality Requirements
- [ ] False positive rate < 5% (valid contacts marked invalid)
- [ ] False negative rate < 2% (invalid contacts marked valid)
- [ ] Performance overhead < 10% (validation is fast)
- [ ] Clear documentation of validation rules
- [ ] Migration guide for CSV consumers

### Testing Requirements
- [ ] Test valid email formats
- [ ] Test invalid email formats (missing @, domain, TLD)
- [ ] Test placeholder detection (all common patterns)
- [ ] Test empty/whitespace contacts
- [ ] Test international domains
- [ ] Test multiple contacts per entity
- [ ] Integration test with real metadata sample

## Testing Strategy

**Unit Tests**:
```python
def test_validate_email_format_valid():
    """Test valid email formats pass."""
    assert validate_email_format("security@example.edu") == True
    assert validate_email_format("admin+security@university.org") == True
    assert validate_email_format("john.doe@sub.domain.edu") == True

def test_validate_email_format_invalid():
    """Test invalid email formats fail."""
    assert validate_email_format("security") == False  # No domain
    assert validate_email_format("@example.org") == False  # No local part
    assert validate_email_format("security@") == False  # No domain
    assert validate_email_format("security@localhost") == False  # No TLD

def test_is_placeholder_email():
    """Test placeholder detection."""
    assert is_placeholder_email("noreply@example.org") == True
    assert is_placeholder_email("changeme@localhost") == True
    assert is_placeholder_email("security@example.org") == True  # SAML example
    assert is_placeholder_email("admin@university.edu") == False  # Real

def test_validate_security_contact_quality():
    """Test quality score assignment."""
    assert get_quality_score("security@university.edu") == "valid"
    assert get_quality_score("noreply@example.org") == "placeholder"
    assert get_quality_score("security") == "invalid"
    assert get_quality_score("") == "missing"
    assert get_quality_score(None) == "missing"

def test_validate_multiple_contacts():
    """Test validation with multiple contacts."""
    contacts = [
        "security@university.edu",  # valid
        "noreply@example.org"       # placeholder
    ]
    # Worst quality should be returned
    quality = validate_security_contacts(contacts)
    assert quality == "placeholder"
```

## Implementation Guidance

### Step 1: Create Contact Validation Module

```python
# src/edugain_analysis/core/contact_validation.py

import re
from typing import Optional

# Email validation regex (RFC 5322 simplified)
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# Common placeholder patterns
PLACEHOLDER_PREFIXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "changeme", "change-me", "example", "test", "dummy",
    "sample", "placeholder", "nobody", "admin"
}

PLACEHOLDER_DOMAINS = {
    "example.org", "example.com", "example.net",
    "localhost", "local", "test.org", "test.com",
    "domain.tld", "your-domain.com"
}

# Deprecated domains (defunct services)
DEPRECATED_DOMAINS = {
    "geocities.com", "angelfire.com", "myspace.com",
    "aol.com",  # Rarely used now
}

def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex.

    Args:
        email: Email address to validate

    Returns:
        True if valid format, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip()

    if not email:
        return False

    # Check basic regex
    return EMAIL_REGEX.match(email) is not None

def is_placeholder_email(email: str) -> bool:
    """
    Check if email is a common placeholder.

    Args:
        email: Email address to check

    Returns:
        True if placeholder, False otherwise
    """
    if not email:
        return False

    email = email.lower().strip()

    # Extract local part and domain
    if "@" not in email:
        return False

    local, domain = email.rsplit("@", 1)

    # Check placeholder prefixes
    if local in PLACEHOLDER_PREFIXES:
        return True

    # Check placeholder domains
    if domain in PLACEHOLDER_DOMAINS:
        return True

    return False

def is_deprecated_domain(email: str) -> bool:
    """
    Check if email uses a deprecated/defunct domain.

    Args:
        email: Email address to check

    Returns:
        True if deprecated, False otherwise
    """
    if not email or "@" not in email:
        return False

    domain = email.rsplit("@", 1)[1].lower().strip()
    return domain in DEPRECATED_DOMAINS

def get_quality_score(contact: Optional[str]) -> str:
    """
    Get quality score for security contact.

    Args:
        contact: Security contact email

    Returns:
        Quality level: valid|suspicious|placeholder|invalid|missing
    """
    if not contact or not contact.strip():
        return "missing"

    contact = contact.strip()

    # Check format
    if not validate_email_format(contact):
        return "invalid"

    # Check for placeholders
    if is_placeholder_email(contact):
        return "placeholder"

    # Check for deprecated domains
    if is_deprecated_domain(contact):
        return "suspicious"

    # All checks passed
    return "valid"

def validate_security_contact(
    contact: Optional[str],
    return_issues: bool = False
) -> dict:
    """
    Validate security contact and return detailed results.

    Args:
        contact: Security contact email
        return_issues: If True, return list of specific issues

    Returns:
        Dictionary with quality score and optional issues
    """
    issues = []

    if not contact or not contact.strip():
        return {
            "quality": "missing",
            "issues": ["No security contact provided"]
        }

    contact = contact.strip()

    # Email format validation
    if not validate_email_format(contact):
        if "@" not in contact:
            issues.append("Missing @ symbol")
        elif not contact.split("@")[1]:
            issues.append("Missing domain")
        elif "." not in contact.split("@")[1]:
            issues.append("Missing TLD")
        else:
            issues.append("Invalid email format")

    # Placeholder detection
    if is_placeholder_email(contact):
        if contact.split("@")[0].lower() in PLACEHOLDER_PREFIXES:
            issues.append(f"Placeholder prefix: {contact.split('@')[0]}")
        if contact.split("@")[1].lower() in PLACEHOLDER_DOMAINS:
            issues.append(f"Placeholder domain: {contact.split('@')[1]}")

    # Deprecated domain
    if is_deprecated_domain(contact):
        domain = contact.split("@")[1]
        issues.append(f"Deprecated domain: {domain}")

    # Determine quality
    quality = get_quality_score(contact)

    result = {"quality": quality}
    if return_issues:
        result["issues"] = issues

    return result

def validate_security_contacts(contacts: list[str]) -> dict:
    """
    Validate multiple security contacts (return worst quality).

    Args:
        contacts: List of security contact emails

    Returns:
        Dictionary with quality and aggregated issues
    """
    if not contacts:
        return {"quality": "missing", "issues": [], "count": 0}

    quality_priority = {
        "invalid": 0,
        "placeholder": 1,
        "suspicious": 2,
        "valid": 3,
        "missing": 4
    }

    worst_quality = "valid"
    all_issues = []
    valid_count = 0

    for contact in contacts:
        result = validate_security_contact(contact, return_issues=True)
        quality = result["quality"]
        issues = result.get("issues", [])

        # Track worst quality
        if quality_priority[quality] < quality_priority[worst_quality]:
            worst_quality = quality

        # Aggregate issues
        all_issues.extend(issues)

        # Count valid contacts
        if quality == "valid":
            valid_count += 1

    return {
        "quality": worst_quality,
        "issues": all_issues,
        "count": len(contacts),
        "valid_count": valid_count,
        "single_point_of_failure": len(contacts) == 1
    }
```

### Step 2: Update Analysis

```python
# src/edugain_analysis/core/analysis.py

from .contact_validation import validate_security_contact, validate_security_contacts

def analyze_privacy_security(root: ET.Element, validate_contacts: bool = False):
    """
    Analyze with optional contact quality validation.

    Args:
        root: Parsed XML metadata
        validate_contacts: Enable contact quality validation
    """
    stats = {
        # Existing stats...
        "entities_with_security": 0,

        # New quality stats (if validation enabled)
        "security_contacts_valid": 0,
        "security_contacts_suspicious": 0,
        "security_contacts_placeholder": 0,
        "security_contacts_invalid": 0,
    }

    for entity_elem in root.findall(".//md:EntityDescriptor", ns):
        # ... existing parsing ...

        # Extract security contacts
        security_contacts = []
        # ... extract from REFEDS and InCommon formats ...

        has_security_contact = len(security_contacts) > 0

        # Validate contact quality (if enabled)
        contact_quality = None
        contact_issues = []

        if validate_contacts and security_contacts:
            validation = validate_security_contacts(security_contacts)
            contact_quality = validation["quality"]
            contact_issues = validation["issues"]

            # Update quality statistics
            if contact_quality == "valid":
                stats["security_contacts_valid"] += 1
            elif contact_quality == "suspicious":
                stats["security_contacts_suspicious"] += 1
            elif contact_quality == "placeholder":
                stats["security_contacts_placeholder"] += 1
            elif contact_quality == "invalid":
                stats["security_contacts_invalid"] += 1

        # Store entity data
        entity_data = {
            # ... existing fields ...
            "has_security_contact": has_security_contact,
            "security_contact_quality": contact_quality,
            "security_contact_issues": contact_issues,
            "security_contacts": security_contacts if validate_contacts else None,
        }
        entities_list.append(entity_data)

    return stats, entities_list
```

### Step 3: Update CLI

```python
# src/edugain_analysis/cli/main.py

parser.add_argument(
    "--validate-contacts",
    action="store_true",
    help="Validate security contact quality (email format, placeholders)"
)

def main():
    args = parser.parse_args()

    # ... analysis ...
    stats, entities_list = analyze_privacy_security(
        root,
        validate_contacts=args.validate_contacts
    )

    # ... output quality statistics if validation enabled ...
    if args.validate_contacts:
        print_contact_quality_summary(stats)
```

## Success Metrics

- False positive rate < 5% on validation
- False negative rate < 2% on validation
- Performance overhead < 10%
- Federation operators report improved contact reliability
- Reduction in incident response delays
- All tests pass with >90% coverage

## References

- Current contact parsing: `src/edugain_analysis/core/analysis.py`
- Email validation: RFC 5322 (simplified)
- SIRTFI requirements: Functional security contact
- Common placeholder list: Compiled from real-world metadata
