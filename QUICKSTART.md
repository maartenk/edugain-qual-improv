# Quick Start: Implementing Roadmap Features

This guide helps you start implementing features from the [eduGAIN Quality Improvement Roadmap](docs/ROADMAP.md) using the [AI-ready prompts](docs/ai-prompts/README.md).

## 📋 Prerequisites

Before starting, ensure you have:

1. **Development Environment Set Up**:
   ```bash
   # Clone the repository
   git clone https://github.com/maartenk/edugain-qual-improv.git
   cd edugain-qual-improv

   # Install dependencies
   make install EXTRAS=dev,tests

   # Activate virtual environment
   source .venv/bin/activate

   # Verify tests pass
   pytest -v
   ```

2. **Familiarity with the Codebase**:
   - Read [CLAUDE.md](CLAUDE.md) for architecture overview
   - Review [README.md](README.md) for project structure
   - Browse existing code in `src/edugain_analysis/`

3. **Choose Your Approach**:
   - **AI-Assisted** (recommended): Use Claude Code, GitHub Copilot, or ChatGPT
   - **Manual**: Follow prompts as detailed specifications

## 🎯 Step 1: Choose a Feature

Browse available features in [docs/ai-prompts/README.md](docs/ai-prompts/README.md).

### Recommended Starting Points

**For Beginners**:
- **Prompt 05**: Dry-Run Mode (2 days) - Small, touches multiple components
- **Prompt 09**: Duplicate Entity Detection (2 days) - Clear, well-defined problem
- **Prompt 10**: Progress Indicators (2 days) - UX improvement, no domain complexity

**For Intermediate**:
- **Prompt 01**: JSON Output Format (2 days) - Learn formatters and CLI
- **Prompt 15**: Entity Category Tracking (2-3 weeks) - Extend existing patterns
- **Prompt 19**: Entity Freshness (2-3 weeks) - New module, clear requirements

**For Advanced**:
- **Prompt 04**: Historical Snapshot Storage (1 week) - Database design
- **Prompt 12**: Time-Series Trend Analysis (3-4 weeks) - Analytics and visualization
- **Prompt 22**: Public Dashboard (2-3 months) - Full web application

### Selection Criteria

Consider:
- **Your skills**: Python, databases, web dev, security, etc.
- **Available time**: 2 days to 3 months
- **Dependencies**: Some features require others (check prompt)
- **Impact**: What provides most value to users?

## 🤖 Step 2: Use the AI Prompt

### Option A: With Claude Code (Recommended)

1. **Read the prompt** to understand scope:
   ```bash
   cat docs/ai-prompts/01-json-output-format.md
   ```

2. **Start Claude Code** and provide the prompt:
   ```bash
   # In your Claude Code session:
   "I want to implement the JSON Output Format feature.
   Please read docs/ai-prompts/01-json-output-format.md
   and implement it following the prompt."
   ```

3. **Review and iterate** with Claude Code:
   - Claude will read files, create code, run tests
   - Review each change before accepting
   - Ask clarifying questions if needed

### Option B: With GitHub Copilot or ChatGPT

1. **Copy the entire prompt** to your AI assistant
2. **Provide context**: "Implement this feature in the edugain-analysis project"
3. **Request specific files**: "Start with the core module, then tests"
4. **Review and edit**: AI-generated code needs human oversight

### Option C: Manual Implementation

1. **Read the prompt thoroughly** (objectives, requirements, implementation)
2. **Follow step-by-step** guidance in "Implementation Guidance" section
3. **Copy code examples** and adapt to your codebase
4. **Write tests first** (TDD approach) using test examples from prompt

## 🔧 Step 3: Implement the Feature

### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/json-output-format
   ```

2. **Follow the prompt structure**:
   - Create new modules (if specified)
   - Modify existing files (as indicated)
   - Add CLI flags (if applicable)
   - Update formatters/output

3. **Write tests as you go**:
   ```bash
   # Create test file
   touch tests/unit/test_json_formatter.py

   # Write tests (examples in prompt)
   # Run tests frequently
   pytest tests/unit/test_json_formatter.py -v
   ```

4. **Add type hints and docstrings**:
   ```python
   def format_json_output(stats: Dict, compact: bool = False) -> str:
       """
       Format statistics as JSON.

       Args:
           stats: Statistics dictionary
           compact: If True, minify JSON (no indentation)

       Returns:
           JSON string
       """
       # Implementation
   ```

5. **Check code quality**:
   ```bash
   # Linting
   ruff check src/ tests/

   # Formatting
   ruff format src/ tests/

   # Type checking (if using mypy)
   mypy src/
   ```

### Testing Strategy

Follow the **Testing Strategy** section in each prompt:

```bash
# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run specific test
pytest tests/unit/test_json_formatter.py::test_format_json_compact -v

# Check coverage
pytest --cov=src/edugain_analysis --cov-report=html
open htmlcov/index.html
```

### Common Patterns

Most features follow this structure:

```
src/edugain_analysis/
├── core/                    # Business logic
│   ├── new_module.py       # New functionality
│   └── analysis.py         # Integration point
├── formatters/             # Output formatting
│   └── base.py            # Add new formatter
└── cli/                    # Command-line interface
    └── main.py            # Add CLI flags

tests/
├── unit/
│   └── test_new_module.py  # Unit tests
└── integration/
    └── test_feature_e2e.py # End-to-end tests
```

## ✅ Step 4: Verify Your Implementation

### Acceptance Criteria

Each prompt has an **Acceptance Criteria** section. Verify all items:

- [ ] All functional requirements met
- [ ] All quality requirements met
- [ ] All tests pass
- [ ] Code follows project style
- [ ] Documentation updated

### Manual Testing

```bash
# Test with real metadata
edugain-analyze --json output.json

# Verify output
cat output.json | jq .

# Test edge cases (as specified in prompt)
edugain-analyze --json --compact output-compact.json

# Test error handling
edugain-analyze --json /invalid/path.json
```

### Integration Testing

```bash
# Run full analysis with new feature
edugain-analyze --json report.json --validate

# Compare with expected behavior from prompt
diff expected-output.json report.json
```

## 📝 Step 5: Documentation and Cleanup

### Update Documentation

1. **CHANGELOG.md**:
   ```markdown
   ## [Unreleased]

   ### Added
   - JSON output format with `--json` flag (#123)
   - Compact JSON mode with `--compact` option
   ```

2. **README.md** (if user-facing):
   ```markdown
   ### JSON Output

   Export analysis results as JSON:
   ```bash
   edugain-analyze --json output.json
   ```
   ```

3. **Inline documentation**:
   - Docstrings for all public functions
   - Comments for complex logic
   - Type hints for all parameters

### Clean Up

```bash
# Remove debug prints
grep -r "print(" src/

# Remove commented code
# (manually review)

# Check for TODO comments
grep -r "TODO" src/

# Ensure no secrets or credentials
git secrets --scan

# Final test run
pytest -v
ruff check src/ tests/
```

## 🚀 Step 6: Submit Your Work

### Commit Your Changes

```bash
# Stage files
git add src/ tests/ docs/

# Commit with descriptive message
git commit -m "feat: add JSON output format

- Add --json flag for JSON export
- Support compact mode with --compact
- Include all statistics in structured format
- Add comprehensive test coverage

Implements: #123
Prompt: docs/ai-prompts/01-json-output-format.md"

# Push to remote
git push origin feature/json-output-format
```

### Create Pull Request

```bash
# Using gh CLI
gh pr create --title "feat: Add JSON output format" \
             --body "## Description

Implements JSON output format for analysis results.

## Changes
- Added \`--json\` CLI flag
- Created \`formatters/json.py\` module
- Added comprehensive tests (95% coverage)

## Testing
\`\`\`bash
edugain-analyze --json output.json
pytest tests/unit/test_json_formatter.py -v
\`\`\`

## Checklist
- [x] Tests pass
- [x] Documentation updated
- [x] Follows code style
- [x] Acceptance criteria met

## References
- Prompt: docs/ai-prompts/01-json-output-format.md
- Issue: #123"
```

### Review Process

1. **Self-review** your PR
2. **Request reviews** from maintainers
3. **Address feedback** promptly
4. **Iterate** until approved
5. **Squash and merge** (or as project prefers)

## 💡 Tips and Best Practices

### Do's ✅

- **Start small**: Pick a 2-day prompt first
- **Follow the prompt**: It's been carefully designed
- **Write tests first**: TDD approach ensures quality
- **Ask questions**: Use GitHub issues or discussions
- **Review examples**: Check existing code for patterns
- **Run tests frequently**: Catch issues early
- **Document as you go**: Don't leave it for the end

### Don'ts ❌

- **Don't skip tests**: They're critical for quality
- **Don't ignore edge cases**: Prompts list them for a reason
- **Don't commit broken code**: Always verify tests pass
- **Don't reinvent patterns**: Follow existing codebase conventions
- **Don't add dependencies without discussion**: Keep it lean
- **Don't make breaking changes**: Maintain backward compatibility

### Common Pitfalls

1. **Skipping the prompt's "Context" section**
   - Always understand *why* the feature is needed

2. **Ignoring dependencies**
   - Some features require others (check prompt)

3. **Not testing edge cases**
   - Prompts list edge cases - test them all

4. **Over-engineering**
   - Follow the prompt, don't add extra features

5. **Inadequate error handling**
   - Prompts specify error cases - handle them

## 📚 Additional Resources

### Project Documentation
- [ROADMAP.md](docs/ROADMAP.md) - Full feature roadmap
- [CLAUDE.md](CLAUDE.md) - Architecture and design
- [README.md](README.md) - Project overview
- [docs/ai-prompts/README.md](docs/ai-prompts/README.md) - Prompt index

### AI Prompt Guides
- **Implementation Paths**: 6 different approaches in prompt README
- **Effort Estimates**: Plan your timeline
- **Dependencies**: See which features build on others

### Getting Help
- **Issues**: Report bugs or ask questions
- **Discussions**: General development questions
- **Pull Requests**: Get code review feedback

## 🎯 Example: Complete Workflow

Here's a complete example implementing Prompt 09 (Duplicate Detection):

```bash
# 1. Choose feature
open docs/ai-prompts/09-duplicate-entity-detection.md

# 2. Create branch
git checkout -b feature/duplicate-detection

# 3. Start implementation (with Claude Code)
# "Implement duplicate entity detection from docs/ai-prompts/09-duplicate-entity-detection.md"

# 4. Write tests first
cat > tests/unit/test_duplicate_detection.py << 'EOF'
def test_detect_duplicates():
    """Test duplicate detection."""
    # Test code from prompt
    assert ...
EOF

# 5. Implement feature
# (follow prompt's step-by-step guidance)

# 6. Run tests
pytest tests/unit/test_duplicate_detection.py -v

# 7. Integration test
edugain-analyze --deduplicate

# 8. Check quality
ruff check src/ tests/
pytest --cov=src/edugain_analysis

# 9. Commit
git add -A
git commit -m "feat: add duplicate entity detection

- Detects duplicate entity IDs
- Flags: --deduplicate, --fail-on-duplicates
- Exports: --csv duplicates
- Test coverage: 98%

Implements: docs/ai-prompts/09-duplicate-entity-detection.md"

# 10. Push and create PR
git push origin feature/duplicate-detection
gh pr create
```

## 🚦 Ready to Start?

1. **Browse prompts**: [docs/ai-prompts/README.md](docs/ai-prompts/README.md)
2. **Pick your first feature**: Start with something small
3. **Follow this guide**: Step by step
4. **Have fun coding!** 🎉

---

**Questions?** Open an issue with `[Quick Start]` prefix or see the full documentation.

**First contribution?** Welcome! We're here to help. 👋
