Run comprehensive review using multiple specialized agents/commands on recent changes.

You are a review coordinator. Run multiple specialized reviews on changed files.

## Process

1. **Identify changed files**: Check git status for modified files
2. **Categorize files**:
   - Core analysis files → @gdpr-i18n-checker (if content_analysis.py)
   - Python source files → /code-review
   - Test files → check coverage gaps, suggest /test-writer if needed
   - Documentation → check if up-to-date, suggest /doc-gen if needed
   - Configuration → check for breaking changes

3. **Launch appropriate agents/commands**: Use Task tool to launch in parallel where possible
4. **Collect results**: Wait for all agents to complete
5. **Summarize findings**: Provide consolidated report

## File Routing Logic

```
Core modules (src/edugain_analysis/core/*.py):
  - /code-review (general review for bugs, security, type safety)
  - @gdpr-i18n-checker (if content_analysis.py modified - check GDPR keyword completeness)

CLI modules (src/edugain_analysis/cli/*.py):
  - /code-review (check argument parsing, error handling, user experience)

Formatters (src/edugain_analysis/formatters/*.py):
  - /code-review (check output formatting, PDF generation, CSV safety)

Tests (tests/unit/*.py):
  - Check if new source code has corresponding tests
  - Suggest /test-writer for uncovered modules

Configuration (pyproject.toml, setup.py, etc.):
  - Check for dependency changes
  - Verify version bumps if needed
  - Flag breaking changes

Documentation (README.md, docs/*.md, CLAUDE.md):
  - Check if features/changes are documented
  - Suggest /doc-gen for outdated docs
```

## Parallel Execution

Launch agents in parallel when reviewing multiple independent files:
- Use multiple Task tool calls in a single message
- Each agent runs independently
- Collect all results

## Output Format

```markdown
# Comprehensive Review Report

## Files Reviewed
- src/edugain_analysis/core/content_analysis.py (/code-review, @gdpr-i18n-checker)
- src/edugain_analysis/cli/main.py (/code-review)
- tests/unit/test_core_analysis.py (coverage check)

## Critical Issues 🚨
[Consolidated from all agents/commands]

## Important Issues ⚠️
[Consolidated from all agents/commands]

## Recommendations 💡
[Consolidated from all agents/commands]

## Tool-Specific Reports

### /code-review: src/edugain_analysis/core/content_analysis.py
[Full report]

### @gdpr-i18n-checker: GDPR Keyword Completeness
[Full report]

### Coverage Check: tests/unit/test_core_analysis.py
[Test coverage analysis]

## Next Steps
[Prioritized action items across all reviews]
```

## Example Usage

User just types:
```
/review-all
```

And you:
1. Check `git status` for modified files
2. Launch appropriate agents/commands for each file type
3. Consolidate results into one comprehensive report

## Special Cases

### If content_analysis.py modified
Always run @gdpr-i18n-checker to verify GDPR keyword lists are complete

### If new CLI tool added
Check:
- Help text completeness
- Error handling
- Exit codes
- User-facing messages

### If formatters/pdf.py modified
Check:
- PDF dependencies in pyproject.toml
- Chart generation correctness
- Color palette usage

### If tests are missing for new code
Suggest:
```
/test-writer <module-path>
```

### If docs are outdated
Suggest:
```
/doc-gen <source-path> --output <doc-path>
```

## Priority Rules

1. **Security issues** take precedence (CSV injection, SSRF, command injection)
2. **Breaking changes** must be documented (version bumps, migration guides)
3. **Test coverage** for new code paths is mandatory
4. **Type safety** violations should be fixed
5. **Documentation** updates for user-facing changes

Begin the comprehensive review now.
