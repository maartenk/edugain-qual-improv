---
description: Write new unit tests or fix failing ones for a given module
argument-hint: <module_path> [--fix]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

## Task

Write or fix unit tests for: $ARGUMENTS

If `--fix` is present: fix failing tests only, keep passing tests intact.
Otherwise: write new comprehensive unit tests.

---

## PLAN

1. Read `.claude/plugins/edugain-agents/pdca-logs/test-writer.md` if it exists — apply any learned instructions.
2. Use TodoWrite to plan: read module → read existing tests → write/fix → verify.
3. State in one sentence: new tests or fix mode, and which test file will be created/modified.

---

## DO

1. Read the target module fully to understand every public function, class, and edge case.
2. Use Glob `tests/unit/test_*.py` to find the existing test file for this module (e.g. `core/security.py` → `test_core_security.py`).
3. Read one existing test file (e.g. `test_core_analysis.py`) to copy the exact import/bootstrap pattern.
4. Write or edit the test file in `tests/unit/` following these project conventions exactly:
   - Class names: `Test<FeatureName>`
   - Method names: `test_<behaviour>`
   - Each method has a one-line docstring
   - Use `unittest.mock.patch` for ALL external deps (requests, file I/O, network)
   - No real network calls, no real file system writes outside tmp
5. Run tests:
   ```bash
   cd /Users/kreme003/Workspace/git/edugain-qual-improv && \
     source .venv/bin/activate && \
     python -m pytest tests/unit/ -v -x 2>&1 | tail -40
   ```

---

## CHECK

- Did all tests pass? (exit code 0, no FAILED lines)
- Is coverage meaningfully higher for the target module?
- Are there obvious missing cases (error paths, empty inputs, edge values)?
- Score: ✅ All pass / ⚠️ Some fail / ❌ All fail

---

## ACT

- If ⚠️ or ❌: read the failure output carefully, fix the specific failing test, re-run. Up to 2 retries.
- Always append one entry to `.claude/plugins/edugain-agents/pdca-logs/test-writer.md`:

```
## <date> — <module_path>
**Result**: ✅/⚠️/❌  Tests written: <n>  Passed: <n>
**Approach**: <brief description of what you wrote>
**What worked**: <e.g. "reading existing test file first saved time">
**What to improve**: <e.g. "needed 2 retries on mock setup">
**Action**: <none / updated Learned Instructions>
---
```

- If the same mistake appears in 2+ past log entries, add a rule to `## Learned Instructions` below.

---

## Learned Instructions

*(This section is updated automatically by the ACT phase when patterns emerge across runs.)*
