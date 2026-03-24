---
description: Investigate and fix a failing test, command, or error message
argument-hint: "<shell command that fails>" | --error "<error message>"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

## Task

Debug and fix: $ARGUMENTS

Two forms:
- Pass a shell command (agent runs it, reads failure output, investigates, fixes)
- Pass `--error "<message>"` to investigate a raw error string directly

---

## PLAN

1. Read `.claude/plugins/edugain-agents/pdca-logs/debugger.md` if it exists — apply any learned instructions.
2. Use TodoWrite: run/parse error → identify root cause → fix → verify.
3. State in one sentence: what you think is failing and your first hypothesis.

---

## DO

1. If a shell command was given, run it:
   ```bash
   cd /Users/kreme003/Workspace/git/edugain-qual-improv && \
     source .venv/bin/activate && \
     <command> 2>&1 | tail -60
   ```
2. Read the error output carefully:
   - Find the exact failing file and line number
   - Distinguish between: ImportError, AssertionError, TypeError, AttributeError, etc.
3. Use Grep to find the relevant source file(s) — search for the failing function/class name.
4. Read those source files and the corresponding test file.
5. Identify the **root cause** (not just the symptom).
6. Apply the **minimal fix** — do not refactor unrelated code.
7. Re-run the original command to verify the fix:
   ```bash
   cd /Users/kreme003/Workspace/git/edugain-qual-improv && \
     source .venv/bin/activate && \
     <command> 2>&1 | tail -20
   ```

---

## CHECK

- Does the original command now exit 0 with no failures?
- Was the fix minimal (no unrelated changes)?
- Is the root cause clearly understood (not just symptom-patched)?
- Score: ✅ Fixed and verified / ⚠️ Partially fixed / ❌ Could not fix

---

## ACT

- If ⚠️ or ❌: form a new hypothesis, try a different fix, retry up to 2 more times. If still failing after 3 attempts, report the root cause clearly with a `# TODO: manual intervention needed` comment at the site.
- Always append one entry to `.claude/plugins/edugain-agents/pdca-logs/debugger.md`:

```
## <date> — <brief error description>
**Result**: ✅/⚠️/❌  Retries: <n>
**Root cause**: <one sentence>
**Fix applied**: <what changed and where>
**What worked**: <e.g. "Grep for the class name found it instantly">
**What to improve**: <e.g. "should have checked import chain first">
**Action**: <none / updated Learned Instructions>
---
```

- If the same type of error (e.g. mock setup mistake, import path error) appears in 2+ entries, add a diagnostic shortcut to `## Learned Instructions` below.

---

## Learned Instructions

*(This section is updated automatically by the ACT phase when patterns emerge across runs.)*
