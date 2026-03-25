#!/usr/bin/env bash
# User Prompt Submit Hook
# Provides helpful reminders when user mentions certain keywords

# Get the user's prompt from stdin or command line
USER_PROMPT="${1:-$(cat)}"

# Convert to lowercase for case-insensitive matching
USER_PROMPT_LOWER=$(echo "$USER_PROMPT" | tr '[:upper:]' '[:lower:]')

# Check for commit-related keywords
if echo "$USER_PROMPT_LOWER" | grep -qE '\b(commit|push|merge|pr|pull request)\b'; then
    cat <<'EOF'

💡 Pre-Commit Reminder:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before committing, consider:
  1. Run `make test` or `pytest` to ensure tests pass (300 tests)
  2. Run `make lint` or `ruff check --fix` for code quality
  3. Use /code-review to check for issues
  4. Use /review-all for comprehensive multi-tool review
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
fi

# Check for GDPR/content analysis keywords
if echo "$USER_PROMPT_LOWER" | grep -qE '\b(gdpr|keyword|privacy statement|content quality|multilingual|translation)\b'; then
    echo "💡 Tip: Use @gdpr-i18n-checker to verify GDPR keyword completeness across all 12 languages"
    echo ""
fi

# Check for XML/metadata keywords
if echo "$USER_PROMPT_LOWER" | grep -qE '\b(xml|metadata|entity descriptor|saml|federation)\b'; then
    echo "💡 Tip: Test fixtures are in tests/fixtures/test_metadata.xml for XML validation"
    echo ""
fi

# Check for PDF/report keywords
if echo "$USER_PROMPT_LOWER" | grep -qE '\b(pdf|report|chart|visualization|matplotlib)\b'; then
    echo "💡 Tip: PDF dependencies are in [tests] extra; use make install EXTRAS=tests or pip install -e .[tests]"
    echo ""
fi

# Check for test-related keywords
if echo "$USER_PROMPT_LOWER" | grep -qE '\b(test|pytest|coverage|unit test|integration test)\b'; then
    echo "💡 Tip: Use /test-writer <module-path> to generate comprehensive unit tests"
    echo ""
fi

# Check for CLI/command keywords
if echo "$USER_PROMPT_LOWER" | grep -qE '\b(cli|command|entry point|edugain-analyze|edugain-seccon)\b'; then
    echo "💡 Tip: All 4 CLI entry points (edugain-analyze, edugain-seccon, edugain-sirtfi, edugain-broken-privacy) are validated in CI"
    echo ""
fi

# Check for validation/URL keywords
if echo "$USER_PROMPT_LOWER" | grep -qE '\b(url validation|broken link|accessibility|http|https)\b'; then
    echo "💡 Tip: URL validation includes SSRF protection (see src/edugain_analysis/core/security.py)"
    echo ""
fi

# Check for feature development keywords
if echo "$USER_PROMPT_LOWER" | grep -qE '\b(new feature|implement|add functionality|roadmap)\b'; then
    echo "💡 Tip: Use /coordinator \"feature description\" for full end-to-end workflow (research → implement → test → doc → review)"
    echo ""
fi

# Check for performance/optimization keywords
if echo "$USER_PROMPT_LOWER" | grep -qE '\b(slow|performance|optimize|parallel|thread)\b'; then
    echo "💡 Tip: URL validation uses parallel processing with configurable thread count (URL_VALIDATION_THREADS config)"
    echo ""
fi

# Always allow the prompt to proceed (exit 0)
exit 0
