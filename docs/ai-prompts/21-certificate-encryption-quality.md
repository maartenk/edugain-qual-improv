# AI Implementation Prompt: Certificate & Encryption Quality Analysis

**Feature ID**: 3.3 from ROADMAP.md
**Priority**: LOW-MEDIUM
**Effort**: 6-8 weeks
**Type**: Check

## Objective

Analyze X.509 certificates and encryption standards in SAML metadata to assess security posture, detect weak cryptography, identify expiring certificates, and validate TLS/HTTPS endpoint security.

## Context

**Current State**:
- Tool ignores certificates embedded in metadata
- No visibility into certificate expiry dates
- Can't detect weak algorithms (MD5, SHA-1, small RSA keys)
- No assessment of encryption vs. signing-only entities
- HTTPS endpoint security not validated

**Problem**: Federation operators don't know:
- Which entities have certificates expiring soon
- Which entities use deprecated algorithms
- Which entities don't support SAML encryption
- Which HTTPS endpoints have weak TLS configurations

## Requirements

### Core Functionality

1. **Certificate Extraction & Parsing**:
   - Extract certificates from `<KeyDescriptor>` elements
   - Parse X.509 certificates using Python `cryptography` library
   - Handle both `use="signing"` and `use="encryption"` certificates

2. **Certificate Expiry Checking**:
   - Parse `notAfter` date from certificates
   - Calculate days until expiry
   - Alert levels:
     - 🔴 Expired (< 0 days)
     - 🟠 Critical (< 30 days)
     - 🟡 Warning (< 90 days)
     - 🟢 OK (>= 90 days)

3. **Weak Algorithm Detection**:
   - Signature algorithms: Flag MD5, SHA-1 (deprecated)
   - RSA key sizes: Flag < 2048 bits
   - Recommend: SHA-256+ with RSA 2048+ or ECC

4. **Encryption Support Analysis**:
   - Check if entity has `<KeyDescriptor use="encryption">`
   - Flag signing-only entities (security gap for some use cases)
   - Calculate % of entities supporting encryption

5. **Certificate Chain Validation** (Optional):
   - Validate certificate chains if full chain in metadata
   - Detect self-signed certificates (common in testing)
   - Check for expired intermediate certificates

6. **TLS/HTTPS Endpoint Validation** (Advanced, Optional):
   - Extract HTTPS endpoints from metadata (AssertionConsumerService, SingleSignOnService)
   - Use `ssl` library or `sslyze` to check TLS configuration
   - Validate against Mozilla SSL Configuration Guidelines
   - Check TLS version (flag TLS 1.0/1.1)

### Statistics & Output

**Per-Entity CSV Columns**:
- `CertExpiryDate` (YYYY-MM-DD)
- `CertDaysUntilExpiry` (integer)
- `CertExpiryStatus` (expired/critical/warning/ok)
- `CertSignatureAlgorithm` (e.g., "sha256WithRSAEncryption")
- `CertKeyType` (RSA/DSA/EC)
- `CertKeySize` (bits)
- `HasWeakCrypto` (Yes/No)
- `SupportsEncryption` (Yes/No)
- `IsSelfSigned` (Yes/No)

**Summary Output**:
```
🔐 Certificate & Encryption Quality:

Certificate Expiry:
  Expired: 23 certificates (0.8%)
  Critical (< 30 days): 67 certificates (2.4%)
  Warning (< 90 days): 145 certificates (5.3%)
  OK: 2,515 certificates (91.5%)

Cryptographic Strength:
  Weak algorithms detected: 234 certificates (8.5%)
    - MD5 signatures: 12 (0.4%)
    - SHA-1 signatures: 178 (6.5%)
    - RSA < 2048 bits: 44 (1.6%)
  Strong algorithms: 2,516 certificates (91.5%)

Encryption Support:
  Supports encryption: 1,892 entities (68.8%)
  Signing-only: 858 entities (31.2%)

Top Entities Needing Attention:
  1. sp1.edu: Cert expires in 5 days, MD5 signature
  2. sp2.org: Cert expired 15 days ago
  3. idp3.edu: SHA-1 signature, RSA 1024

HTTPS Endpoint Security (if --validate-tls):
  TLS 1.2+: 2,134 endpoints (89.3%)
  TLS 1.0/1.1: 256 endpoints (10.7%) ⚠️
  Certificate mismatch: 45 endpoints (1.9%)
```

### Implementation Details

**Files to Create**:

1. **`src/edugain_analysis/core/certificates.py`** (NEW):
   - X.509 certificate parsing with `cryptography` library
   - Expiry checking
   - Weak algorithm detection
   - Encryption support analysis
   - TLS validation (optional)

2. **Dependencies**:
   ```python
   # Add to pyproject.toml
   dependencies = [
       "cryptography>=41.0.0",  # X.509 parsing
       # Optional:
       # "sslyze>=5.0.0",  # TLS scanning
   ]
   ```

3. **Example Implementation**:
   ```python
   from cryptography import x509
   from cryptography.hazmat.backends import default_backend
   from datetime import datetime
   import base64

   def parse_certificate(cert_pem: str) -> x509.Certificate:
       """Parse PEM-encoded certificate."""
       cert_bytes = base64.b64decode(cert_pem)
       return x509.load_der_x509_certificate(cert_bytes, default_backend())

   def check_certificate_expiry(cert: x509.Certificate) -> dict:
       """Check certificate expiry."""
       not_after = cert.not_valid_after
       now = datetime.utcnow()
       days_until_expiry = (not_after - now).days

       if days_until_expiry < 0:
           status = "expired"
       elif days_until_expiry < 30:
           status = "critical"
       elif days_until_expiry < 90:
           status = "warning"
       else:
           status = "ok"

       return {
           "expiry_date": not_after.isoformat(),
           "days_until_expiry": days_until_expiry,
           "status": status
       }

   def detect_weak_algorithms(cert: x509.Certificate) -> dict:
       """Detect weak cryptographic algorithms."""
       sig_alg = cert.signature_algorithm_oid._name
       public_key = cert.public_key()

       issues = []

       # Check signature algorithm
       if "md5" in sig_alg.lower():
           issues.append("MD5 signature (deprecated)")
       elif "sha1" in sig_alg.lower():
           issues.append("SHA-1 signature (deprecated)")

       # Check key size
       key_type = type(public_key).__name__
       if hasattr(public_key, 'key_size'):
           key_size = public_key.key_size
           if key_type == "RSAPublicKey" and key_size < 2048:
               issues.append(f"RSA key too small ({key_size} bits, recommend 2048+)")

       return {
           "has_weak_crypto": len(issues) > 0,
           "issues": issues,
           "signature_algorithm": sig_alg,
           "key_type": key_type,
           "key_size": getattr(public_key, 'key_size', None)
       }
   ```

## Acceptance Criteria

- [ ] Certificate extraction from metadata
- [ ] Expiry date parsing and calculation
- [ ] Weak algorithm detection (MD5, SHA-1, small keys)
- [ ] Encryption support checking
- [ ] CSV export with certificate columns
- [ ] Summary shows expiry and crypto statistics
- [ ] Performance acceptable (cert parsing is CPU-intensive)

## Testing Strategy

```python
def test_parse_certificate():
    """Test certificate parsing."""
    # Use test certificate
    cert_pem = "..."  # Base64-encoded DER certificate
    cert = parse_certificate(cert_pem)

    assert cert is not None
    assert hasattr(cert, 'not_valid_after')

def test_check_expiry():
    """Test expiry checking."""
    # Mock certificate expiring in 15 days
    from datetime import datetime, timedelta
    not_after = datetime.utcnow() + timedelta(days=15)

    result = check_certificate_expiry_mock(not_after)

    assert result["status"] == "critical"  # < 30 days
    assert result["days_until_expiry"] == 15

def test_detect_weak_algorithms():
    """Test weak algorithm detection."""
    # Mock certificate with SHA-1
    result = detect_weak_algorithms_mock(sig_alg="sha1WithRSAEncryption", key_size=2048)

    assert result["has_weak_crypto"] is True
    assert "SHA-1" in str(result["issues"])
```

## Success Metrics

- Early warning system prevents certificate expiry incidents
- Weak cryptography identified and upgraded
- % of entities with strong crypto improves over time
- Federation operators appreciate proactive security monitoring

## References

- Python `cryptography` library: https://cryptography.io/
- Mozilla SSL Configuration: https://wiki.mozilla.org/Security/Server_Side_TLS
- SAML metadata specification (KeyDescriptor elements)
- X.509 certificate standards

## Dependencies

**Required**:
- `cryptography` library for X.509 parsing

**Optional**:
- `sslyze` for TLS/HTTPS endpoint validation
- URL validation (Feature 1.8) for HTTPS endpoint discovery
