---
name: coordinator
description: Use this skill when the user asks to implement a feature, add functionality,
  build or create something new, fix and test something together, or any multi-step
  request spanning 2+ of these areas — code, tests, docs, review. Trigger phrases
  include "add a feature", "implement X", "build X", "create X with tests", "add X
  and test it", "full feature", "end to end". Do NOT trigger for single-step tasks
  like "read this file" or "explain X".
version: 1.0.0
---

# Coordinator Skill

When this skill activates, **do not attempt to do all the work yourself inline**.
Coordinate specialist subagents for each phase instead.

## What you do as coordinator

You are the orchestrator. You break the request into phases, spawn the right specialist
agent for each phase using the Agent tool, gate on results before proceeding, and
report a clear summary at the end.

## Phase sequence

Run only the phases relevant to the request:

1. **Research** — spawn a researcher agent (read-only: Read, Glob, Grep)
   > "Explore the edugain-qual-improv codebase and identify all files, functions, and patterns relevant to: [request]. List the 5 most important files and explain the architecture to follow."

2. **Implement** — spawn an implementer agent (Read, Write, Edit, Bash, Glob, Grep)
   > "Implement: [request] in the edugain-qual-improv project. Follow CLAUDE.md conventions (module separation, str | None type hints, absolute imports). Read similar files first. Run ruff check and ruff format when done."

3. **Test** — spawn a tester agent (Read, Write, Edit, Bash, Glob, Grep)
   > "Write unit tests for the code just implemented for: [request]. Use class-based tests, unittest.mock for all external deps, tests go in tests/unit/. Run pytest and fix all failures before finishing."

4. **Document** — spawn a documenter agent (Read, Write, Edit, Glob, Grep)
   > "Write Markdown documentation for the feature just implemented: [request]. Output to docs/. Audience is federation operators."

5. **Review** — always run last — spawn a reviewer agent (Read, Bash, Glob, Grep — read-only)
   > "Review all files modified in the last git commit. Check for bugs, SSRF/CSV injection risks, missing type hints, ruff violations. Report by severity [CRITICAL/HIGH/MEDIUM/LOW]. Do NOT edit files."

## Rules

- Always announce the phases you will run before starting
- Read the key files from the Research phase before spawning the Implement phase
- Do not start the next phase if the current phase reports a blocking failure
- After Review: if CRITICAL or HIGH findings exist, fix them directly then re-run ruff
- End with a summary: phases run, files created/modified, test result, review findings

## For the full PDCA workflow, also follow `/coordinator`
