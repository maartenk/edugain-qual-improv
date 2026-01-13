"""
Configuration settings for eduGAIN quality analysis.

Provides settings for HTTP accessibility validation of privacy statements
and security contact analysis in SAML metadata.
"""

# eduGAIN metadata URL
EDUGAIN_METADATA_URL = "https://mds.edugain.org/edugain-v2.xml"
EDUGAIN_FEDERATIONS_API = "https://technical.edugain.org/api.php?action=list_feds"

# Cache settings (XDG-compliant)
METADATA_CACHE_FILE = "metadata.xml"
METADATA_CACHE_HOURS = 12
FEDERATION_CACHE_FILE = "federations.json"
FEDERATION_CACHE_DAYS = 30
URL_VALIDATION_CACHE_FILE = "url_validation.json"
URL_VALIDATION_CACHE_DAYS = 7

# HTTP request settings
REQUEST_TIMEOUT = 30

# URL validation settings
URL_VALIDATION_TIMEOUT = 10  # seconds
URL_VALIDATION_DELAY = 0.1  # seconds between requests
URL_VALIDATION_THREADS = 10  # concurrent threads for URL validation
MAX_CONTENT_SIZE = 1024 * 1024  # 1MB max content size for analysis

# Bot protection mitigation settings
ENABLE_CLOUDSCRAPER_RETRY = True  # Retry with cloudscraper if bot protection detected
CLOUDSCRAPER_TIMEOUT = 20  # seconds (longer timeout for JS challenge solving)

# XML Namespaces for SAML metadata processing
NAMESPACES = {
    "md": "urn:oasis:names:tc:SAML:2.0:metadata",
    "mdui": "urn:oasis:names:tc:SAML:metadata:ui",
    "mdrpi": "urn:oasis:names:tc:SAML:metadata:rpi",
    "remd": "http://refeds.org/metadata",
    "icmd": "http://id.incommon.org/metadata",
    "mdattr": "urn:oasis:names:tc:SAML:metadata:attribute",
    "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
}
