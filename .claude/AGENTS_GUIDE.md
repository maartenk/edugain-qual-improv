# Claude Code Agents & Commands Guide

Complete guide to using custom agents, slash commands, and hooks in the eduGAIN Quality Improvement project.

## Table of Contents

- [Overview](#overview)
- [Custom Agents](#custom-agents)
- [Slash Commands](#slash-commands)
- [Hooks](#hooks)
- [Workflow Examples](#workflow-examples)
- [Best Practices](#best-practices)

---

## Overview

This project uses Claude Code's extensibility features to provide specialized assistance:

- **Custom Agents**: Autonomous specialists for specific review tasks (GDPR i18n)
- **Slash Commands**: Quick access to common development tasks (review, test, document)
- **Hooks**: Automated reminders and helpful suggestions based on context

### Quick Reference

| Tool | When to Use | Example |
|------|-------------|---------|
| `@gdpr-i18n-checker` | GDPR keyword changes | `@gdpr-i18n-checker verify content_analysis.py` |
| `/coordinator` | New features | `/coordinator "add CSV export for IdP privacy stats"` |
| `/code-review` | Code review | `/code-review src/edugain_analysis/core/` |
| `/test-writer` | Generate tests | `/test-writer src/edugain_analysis/cli/main.py` |
| `/review-all` | Multi-tool review | `/review-all` (checks git changes) |
| `/debugger` | Debug failures | `/debugger "pytest tests/unit/test_core.py fails"` |

---

## Custom Agents

Agents are specialized AI assistants that handle specific review and analysis tasks.

### Available Agents

#### 1. @gdpr-i18n-checker (GDPR Keyword Specialist)
**Purpose**: Verify GDPR keyword completeness across all 12 supported languages

**Expertise**:
- GDPR compliance terminology validation
- Keyword equivalence across EU languages
- Soft-404 pattern coverage
- Translation consistency
- Python dictionary structure validation

**Supported Languages**: EN, DE, FR, ES, IT, NL, PT, SV, DA, FI, NO, PL

**When to Use**:
- After modifying `src/edugain_analysis/core/content_analysis.py`
- When adding new languages to GDPR keyword lists
- Before releasing content quality features
- When reviewing multilingual support

**Example**:
```
@gdpr-i18n-checker verify all languages have core GDPR terms
```

**Output**: Comprehensive report with:
- Language coverage matrix
- Missing keywords by language
- Keyword count distribution
- Soft-404 pattern gaps
- Actionable recommendations

**File Checked**: `src/edugain_analysis/core/content_analysis.py`
- `GDPR_KEYWORDS` dictionary (12 languages)
- `SOFT_404_PATTERNS` dictionary
- Language detection logic

---

## Slash Commands

Slash commands provide quick access to development workflows.

### Available Commands

#### 1. /coordinator
**Purpose**: Full end-to-end feature development workflow

**Phases**:
1. **Research**: Explore codebase, understand patterns
2. **Implement**: Write code following conventions
3. **Test**: Generate and run unit tests
4. **Document**: Create user-facing documentation
5. **Review**: Check for bugs, security, style

**Example**:
```
/coordinator "add CSV export for IdP privacy statistics"
```

**Flags**:
- `--skip-research`: Skip research phase
- `--skip-codegen`: Skip implementation
- `--skip-tests`: Skip test generation
- `--skip-doc`: Skip documentation

---

#### 2. /code-review
**Purpose**: Review code for bugs, security issues, type safety, and style

**Checks**:
- Security vulnerabilities (SSRF, CSV injection)
- Type hint completeness (PEP 604)
- ruff violations
- Bug patterns

**Example**:
```
/code-review src/edugain_analysis/formatters/pdf.py
```

**Output**: Severity-based findings (CRITICAL, HIGH, MEDIUM, LOW)

---

#### 3. /test-writer
**Purpose**: Generate comprehensive unit tests for modules

**Features**:
- Follows pytest conventions
- Mocks external dependencies
- Tests edge cases
- Covers error handling

**Example**:
```
/test-writer src/edugain_analysis/core/validation.py
```

**Flags**:
- `--fix`: Run pytest and fix failing tests

---

#### 4. /researcher
**Purpose**: Answer questions about the codebase (read-only)

**Example**:
```
/researcher "How does URL validation handle bot protection?"
```

**Output**: Detailed analysis with file/line references

---

#### 5. /doc-gen
**Purpose**: Generate Markdown documentation from source code

**Example**:
```
/doc-gen src/edugain_analysis/core/security.py --output docs/security.md
```

---

#### 6. /review-all
**Purpose**: Multi-agent comprehensive review of git changes

**Process**:
1. Checks `git status` for modified files
2. Routes files to appropriate tools:
   - `content_analysis.py` → @gdpr-i18n-checker
   - Python files → /code-review
   - Tests → coverage check + /test-writer if gaps
   - Docs → /doc-gen if outdated
3. Consolidates findings

**Example**:
```
/review-all
```

**Output**: Consolidated report from all tools

---

#### 7. /debugger
**Purpose**: Debug failing commands or error messages

**Example**:
```
/debugger "pytest tests/unit/test_formatters.py::test_pdf_generation fails"
```

or:

```
/debugger --error "ModuleNotFoundError: No module named 'matplotlib'"
```

---

#### 8. /integration-test-writer
**Purpose**: Generate end-to-end CLI integration tests

**Example**:
```
/integration-test-writer edugain-analyze
```

or:

```
/integration-test-writer --all  # All 4 CLI tools
```

---

## Hooks

Hooks provide automated reminders and context-aware tips.

### session-start.sh
**Trigger**: When starting a new Claude Code session

**Displays**:
- Available agents and commands
- Quick reference for development tools
- Documentation links
- Pro tips

**Output Example**:
```
╔════════════════════════════════════════════════════════════════╗
║      eduGAIN Quality Improvement - Claude Code Session        ║
╚════════════════════════════════════════════════════════════════╝

🤖 Custom Agents (use @agent-name)
  @gdpr-i18n-checker  - Verify GDPR keyword completeness (12 languages)

⚡ Slash Commands (use /command-name)
  /coordinator "feature"      - Full end-to-end workflow
  /code-review [path]         - Review code for bugs, security
  ...

Ready to improve eduGAIN quality! 🚀
```

---

### user-prompt-submit.sh
**Trigger**: When user submits a prompt (before processing)

**Detects keywords and provides tips**:

| Keyword Pattern | Tip |
|-----------------|-----|
| `commit`, `push`, `pr` | Run `make test` and `make lint` before committing |
| `gdpr`, `keyword`, `multilingual` | Use @gdpr-i18n-checker for keyword validation |
| `xml`, `metadata`, `saml` | Test fixtures in tests/fixtures/test_metadata.xml |
| `pdf`, `report`, `chart` | PDF dependencies in [tests] extra |
| `test`, `pytest`, `coverage` | Use /test-writer <module-path> |
| `cli`, `command`, `entry point` | 4 CLI tools validated in CI |
| `url validation`, `broken link` | SSRF protection in core/security.py |
| `new feature`, `implement` | Use /coordinator for full workflow |

**Example**:
```
User: "I'm about to commit these changes"

💡 Pre-Commit Reminder:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before committing, consider:
  1. Run `make test` or `pytest` to ensure tests pass
  2. Run `make lint` or `ruff check --fix` for code quality
  3. Use /code-review to check for issues
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Workflow Examples

### Example 1: Adding a New Feature
```
User: /coordinator "add IdP privacy statement validation to edugain-broken-privacy CLI"

Claude:
1. [Research Phase] Analyzing existing CLI structure and validation patterns...
2. [Implement Phase] Writing code following project conventions...
3. [Test Phase] Generating unit tests...
4. [Document Phase] Updating README.md with new functionality...
5. [Review Phase] Checking for security issues and style violations...

Summary: Feature implemented with 12 new tests, all passing.
```

### Example 2: Reviewing Changes Before Commit
```
User: /review-all

Claude:
# Comprehensive Review Report

## Files Reviewed
- src/edugain_analysis/core/content_analysis.py (@gdpr-i18n-checker, /code-review)
- src/edugain_analysis/cli/main.py (/code-review)
- tests/unit/test_core_analysis.py (coverage check)

## Critical Issues 🚨
- Finnish (fi) GDPR keywords list is empty (0 keywords)
- Missing SSRF validation in new URL handling code

## Next Steps
1. Add Finnish GDPR keywords (12 terms minimum)
2. Apply validate_url_for_ssrf() before HTTP requests
3. Run pytest to verify fixes
```

### Example 3: Checking GDPR Keyword Coverage
```
User: @gdpr-i18n-checker verify all languages

Claude:
# GDPR i18n Keyword Completeness Report

## Executive Summary
10/12 languages complete, 2 languages missing critical keywords

## Critical Issues 🚨
### Empty Keyword Lists
- `da` (Danish) - GDPR_KEYWORDS['da'] has 0 entries
- `pt` (Portuguese) - GDPR_KEYWORDS entry completely missing

## Recommendations 💡
- Add Danish keywords (recommend ~35-40 based on average)
- Create Portuguese keyword list with core GDPR terms
```

---

## Best Practices

### When to Use Agents vs Commands

**Use Agents (@name) when:**
- You need specialized domain expertise (GDPR keywords)
- The task is review/analysis (read-only)
- You want detailed reports with specific recommendations

**Use Commands (/name) when:**
- You need code generation or modification
- You want a full workflow (coordinator)
- You need quick code review or testing

### Workflow Recommendations

#### Before Committing
```
1. /review-all              # Multi-tool comprehensive review
2. make test                # Run full test suite
3. make lint                # Check code quality
4. git commit -m "..."      # Commit with descriptive message
```

#### Implementing New Features
```
1. /coordinator "feature description"  # Let it handle research → implement → test → doc → review
2. Review PDCA logs for learned patterns
3. make test to verify
4. Commit changes
```

#### Debugging Test Failures
```
1. /debugger "pytest tests/unit/test_foo.py fails"
2. Review suggested fixes
3. Apply fixes
4. Re-run pytest
```

#### Checking GDPR Keywords
```
1. Modify src/edugain_analysis/core/content_analysis.py
2. @gdpr-i18n-checker verify completeness
3. Address missing keywords
4. Re-run agent to confirm fixes
```

### Pro Tips

1. **Use /coordinator for complex features** - It handles the full workflow
2. **Run @gdpr-i18n-checker after modifying content_analysis.py** - Catches missing keywords early
3. **Use /review-all before PRs** - Comprehensive multi-tool analysis
4. **Check hooks output** - They provide context-aware tips
5. **Read PDCA logs** - Learn from previous agent runs
6. **Keep tests green** - Run `make test` frequently

---

## Troubleshooting

### Agent Not Found
**Problem**: `@agent-name` not recognized

**Solution**: Check `.claude/agents/` directory for available agents

### Command Not Working
**Problem**: `/command-name` does nothing

**Solution**: Check `.claude/commands/` directory for available commands

### Hook Not Triggering
**Problem**: No tips appearing on keyword matches

**Solution**:
```bash
# Verify hooks are executable
ls -l .claude/hooks/*.sh

# If not executable
chmod +x .claude/hooks/*.sh
```

### GDPR Agent Returns Empty Report
**Problem**: @gdpr-i18n-checker finds no issues (but you know there are)

**Solution**:
- Verify `src/edugain_analysis/core/content_analysis.py` exists
- Check if `GDPR_KEYWORDS` dictionary is present in file
- Ensure Python dict syntax is correct

---

## Configuration

### Agent Settings
Agents are configured in `.claude/agents/*.md` with frontmatter:
```yaml
---
name: agent-name
description: When to use this agent
model: haiku|sonnet|opus
color: cyan|blue|green|...
tools:
  allow: [Read, Grep, Glob]
  deny: [Write, Edit, Bash]
---
```

### Command Settings
Commands are markdown files in `.claude/commands/*.md` with plain text instructions.

### Hook Settings
Hooks are bash scripts in `.claude/hooks/` with executable permissions (`chmod +x`).

---

## Further Reading

- **CLAUDE.md**: Project conventions and coding standards
- **README.md**: User documentation and CLI usage
- **docs/ROADMAP.md**: Future features and enhancement plans
- **.claude/pdca-logs/**: Historical agent run logs with lessons learned

---

**Ready to use agents and commands?** Type `/review-all` to see them in action! 🚀
