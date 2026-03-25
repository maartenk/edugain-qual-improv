#!/usr/bin/env bash
# Session Start Hook
# Displays available agents and commands when starting a new Claude Code session

cat <<'EOF'
╔════════════════════════════════════════════════════════════════╗
║      eduGAIN Quality Improvement - Claude Code Session        ║
╚════════════════════════════════════════════════════════════════╝

📋 Quick Reference
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 Custom Agents (use @agent-name)
  @gdpr-i18n-checker  - Verify GDPR keyword completeness (12 languages)

⚡ Slash Commands (use /command-name)
  /coordinator "feature"      - Full end-to-end workflow (research → implement → test → doc → review)
  /code-review [path]         - Review code for bugs, security, type safety
  /test-writer <module>       - Generate unit tests for modules
  /researcher "question"      - Answer questions about the codebase
  /doc-gen <source> <output>  - Generate documentation from code
  /review-all                 - Multi-agent review of git changes
  /debugger <error|command>   - Debug failing commands or errors
  /integration-test-writer    - Generate CLI integration tests

🔧 Development Quick Commands
  make install EXTRAS=dev,tests  - Install with development dependencies
  make shell                     - Activate virtual environment
  make test                      - Run pytest test suite (300 tests)
  make lint                      - Run ruff format + check
  pytest --cov                   - Generate coverage report
  ruff check --fix               - Auto-fix linting issues

📚 Documentation
  CLAUDE.md            - Project conventions & AI guidance
  README.md            - User documentation & CLI usage
  docs/ROADMAP.md      - Feature roadmap
  docs/content-quality-analysis.md  - Privacy URL content analysis
  docs/idp-privacy-tracking.md      - IdP privacy statement tracking
  docs/migration-guide-v3.md        - v2.x → v3.0.0 migration

🎯 CLI Tools (4 entry points)
  edugain-analyze           - Main analysis tool (privacy, security, SIRTFI)
  edugain-seccon            - Security contacts without SIRTFI
  edugain-sirtfi            - SIRTFI without security contacts
  edugain-broken-privacy    - Broken privacy link validation

💡 Pro Tips
  • Run `make test` before committing
  • Use /coordinator for feature development
  • Use @gdpr-i18n-checker when modifying content_analysis.py
  • Check CLAUDE.md for coding standards (PEP 604, type hints)
  • All 4 CLI tools validated in CI (matrix: Python 3.11-3.14)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready to improve eduGAIN quality! 🚀
EOF
