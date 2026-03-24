---
description: Run a full feature end-to-end: research → implement → test → document → review
argument-hint: "<feature description>" [--skip-research] [--skip-codegen] [--skip-tests] [--skip-doc]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Agent]
---

## Task

Deliver this feature end-to-end: $ARGUMENTS

Optional skip flags: `--skip-research`, `--skip-codegen`, `--skip-tests`, `--skip-doc`

**Always run on a feature branch. This command modifies files.**

---

## PLAN

1. Read `.claude/plugins/edugain-agents/pdca-logs/coordinator.md` if it exists — apply any learned instructions.
2. Parse the description and any skip flags from `$ARGUMENTS`.
3. Use TodoWrite to create one task per active phase: Research → Implement → Test → Document → Review.
4. State in one sentence what will be built and which phases will run.

---

## DO

Execute each active phase in order. For each phase, spawn a focused subagent using the Agent tool with specific instructions and only the tools it needs:

### Phase 1 — Research (skip if `--skip-research`)
Spawn an Agent with tools `[Read, Glob, Grep]`:
> "Explore the edugain-qual-improv codebase and identify all files, functions, and patterns relevant to: [description]. List the 5 most important files to read and explain the existing architecture I should follow."

Read the files the agent identified before moving to Phase 2.

### Phase 2 — Implement (skip if `--skip-codegen`)
Spawn an Agent with tools `[Read, Write, Edit, Bash, Glob, Grep]`:
> "Implement the following feature in the edugain-qual-improv project: [description]. Follow CLAUDE.md conventions (module separation, str | None type hints, absolute imports). Read similar existing files first. Run ruff check and ruff format when done."

### Phase 3 — Test (skip if `--skip-tests`)
Spawn an Agent with tools `[Read, Write, Edit, Bash, Glob, Grep]`:
> "Write comprehensive unit tests for the code just implemented for: [description]. Follow project conventions: class-based tests, unittest.mock for all external deps, tests go in tests/unit/. Run pytest and fix any failures before finishing."

### Phase 4 — Document (skip if `--skip-doc`)
Spawn an Agent with tools `[Read, Write, Edit, Glob, Grep]`:
> "Generate or update Markdown documentation for the feature just implemented: [description]. Write to docs/ as a new file or append to an existing relevant doc. Be concise. Audience is federation operators."

### Phase 5 — Review (always runs)
Spawn an Agent with tools `[Read, Bash, Glob, Grep]` (read-only):
> "Review all recently git-modified files in the edugain-qual-improv project (run: git diff --name-only HEAD). For each changed file, check for bugs, SSRF/CSV injection risks, missing type hints, and ruff violations. Report findings by severity. Do NOT fix."

After the review agent returns, display its findings to the user.

---

## CHECK

- Did each phase complete without blocking errors?
- Do all tests pass? (Re-run pytest if unsure)
- Are there any CRITICAL or HIGH review findings that must be fixed before committing?
- Score: ✅ All phases clean / ⚠️ Review findings need attention / ❌ Tests failing or blocked

---

## ACT

- If ❌ tests failing: spawn another Test agent with the failure output as context — fix and re-run.
- If ⚠️ critical review findings: fix them directly (Edit), then re-run ruff to confirm.
- Always append one entry to `.claude/plugins/edugain-agents/pdca-logs/coordinator.md`:

```
## <date> — "<feature description (first 60 chars)>"
**Result**: ✅/⚠️/❌  Phases run: <list>
**Files created/modified**: <list>
**Test result**: <n passed / n failed>
**Review findings**: CRITICAL=<n> HIGH=<n>
**What worked**: <e.g. "research phase found the right pattern quickly">
**What to improve**: <e.g. "test phase needed a retry due to mock setup">
**Action**: <none / updated Learned Instructions>
---
```

- If the same phase consistently fails or needs retries across 2+ entries, add a targeted instruction to `## Learned Instructions` below.

---

## Learned Instructions

*(This section is updated automatically by the ACT phase when patterns emerge across runs.)*
