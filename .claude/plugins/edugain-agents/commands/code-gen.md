---
description: Generate a new module or feature from a plain-English description
argument-hint: "<description>" --output <path> [--with-tests]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

## Task

Generate new code described as: $ARGUMENTS

Required flag: `--output <path>` — the destination file.
Optional flag: `--with-tests` — also write a unit test stub in `tests/unit/`.

---

## PLAN

1. Read `.claude/plugins/edugain-agents/pdca-logs/code-gen.md` if it exists — apply any learned instructions.
2. Determine the layer from the output path: `cli/` = orchestration, `core/` = business logic, `formatters/` = output, `config/` = constants.
3. Use TodoWrite: read similar module → write → lint → format → (optionally write tests).
4. State which existing file you will read for style reference.

---

## DO

1. Read 1–2 existing files in the same layer as the output path, for style reference.
2. Write the new file to the output path with:
   - Module-level docstring
   - Type hints using `str | None` style (PEP 604, never `Optional[str]`)
   - Absolute imports from the package root
   - Layer separation respected (CLI: no business logic; core: no `print()`; formatters: no business logic)
   - Specific exceptions (no bare `except`)
3. Run ruff check:
   ```bash
   cd /Users/kreme003/Workspace/git/edugain-qual-improv && \
     source .venv/bin/activate && \
     ruff check <output_path> 2>&1
   ```
4. Fix any ruff issues, then format:
   ```bash
   ruff format <output_path>
   ```
5. If `--with-tests`: write a test stub to `tests/unit/test_<stem>.py`, run `pytest tests/unit/ -x -q 2>&1 | tail -20`.

---

## CHECK

- Does ruff check pass with zero errors?
- Does the new file match the layer's responsibility (no cross-layer logic)?
- Are all public functions type-hinted?
- If `--with-tests`: do tests run without errors?
- Score: ✅ Clean / ⚠️ Minor issues / ❌ Major issues

---

## ACT

- If ⚠️ or ❌: fix the specific issues and re-run ruff. Retry up to 2 times.
- Always append one entry to `.claude/plugins/edugain-agents/pdca-logs/code-gen.md`:

```
## <date> — <output_path>
**Result**: ✅/⚠️/❌  Lines written: <n>
**Approach**: <reference file used, key decisions>
**What worked**: <e.g. "reading similar module first made style easy">
**What to improve**: <e.g. "ruff flagged missing type hint on return value">
**Action**: <none / updated Learned Instructions>
---
```

- If the same ruff violation or pattern issue appears in 2+ past entries, add a rule to `## Learned Instructions` below.

---

## Learned Instructions

*(This section is updated automatically by the ACT phase when patterns emerge across runs.)*
