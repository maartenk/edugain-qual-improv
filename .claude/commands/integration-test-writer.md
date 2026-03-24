---
description: Write end-to-end integration tests for CLI commands (edugain-analyze, edugain-seccon, edugain-sirtfi, edugain-broken-privacy, or --all)
argument-hint: <command-name> | --all
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

## Task

Write integration tests for: $ARGUMENTS

Valid targets: `edugain-analyze`, `edugain-seccon`, `edugain-sirtfi`, `edugain-broken-privacy`, or `--all` for all four.

---

## PLAN

1. Read `.claude/pdca-logs/integration-test-writer.md` if it exists — apply any learned instructions.
2. Use TodoWrite: identify CLI source → list fixtures → write subprocess tests → run.
3. State in one sentence which commands will be tested and which fixture file will be used.

---

## DO

1. Read the relevant CLI source file(s) in `src/edugain_analysis/cli/` to understand arguments and expected output.
2. Use Glob `tests/fixtures/*` to see what metadata files are available as test inputs.
3. Read any existing files in `tests/integration/` for the current pattern.
4. Write integration tests in `tests/integration/test_cli_<stem>.py` (e.g. `test_cli_analyze.py`):
   - Use `subprocess.run` to invoke the real CLI entry point (e.g. `.venv/bin/edugain-analyze`)
   - Pass `--source tests/fixtures/sample_metadata.xml` (or appropriate fixture)
   - Assert `returncode == 0` for success cases
   - Assert key strings appear in `stdout`
   - Test `--help` exits 0
   - Mark every test class with `@pytest.mark.integration`
5. Run tests:
   ```bash
   cd /Users/kreme003/Workspace/git/edugain-qual-improv && \
     source .venv/bin/activate && \
     python -m pytest tests/integration/ -v -m integration 2>&1 | tail -40
   ```

---

## CHECK

- Did all integration tests pass?
- Does `--help` test pass for each command?
- Is at least one real execution test (non-help) present per command?
- Score: ✅ All pass / ⚠️ Some fail / ❌ All fail

---

## ACT

- If ⚠️ or ❌: read the failure, adjust (wrong fixture path, missing venv activation, wrong output assertion), retry up to 2 times.
- Always append one entry to `.claude/pdca-logs/integration-test-writer.md`:

```
## <date> — <commands tested>
**Result**: ✅/⚠️/❌  Tests written: <n>  Passed: <n>
**Approach**: <brief>
**What worked**: <e.g. "checking fixture files first">
**What to improve**: <e.g. "CLI path needed full .venv/bin/ prefix">
**Action**: <none / updated Learned Instructions>
---
```

- If the same issue appears in 2+ past entries, add a rule to `## Learned Instructions` below.

---

## Learned Instructions

*(This section is updated automatically by the ACT phase when patterns emerge across runs.)*
