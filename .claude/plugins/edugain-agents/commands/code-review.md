---
description: Review code for bugs, security issues, and style. Add --fix to apply fixes.
argument-hint: <path> [--fix]
allowed-tools: [Read, Bash, Glob, Grep]
---

## Task

Review code at: $ARGUMENTS

Default: read-only review — findings reported, nothing changed.
With `--fix`: apply fixes directly (adds Write and Edit access implicitly — ask Claude Code to use those tools).

---

## PLAN

1. Read `.claude/plugins/edugain-agents/pdca-logs/code-review.md` if it exists — apply any learned instructions.
2. Use TodoWrite: list files → run ruff → read each file → compile findings → (fix if --fix).
3. State in one sentence: read-only or fix mode, and what directory/file is being reviewed.

---

## DO

1. If the path is a directory: use Glob `<path>/**/*.py` to list all Python files.
2. Run ruff on the target:
   ```bash
   cd /Users/kreme003/Workspace/git/edugain-qual-improv && \
     source .venv/bin/activate && \
     ruff check <path> 2>&1
   ```
3. Read each Python file carefully. Check for:
   - **[CRITICAL]** Bugs: wrong conditions, unhandled exceptions, off-by-one, wrong return values
   - **[HIGH]** Security:
     - SSRF: URLs passed to `requests.*` without going through `core/security.py`'s validator
     - CSV injection: values written to `csv.writer` without sanitization from `core/security.py`
     - Credentials in logs or printed output
   - **[MEDIUM]** Type hints: missing or using `Optional[str]` instead of `str | None`
   - **[MEDIUM]** Missing docstrings on public functions/classes
   - **[LOW]** Ruff violations (from step 2)
4. If `--fix`: apply the fixes directly using Edit. Re-run ruff after each edit to confirm it passes.
5. If read-only: output findings as:
   `[SEVERITY] file:line — description`

---

## CHECK

- Are all CRITICAL and HIGH findings addressed (or noted if intentional)?
- Does ruff pass after fixes (if `--fix` mode)?
- Is the summary accurate (correct count by severity)?
- Score: ✅ Clean or fixed / ⚠️ Issues found but not fixed (read-only) / ❌ Could not fix critical issues

---

## ACT

- If ❌ in fix mode: explain what blocked the fix and leave a `# TODO:` comment at the location.
- Always append one entry to `.claude/plugins/edugain-agents/pdca-logs/code-review.md`:

```
## <date> — <path> [read-only | fix]
**Result**: ✅/⚠️/❌  Issues: CRITICAL=<n> HIGH=<n> MEDIUM=<n> LOW=<n>
**Approach**: <ruff first, then manual read>
**What worked**: <e.g. "ruff caught the type hint issues quickly">
**What to improve**: <e.g. "need to check security.py imports explicitly">
**Action**: <none / updated Learned Instructions>
---
```

- If the same category of issue dominates 2+ past entries, add a targeted check rule to `## Learned Instructions` below.

---

## Learned Instructions

*(This section is updated automatically by the ACT phase when patterns emerge across runs.)*
