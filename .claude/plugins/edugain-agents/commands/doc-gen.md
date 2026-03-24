---
description: Generate Markdown documentation from a source file or directory
argument-hint: <source_path> --output <doc_path>
allowed-tools: [Read, Write, Edit, Glob, Grep]
---

## Task

Generate Markdown documentation for: $ARGUMENTS

Required flag: `--output <path>` — the destination Markdown file.

---

## PLAN

1. Read `.claude/plugins/edugain-agents/pdca-logs/doc-gen.md` if it exists — apply any learned instructions.
2. Use TodoWrite: list source files → read each → write doc → review doc.
3. State in one sentence: is the source a single file or a directory, and what the output file will be named.

---

## DO

1. If the source is a directory: use Glob `<source_path>/**/*.py` to list all Python files. Skip `__init__.py` unless it has content.
2. If the source is a single file: read it directly.
3. For each file extract:
   - Module docstring
   - All public functions/classes (not prefixed with `_`)
   - Their signatures, docstrings, parameters, return values, raised exceptions
4. Write a Markdown document to the output path with:
   - `# Module Name` top-level heading
   - 2–3 sentence overview paragraph
   - One `## FunctionName` or `## ClassName` section per public symbol
   - Signature in a code block
   - Prose explanation (not a copy of the docstring — add context)
   - `### Example` subsection for the most important function
5. Read the output file back to check it renders well.

---

## CHECK

- Does the doc cover all public symbols?
- Is the prose actually helpful (not just docstring copy-paste)?
- Are code examples syntactically correct?
- Score: ✅ Complete and useful / ⚠️ Missing some symbols or thin prose / ❌ Major gaps

---

## ACT

- If ⚠️: fill missing sections or expand thin prose, then re-read.
- Always append one entry to `.claude/plugins/edugain-agents/pdca-logs/doc-gen.md`:

```
## <date> — <source_path>
**Result**: ✅/⚠️/❌  Symbols documented: <n>
**Approach**: <single file or directory walk>
**What worked**: <e.g. "reading module docstring set the tone for the overview">
**What to improve**: <e.g. "missed private-but-important helper functions">
**Action**: <none / updated Learned Instructions>
---
```

- If the same gap appears in 2+ past entries, add a rule to `## Learned Instructions` below.

---

## Learned Instructions

*(This section is updated automatically by the ACT phase when patterns emerge across runs.)*
