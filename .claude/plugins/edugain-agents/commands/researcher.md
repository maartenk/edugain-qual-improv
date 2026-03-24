---
description: Answer read-only questions about the edugain codebase
argument-hint: "<question>"
allowed-tools: [Read, Glob, Grep]
---

## Task

Answer this question about the codebase: $ARGUMENTS

---

## PLAN

1. Read `.claude/plugins/edugain-agents/pdca-logs/researcher.md` if it exists — apply any learned instructions from past runs.
2. Use TodoWrite to create a task list: identify what files likely hold the answer, then read/grep them.
3. State your search strategy in one sentence before starting.

---

## DO

- Use Grep to find relevant code by keyword first — faster than reading blindly.
- Use Glob to discover file structure when unsure where to look.
- Use Read to read the specific files/sections Grep points to.
- Cite every claim with `file:line` — do not state things you cannot confirm from the code.
- If the answer spans multiple files, trace the call chain (e.g. CLI → core → formatter).
- Keep the answer concise but complete. Use headers if multiple aspects are covered.

---

## CHECK

- Re-read your answer. Does every factual claim have a file:line citation?
- Did you actually answer the question asked, or drift to adjacent topics?
- Score: ✅ Fully answered / ⚠️ Partial (note what's missing) / ❌ Could not find answer

---

## ACT

- If ❌ or ⚠️: try a different Grep pattern or look in test files for usage examples, then re-answer.
- Always append one entry to `.claude/plugins/edugain-agents/pdca-logs/researcher.md`:

```
## <date> — "<question (first 60 chars)>"
**Result**: ✅/⚠️/❌
**Approach**: <what you searched and how>
**What worked**: <most effective search strategy>
**What to improve**: <anything that wasted time or was missing>
**Action**: <none / updated Learned Instructions>
---
```

- If the same inefficiency appears in 2 or more past log entries, add a concise rule to `## Learned Instructions` below.

---

## Learned Instructions

*(This section is updated automatically by the ACT phase when patterns emerge across runs.)*
