# AI Ready Prompt: Graphical PDF Reports

Goal: add a `--pdf` option to `edugain-analyze` so the default summary, `--report`,
and `--report-with-validation` can render a graphical PDF report. The PDF must
include a summary page plus one page per federation, and it should include KPI
blocks and charts for all major stats. When validation is enabled, include URL
validation charts.

Plan:
- Add CLI flags `--pdf` and `--output` (default to
  `reports/edugain-report-YYYYMMDD-HHMMSS.pdf`).
- Implement a PDF renderer in `src/edugain_analysis/formatters/pdf.py` using
  `matplotlib` (Agg) for charts and `reportlab` for layout.
- Build a summary page with KPI blocks plus charts (privacy, security, SIRTFI,
  SP compliance, and URL validation when enabled).
- Build one page per federation with the same KPI block + charts.
- Use existing `stats` and `federation_stats` from analysis; do not re-run
  analysis or recompute.
- Add optional dependencies under a `[pdf]` extra in `pyproject.toml`:
  `matplotlib`, `reportlab`, and `pillow`.
- Keep output ASCII-only in labels/titles (no emoji).
