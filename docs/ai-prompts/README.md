# AI-Ready Implementation Prompts

This directory contains comprehensive, AI-ready prompts for implementing features from the [ROADMAP.md](../ROADMAP.md). Each prompt is designed to be self-contained and can be given to an AI coding assistant (like Claude Code, GitHub Copilot, or ChatGPT) for autonomous implementation.

## 📋 Available Prompts

### 🚀 Quick Wins (High Impact, Low Effort)

| # | Feature | Priority | Effort | File |
|---|---------|----------|--------|------|
| 1 | **JSON Output Format** | HIGH | 2 days | [01-json-output-format.md](01-json-output-format.md) |
| 2 | **Exit Codes for Quality Thresholds** | HIGH | 1 day | [02-exit-codes-quality-thresholds.md](02-exit-codes-quality-thresholds.md) |
| 3 | **Actionable Insights Report** | HIGH | 1 week | [03-actionable-insights-report.md](03-actionable-insights-report.md) |

### 📊 Foundation Building (Enables Future Features)

| # | Feature | Priority | Effort | File |
|---|---------|----------|--------|------|
| 4 | **Historical Snapshot Storage** | HIGH | 1 week | [04-historical-snapshot-storage.md](04-historical-snapshot-storage.md) |
| 5 | **Dry-Run Mode for Validation** | MEDIUM-HIGH | 2 days | [05-dry-run-mode-validation.md](05-dry-run-mode-validation.md) |

### 🔍 Quality Improvements (Enhanced Validation)

| # | Feature | Priority | Effort | File |
|---|---------|----------|--------|------|
| 6 | **IdP Privacy Statement Tracking** | HIGH | 1-2 weeks | [06-idp-privacy-statement-tracking.md](06-idp-privacy-statement-tracking.md) |
| 7 | **Security Contact Quality Validation** | HIGH | 1-2 weeks | [07-security-contact-quality-validation.md](07-security-contact-quality-validation.md) |
| 8 | **Privacy URL Content Quality Analysis** | MEDIUM-HIGH | 2-3 weeks | [08-privacy-url-content-quality.md](08-privacy-url-content-quality.md) |

### 🎯 Tier 1: Data Quality & Analysis (Additional Features)

| # | Feature | Priority | Effort | File |
|---|---------|----------|--------|------|
| 9 | **Duplicate Entity ID Detection** | HIGH (CRITICAL) | 2 days | [09-duplicate-entity-detection.md](09-duplicate-entity-detection.md) |
| 10 | **Progress Indicators for Long Operations** | MEDIUM | 2 days | [10-progress-indicators.md](10-progress-indicators.md) |
| 11 | **Placeholder/Template URL Detection** | MEDIUM-HIGH | 2 days | [11-placeholder-url-detection.md](11-placeholder-url-detection.md) |
| 12 | **Time-Series Trend Analysis** | HIGH | 3-4 weeks | [12-time-series-trend-analysis.md](12-time-series-trend-analysis.md) |
| 13 | **Federation Benchmarking & Peer Comparison** | HIGH | 2 weeks | [13-federation-benchmarking.md](13-federation-benchmarking.md) |

### 🔧 Tier 2: Advanced Features & Phase 2 Completion

| # | Feature | Priority | Effort | File |
|---|---------|----------|--------|------|
| 14 | **Metadata Completeness Scoring** | MEDIUM-HIGH | 3-4 weeks | [14-metadata-completeness-scoring.md](14-metadata-completeness-scoring.md) |
| 15 | **Additional Entity Category Tracking** | MEDIUM | 2-3 weeks | [15-additional-entity-category-tracking.md](15-additional-entity-category-tracking.md) |
| 16 | **Automated Alerting System** | MEDIUM | 3-4 weeks | [16-automated-alerting-system.md](16-automated-alerting-system.md) |
| 17 | **Enhanced PDF Reports with Executive Summary** | MEDIUM | 3 weeks | [17-enhanced-pdf-reports-executive-summary.md](17-enhanced-pdf-reports-executive-summary.md) |
| 18 | **Differential Comparison & Baseline Mode** | MEDIUM | 4 weeks | [18-differential-comparison-baseline-mode.md](18-differential-comparison-baseline-mode.md) |

### 🚀 Tier 3: Phase 3 Strategic Platform Features

| # | Feature | Priority | Effort | File |
|---|---------|----------|--------|------|
| 19 | **Entity Freshness & Activity Tracking** | LOW | 2-3 weeks | [19-entity-freshness-activity-tracking.md](19-entity-freshness-activity-tracking.md) |
| 20 | **Multi-Lingual Support Quality Assessment** | LOW | 4-5 weeks | [20-multilingual-support-quality.md](20-multilingual-support-quality.md) |
| 21 | **Certificate & Encryption Quality Analysis** | LOW-MEDIUM | 6-8 weeks | [21-certificate-encryption-quality.md](21-certificate-encryption-quality.md) |
| 22 | **Public-Facing Quality Dashboard** | MEDIUM | 2-3 months | [22-public-quality-dashboard.md](22-public-quality-dashboard.md) |

## 🎯 Recommended Implementation Order

### Path 1: Quick Automation Wins
Best for: Enabling CI/CD integration and automated workflows
```
1. JSON Output Format (2 days)
   ↓
2. Exit Codes for Quality Thresholds (1 day)
   ↓
3. Actionable Insights Report (1 week)
```
**Total**: ~2 weeks, **Value**: Immediate automation capabilities

### Path 2: Data-Driven Analysis
Best for: Long-term tracking and trend analysis
```
1. Historical Snapshot Storage (1 week)
   ↓
2. IdP Privacy Statement Tracking (1-2 weeks)
   ↓
3. Privacy URL Content Quality Analysis (2-3 weeks)
```
**Total**: 4-6 weeks, **Value**: Comprehensive quality insights

### Path 3: User Experience First
Best for: Immediate operator value
```
1. Dry-Run Mode for Validation (2 days)
   ↓
2. Actionable Insights Report (1 week)
   ↓
3. Security Contact Quality Validation (1-2 weeks)
```
**Total**: 2-4 weeks, **Value**: Improved usability and guidance

### Path 4: Data Quality & Benchmarking
Best for: Improving data accuracy and competitive analysis
```
1. Duplicate Entity ID Detection (2 days) [CRITICAL]
   ↓
2. Placeholder URL Detection (2 days)
   ↓
3. Progress Indicators (2 days) [UX improvement]
   ↓
4. Federation Benchmarking (2 weeks)
   ↓
5. Time-Series Trend Analysis (3-4 weeks)
   [Requires Historical Snapshot Storage from Path 2]
```
**Total**: 6-8 weeks, **Value**: Accurate metrics, competitive insights, trend tracking

### Path 5: Phase 2 Advanced Features (Tier 2)
Best for: Comprehensive quality improvement platform
```
1. Additional Entity Category Tracking (2-3 weeks) [Quick win]
   ↓
2. Metadata Completeness Scoring (3-4 weeks)
   ↓
3. Differential Comparison & Baseline Mode (4 weeks)
   [Requires Historical Snapshot Storage from Path 2]
   ↓
4. Enhanced PDF Reports with Executive Summary (3 weeks)
   ↓
5. Automated Alerting System (3-4 weeks)
   [Requires Historical Snapshot Storage + Baseline Mode]
```
**Total**: 15-18 weeks, **Value**: Complete strategic quality improvement platform for federation leadership

### Path 6: Phase 3 Strategic Platform (Tier 3)
Best for: Public transparency and community engagement
```
1. Entity Freshness & Activity Tracking (2-3 weeks) [Quick win, cleanup focus]
   ↓
2. Multi-Lingual Support Quality Assessment (4-5 weeks) [Accessibility]
   ↓
3. Certificate & Encryption Quality Analysis (6-8 weeks) [Security deep-dive]
   ↓
4. Public-Facing Quality Dashboard (2-3 months) [Flagship web platform]
   [Requires all previous features for complete dashboard]
```
**Total**: 15-20 weeks, **Value**: Full public platform with transparency, API access, and community engagement

## 🤖 How to Use These Prompts

### With Claude Code (Recommended)

1. **Select a feature** from the list above
2. **Read the prompt file** to understand scope and requirements
3. **Copy the entire prompt** into Claude Code
4. **Add context**: "Please implement this feature following the prompt"
5. **Review and test** the implementation
6. **Iterate** with Claude Code if adjustments needed

**Example**:
```bash
# In your terminal with Claude Code active
cat docs/ai-prompts/01-json-output-format.md | pbcopy

# Then in Claude Code:
"Please implement the JSON output format feature as described in this prompt: [paste]"
```

### With GitHub Copilot or ChatGPT

1. **Open the prompt file** in your editor
2. **Copy the prompt** to clipboard
3. **Paste into chat** with context: "Implement this feature in the edugain-analysis project"
4. **Provide additional files** if the AI requests them (use file references from prompt)
5. **Follow test-driven development** approach outlined in prompt

### Manual Implementation

Each prompt includes:
- ✅ **Objective** and context
- ✅ **Requirements** and acceptance criteria
- ✅ **Implementation guidance** with code examples
- ✅ **Testing strategy** with example tests
- ✅ **Success metrics**

You can use these as detailed implementation specs even without AI assistance.

## 📐 Prompt Structure

Each prompt follows a consistent structure:

```markdown
# Feature Name

**Priority**: HIGH/MEDIUM/LOW
**Effort**: X days/weeks
**Type**: Check/Report/Infrastructure

## Objective
[What to build]

## Context
[Why it's needed, current state, problems]

## Requirements
[Detailed functional requirements]

## Implementation Details
[Files to modify, algorithms, edge cases]

## Acceptance Criteria
[How to know when it's done]

## Testing Strategy
[Unit tests, integration tests, examples]

## Implementation Guidance
[Step-by-step code examples]

## Success Metrics
[How to measure success]
```

## 🔧 Prerequisites

Before implementing any feature, ensure:

1. **Development environment** is set up:
   ```bash
   make install EXTRAS=dev,tests
   source .venv/bin/activate
   ```

2. **Tests are passing**:
   ```bash
   pytest -v
   ```

3. **You understand the codebase**:
   - Read [CLAUDE.md](../../CLAUDE.md) for architecture overview
   - Review current implementation in relevant files

## ✅ Implementation Checklist

For each feature implementation:

- [ ] Read entire prompt and understand requirements
- [ ] Review current codebase (files mentioned in prompt)
- [ ] Create feature branch: `git checkout -b feature/feature-name`
- [ ] Implement core functionality
- [ ] Add type hints and docstrings
- [ ] Write unit tests (aim for >90% coverage)
- [ ] Write integration tests
- [ ] Update documentation (README, CHANGELOG)
- [ ] Run all tests: `pytest -v`
- [ ] Run linting: `ruff check src/ tests/`
- [ ] Run formatting: `ruff format src/ tests/`
- [ ] Commit with descriptive message
- [ ] Push and create pull request

## 📊 Effort Estimates

| Complexity | Effort Range | Example Features |
|------------|--------------|------------------|
| **Low** | 1-2 days | JSON Output, Exit Codes, Dry-Run Mode |
| **Medium** | 1-2 weeks | Actionable Insights, Historical Storage, IdP Privacy |
| **High** | 2-3 weeks | Content Quality Analysis |

Estimates assume:
- Familiarity with Python and the codebase
- AI assistance for code generation
- Includes testing and documentation

## 🎓 Learning Path

New to the codebase? Suggested learning order:

1. **Start simple**: Implement "Dry-Run Mode" (prompt #5)
   - Small scope, touches multiple components
   - Good introduction to validation system

2. **Add value**: Implement "JSON Output Format" (prompt #1)
   - Learn about formatters and CLI integration
   - Immediate user value

3. **Go deeper**: Implement "Security Contact Quality Validation" (prompt #7)
   - Create new module from scratch
   - Practice validation patterns

## 🤝 Contributing

After implementing a feature:

1. **Update ROADMAP.md**: Mark feature as completed
2. **Update CHANGELOG.md**: Document changes
3. **Add migration guide**: If breaking changes
4. **Submit PR**: Reference the prompt file in description
5. **Request review**: From project maintainers

## 📞 Support

- **Questions about prompts**: Open an issue with `[AI-Prompt]` prefix
- **Implementation help**: Reference the prompt number in your question
- **General development**: See [CLAUDE.md](../../CLAUDE.md)

## 📜 License

These prompts are part of the eduGAIN Analysis project and follow the same MIT license.

---

**Last Updated**: 2026-01-18
**Total Prompts**: 22
**Estimated Total Effort**: 44-59 weeks (depending on path)

**Coverage**: All 3 phases of the ROADMAP completed! 🎉
