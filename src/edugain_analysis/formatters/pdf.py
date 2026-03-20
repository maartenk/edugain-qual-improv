"""
Graphical PDF report rendering for eduGAIN analysis results.

Generates a summary page and one page per federation with KPI blocks and charts.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

PAGE_MARGIN = 36
HEADER_HEIGHT = 44
KPI_ROW_HEIGHT = 34
KPI_ROW_GAP = 8
KPI_COLS = 3
CHART_GAP = 14
FOOTER_HEIGHT = 18
MAX_CHART_SLOT_H = 240  # pt — cap chart slot height to prevent huge empty spaces

PALETTE = {
    "blue": "#1E5AA8",
    "green": "#2E7D32",
    "orange": "#EF6C00",
    "red": "#C62828",
    "teal": "#00897B",
    "gray": "#455A64",
    "light_gray": "#F4F5F6",
    "purple": "#7B1FA2",
    "yellow": "#F9A825",
}


@dataclass
class ChartImage:
    image: ImageReader
    buffer: io.BytesIO


def _pct(part: int, total: int) -> float:
    return (part / total * 100.0) if total else 0.0


def _image_from_figure(fig) -> ChartImage:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return ChartImage(image=ImageReader(buf), buffer=buf)


def _pie_chart(values, labels, colors_list, title, donut=False, center_label=None):
    # Filter out zero-value segments to keep legend and chart clean
    non_zero = [
        (v, lb, c)
        for v, lb, c in zip(values, labels, colors_list, strict=False)
        if v > 0
    ]
    if not non_zero:
        return None
    values, labels, colors_list = zip(*non_zero, strict=False)

    fig, ax = plt.subplots(figsize=(3.6, 3.0), dpi=150)
    autopct = None

    if not donut:
        total = sum(values)

        def autopct_fn(pct):
            count = int(round(pct * total / 100.0))
            return f"{pct:.0f}%" if count > 0 else ""

        autopct = autopct_fn

    result = ax.pie(
        values,
        colors=colors_list,
        startangle=90,
        autopct=autopct,
        textprops={"fontsize": 7},
    )
    wedges = result[0]

    if donut:
        centre = plt.Circle((0, 0), 0.60, fc="white")
        ax.add_artist(centre)
        if center_label:
            ax.text(
                0,
                0,
                center_label,
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
            )

    if labels:
        ax.legend(
            wedges,
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.08),
            ncol=2,
            frameon=False,
            fontsize=7,
        )

    ax.set_title(title, fontsize=10, pad=8)
    ax.axis("equal")
    fig.tight_layout()
    return _image_from_figure(fig)


def _bar_chart(labels, values, colors_list, title):
    fig, ax = plt.subplots(figsize=(3.4, 2.5), dpi=150)
    bar_width = 0.4 if len(values) == 1 else 0.6
    bars = ax.bar(labels, values, color=colors_list, width=bar_width)

    max_val = max(values) if values else 0
    # Allow ylim to exceed 100 to give headroom for data labels above bars
    ylim_top = min(118, max_val * 1.18 + 2) if max_val > 0 else 100
    ax.set_ylim(0, ylim_top)

    ax.set_ylabel("Percent", fontsize=8)
    ax.set_title(title, fontsize=10, pad=8)
    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)

    for bar, value in zip(bars, values, strict=False):
        label_y = value + ylim_top * 0.02
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            label_y,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.tight_layout()
    return _image_from_figure(fig)


def _make_styled_table(
    title: str,
    table_data: list[list[str]],
    col_widths: list[float],
    header_color: str,
    fig_size: tuple[float, float] = (3.4, 2.3),
) -> ChartImage:
    """Create a styled matplotlib table as a ChartImage."""
    fig, ax = plt.subplots(figsize=fig_size, dpi=150)
    ax.axis("tight")
    ax.axis("off")

    table = ax.table(
        cellText=table_data,
        cellLoc="left",
        loc="center",
        colWidths=col_widths,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.5)

    num_cols = len(table_data[0])
    for j in range(num_cols):
        cell = table[(0, j)]
        cell.set_facecolor(header_color)
        cell.set_text_props(weight="bold", color="white")
        cell.set_linewidth(0.5)
        cell.set_edgecolor(header_color)

    for i in range(1, len(table_data)):
        for j in range(num_cols):
            cell = table[(i, j)]
            cell.set_facecolor("#F4F5F6" if i % 2 == 0 else "white")
            if j > 0:
                cell.set_text_props(ha="right")
            cell.set_linewidth(0.5)
            cell.set_edgecolor("#E0E0E0")

    ax.set_title(title, fontsize=9, weight="bold", pad=10)
    return _image_from_figure(fig)


def _kpi_accent(label: str, value: str) -> str:
    """Return a PALETTE hex color as the KPI left-border accent based on metric value."""
    import re

    if "N/A" in value:
        return PALETTE["gray"]
    m = re.search(r"(\d+\.?\d*)%", value)
    if m:
        pct = float(m.group(1))
        if "Score" in label:
            return (
                PALETTE["green"]
                if pct >= 70
                else (PALETTE["orange"] if pct >= 50 else PALETTE["red"])
            )
        return (
            PALETTE["green"]
            if pct >= 80
            else (PALETTE["orange"] if pct >= 50 else PALETTE["red"])
        )
    return PALETTE["blue"]


def _build_kpis(
    stats: dict, include_content_validation: bool = False
) -> list[tuple[str, str, str]]:
    """Return list of (label, value, accent_color) triples for KPI blocks."""
    total = stats.get("total_entities", 0)
    total_sps = stats.get("total_sps", 0)
    total_idps = stats.get("total_idps", 0)

    sp_privacy_pct = _pct(stats.get("sps_has_privacy", 0), total_sps)
    idp_privacy_pct = _pct(stats.get("idps_has_privacy", 0), total_idps)
    security_pct = _pct(stats.get("total_has_security", 0), total)
    sirtfi_pct = _pct(stats.get("total_has_sirtfi", 0), total)

    raw: list[tuple[str, str]] = [
        ("Total Entities", f"{total:,}"),
        ("Service Providers", f"{total_sps:,}"),
        ("Identity Providers", f"{total_idps:,}"),
        (
            "Privacy Coverage (SPs)",
            "N/A"
            if total_sps == 0
            else f"{stats.get('sps_has_privacy', 0):,}/{total_sps:,} ({sp_privacy_pct:.1f}%)",
        ),
        (
            "Privacy Coverage (IdPs)",
            "N/A"
            if total_idps == 0
            else f"{stats.get('idps_has_privacy', 0):,}/{total_idps:,} ({idp_privacy_pct:.1f}%)",
        ),
        (
            "Security Coverage",
            "N/A"
            if total == 0
            else f"{stats.get('total_has_security', 0):,}/{total:,} ({security_pct:.1f}%)",
        ),
        (
            "SIRTFI Coverage",
            "N/A"
            if total == 0
            else f"{stats.get('total_has_sirtfi', 0):,}/{total:,} ({sirtfi_pct:.1f}%)",
        ),
    ]

    if include_content_validation:
        scores = stats.get("content_quality_scores", [])
        if scores:
            avg_score = sum(scores) / len(scores)
            raw.append(("Avg Privacy Quality Score", f"{avg_score:.0f}/100"))

    return [(label, value, _kpi_accent(label, value)) for label, value in raw]


def _build_charts(
    stats: dict, include_validation: bool, include_content_validation: bool = False
) -> list[ChartImage]:
    charts: list[ChartImage] = []
    total = stats.get("total_entities", 0)
    total_sps = stats.get("total_sps", 0)
    total_idps = stats.get("total_idps", 0)

    # Privacy statement comparison: SP vs IdP
    if total_sps > 0 or total_idps > 0:
        privacy_labels, privacy_values, privacy_colors = [], [], []
        if total_sps > 0:
            sp_privacy_pct = _pct(stats.get("sps_has_privacy", 0), total_sps)
            privacy_labels.append(
                f"SPs\n{stats.get('sps_has_privacy', 0):,}/{total_sps:,}"
            )
            privacy_values.append(sp_privacy_pct)
            privacy_colors.append(PALETTE["green"])
        if total_idps > 0:
            idp_privacy_pct = _pct(stats.get("idps_has_privacy", 0), total_idps)
            privacy_labels.append(
                f"IdPs\n{stats.get('idps_has_privacy', 0):,}/{total_idps:,}"
            )
            privacy_values.append(idp_privacy_pct)
            privacy_colors.append(PALETTE["purple"])
        if privacy_labels and any(v > 0 for v in privacy_values):
            charts.append(
                _bar_chart(
                    privacy_labels,
                    privacy_values,
                    privacy_colors,
                    "Privacy Statements (by Entity Type)",
                )
            )

    if total > 0:
        sec_labels, sec_values, sec_colors = [], [], []
        if total_sps > 0:
            sec_labels.append(
                f"SPs\n{stats.get('sps_has_security', 0):,}/{total_sps:,}"
            )
            sec_values.append(_pct(stats.get("sps_has_security", 0), total_sps))
            sec_colors.append(PALETTE["blue"])
        if total_idps > 0:
            sec_labels.append(
                f"IdPs\n{stats.get('idps_has_security', 0):,}/{total_idps:,}"
            )
            sec_values.append(_pct(stats.get("idps_has_security", 0), total_idps))
            sec_colors.append(PALETTE["teal"])
        if sec_labels and any(v > 0 for v in sec_values):
            charts.append(
                _bar_chart(
                    sec_labels,
                    sec_values,
                    sec_colors,
                    "Security Contacts (by Entity Type)",
                )
            )

    if total > 0:
        sirtfi_labels, sirtfi_values, sirtfi_colors = [], [], []
        if total_sps > 0:
            sirtfi_labels.append(
                f"SPs\n{stats.get('sps_has_sirtfi', 0):,}/{total_sps:,}"
            )
            sirtfi_values.append(_pct(stats.get("sps_has_sirtfi", 0), total_sps))
            sirtfi_colors.append(PALETTE["green"])
        if total_idps > 0:
            sirtfi_labels.append(
                f"IdPs\n{stats.get('idps_has_sirtfi', 0):,}/{total_idps:,}"
            )
            sirtfi_values.append(_pct(stats.get("idps_has_sirtfi", 0), total_idps))
            sirtfi_colors.append(PALETTE["orange"])
        if sirtfi_labels and any(v > 0 for v in sirtfi_values):
            charts.append(
                _bar_chart(
                    sirtfi_labels,
                    sirtfi_values,
                    sirtfi_colors,
                    "SIRTFI Coverage (by Entity Type)",
                )
            )

    if total_sps > 0:
        sp_missing_both = stats.get("sps_missing_both", 0)
        sp_has_both = stats.get("sps_has_both", 0)
        sp_partial = (total_sps - sp_missing_both) - sp_has_both
        chart = _pie_chart(
            [sp_has_both, sp_partial, sp_missing_both],
            [
                f"Both ({sp_has_both:,})",
                f"Partial ({sp_partial:,})",
                f"None ({sp_missing_both:,})",
            ],
            [PALETTE["green"], PALETTE["orange"], PALETTE["red"]],
            "SP Compliance (Privacy + Security)",
        )
        if chart is not None:
            charts.append(chart)

    if include_validation and stats.get("urls_checked", 0) > 0:
        urls_checked = stats.get("urls_checked", 0)
        urls_accessible = stats.get("urls_accessible", 0)
        urls_broken = stats.get("urls_broken", 0)
        validation_pct = _pct(urls_accessible, urls_checked)
        chart = _pie_chart(
            [urls_accessible, urls_broken],
            [f"Accessible ({urls_accessible:,})", f"Broken ({urls_broken:,})"],
            [PALETTE["blue"], PALETTE["red"]],
            "Privacy URL Accessibility",
            donut=True,
            center_label=f"{validation_pct:.1f}%",
        )
        if chart is not None:
            charts.append(chart)

        # Error breakdown table (top 5)
        error_breakdown = stats.get("error_breakdown", {})
        if error_breakdown and urls_broken > 0:
            sorted_errors = sorted(
                error_breakdown.items(), key=lambda x: x[1], reverse=True
            )[:5]
            table_data = [["Error Type", "Count", "% of Errors"]]
            for error_type, count in sorted_errors:
                table_data.append(
                    [error_type, f"{count:,}", f"{_pct(count, urls_broken):.1f}%"]
                )
            charts.append(
                _make_styled_table(
                    "Error Breakdown (Top 5)",
                    table_data,
                    [0.50, 0.25, 0.25],
                    PALETTE["blue"],
                )
            )

        # Bot protection provider table
        provider_stats = stats.get("provider_stats", {})
        if provider_stats and provider_stats.get("total_detected", 0) > 0:
            by_provider = provider_stats.get("by_provider", {})
            retry_attempted = provider_stats.get("retry_attempted", 0)
            retry_success = provider_stats.get("retry_success", 0)
            sorted_providers = sorted(
                by_provider.items(), key=lambda x: x[1], reverse=True
            )
            table_data = [["Provider", "Count", "Bypass Rate"]]
            for provider, count in sorted_providers:
                if retry_attempted > 0:
                    bypass_rate = (retry_success / retry_attempted) * 100
                    table_data.append([provider, f"{count:,}", f"{bypass_rate:.1f}%"])
                else:
                    table_data.append([provider, f"{count:,}", "N/A"])
            charts.append(
                _make_styled_table(
                    "Bot Protection Detected",
                    table_data,
                    [0.50, 0.25, 0.25],
                    PALETTE["blue"],
                )
            )

    # Content quality charts
    if include_content_validation and stats.get("content_urls_checked", 0) > 0:
        scores = stats.get("content_quality_scores", [])
        if scores:
            bands = [
                (
                    "Excellent\n90-100",
                    sum(1 for s in scores if s >= 90),
                    PALETTE["green"],
                ),
                (
                    "Good\n70-89",
                    sum(1 for s in scores if 70 <= s < 90),
                    PALETTE["teal"],
                ),
                (
                    "Fair\n50-69",
                    sum(1 for s in scores if 50 <= s < 70),
                    PALETTE["yellow"],
                ),
                (
                    "Poor\n30-49",
                    sum(1 for s in scores if 30 <= s < 50),
                    PALETTE["orange"],
                ),
                ("Broken\n<30", sum(1 for s in scores if s < 30), PALETTE["red"]),
            ]
            band_labels = [b[0] for b in bands]
            band_counts = [b[1] for b in bands]
            band_colors = [b[2] for b in bands]

            fig, ax = plt.subplots(figsize=(3.4, 2.5), dpi=150)
            bars = ax.bar(band_labels, band_counts, color=band_colors, width=0.6)
            ax.set_ylabel("Pages", fontsize=8)
            ax.set_title("Privacy Page Quality Distribution", fontsize=10, pad=8)
            ax.tick_params(axis="x", labelsize=7)
            ax.tick_params(axis="y", labelsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.yaxis.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
            ax.set_axisbelow(True)
            max_count = max(band_counts) if band_counts else 1
            ax.set_ylim(0, max_count * 1.18 + 0.5)
            for bar, count in zip(bars, band_counts, strict=False):
                if count > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        count + max_count * 0.02,
                        str(count),
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )
            fig.tight_layout()
            charts.append(_image_from_figure(fig))

        issues = stats.get("content_quality_issues_breakdown", {})
        if issues:
            content_checked = max(stats.get("content_urls_checked", 1), 1)
            sorted_issues = sorted(issues.items(), key=lambda x: x[1], reverse=True)[:8]
            issue_labels = {
                "soft-404": "Soft 404 (returns 200 but shows error)",
                "no-gdpr-keywords": "No GDPR compliance keywords",
                "few-gdpr-keywords": "Too few GDPR keywords (< 3)",
                "thin-content": "Thin content (< 500 bytes)",
                "empty-content": "Empty content (< 100 bytes)",
                "non-https": "Non-HTTPS URL",
                "slow-response": "Slow response (> 5 s)",
                "very-slow-response": "Very slow response (> 10 s)",
            }
            table_data = [["Issue", "Count", "% of Pages"]]
            for issue_key, count in sorted_issues:
                label = issue_labels.get(issue_key, issue_key)
                table_data.append(
                    [label, f"{count:,}", f"{_pct(count, content_checked):.1f}%"]
                )
            charts.append(
                _make_styled_table(
                    "Content Quality Issues (Top 8)",
                    table_data,
                    [0.55, 0.20, 0.25],
                    PALETTE["green"],
                )
            )

    return charts


def _draw_header(
    c: canvas.Canvas,
    title: str,
    subtitle: str,
    page_number: int,
    total_pages: int,
    page_width: float,
    page_height: float,
) -> float:
    top = page_height - PAGE_MARGIN
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor(PALETTE["gray"]))
    c.drawString(PAGE_MARGIN, top, title)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor(PALETTE["gray"]))
    c.drawString(PAGE_MARGIN, top - 16, subtitle)
    c.setFont("Helvetica", 9)
    c.drawRightString(
        page_width - PAGE_MARGIN, top, f"Page {page_number} of {total_pages}"
    )
    # Separator line below header
    line_y = top - HEADER_HEIGHT + 6
    c.setStrokeColor(colors.HexColor(PALETTE["blue"]))
    c.setLineWidth(0.5)
    c.line(PAGE_MARGIN, line_y, page_width - PAGE_MARGIN, line_y)
    return top - HEADER_HEIGHT


def _draw_kpi_blocks(
    c: canvas.Canvas, kpis: list[tuple[str, str, str]], top: float, page_width: float
) -> float:
    rows = max(1, math.ceil(len(kpis) / KPI_COLS))
    block_w = (page_width - (2 * PAGE_MARGIN) - (KPI_COLS - 1) * KPI_ROW_GAP) / KPI_COLS
    block_h = KPI_ROW_HEIGHT

    for idx, (label, value, accent) in enumerate(kpis):
        row = idx // KPI_COLS
        col = idx % KPI_COLS
        x = PAGE_MARGIN + col * (block_w + KPI_ROW_GAP)
        y_top = top - row * (block_h + KPI_ROW_GAP)
        y = y_top - block_h

        # Background card
        c.setFillColor(colors.HexColor(PALETTE["light_gray"]))
        c.roundRect(x, y, block_w, block_h, 6, fill=1, stroke=0)

        # Left accent stripe (4pt wide colored bar)
        c.setFillColor(colors.HexColor(accent))
        c.rect(x, y, 4, block_h, fill=1, stroke=0)

        # Label
        c.setFillColor(colors.HexColor(PALETTE["gray"]))
        c.setFont("Helvetica", 8)
        c.drawString(x + 10, y + block_h - 12, label)

        # Value
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor(PALETTE["blue"]))
        c.drawString(x + 10, y + 8, value)

    total_height = rows * block_h + (rows - 1) * KPI_ROW_GAP
    return top - total_height


def _draw_chart_grid(
    c: canvas.Canvas,
    charts: list[ChartImage],
    top: float,
    bottom: float,
    page_width: float,
) -> None:
    if not charts:
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor(PALETTE["gray"]))
        c.drawString(PAGE_MARGIN, top - 20, "No chart data available.")
        return

    cols = 2
    rows = math.ceil(len(charts) / cols)
    available_height = max(1, top - bottom)
    chart_w = (page_width - (2 * PAGE_MARGIN) - (cols - 1) * CHART_GAP) / cols
    # Cap slot height to prevent huge empty areas when there are few charts
    chart_h = min(MAX_CHART_SLOT_H, (available_height - (rows - 1) * CHART_GAP) / rows)

    for idx, chart in enumerate(charts):
        row = idx // cols
        col = idx % cols
        # Last chart on an odd total: center it across the full content width
        is_last_odd = (len(charts) % 2 == 1) and (idx == len(charts) - 1)
        content_w = page_width - 2 * PAGE_MARGIN
        if is_last_odd:
            # Draw at chart_w wide, centered on the full content area
            left = PAGE_MARGIN + (content_w - chart_w) / 2
        else:
            left = PAGE_MARGIN + col * (chart_w + CHART_GAP)
        top_y = top - row * (chart_h + CHART_GAP)
        bottom_y = top_y - chart_h
        c.drawImage(
            chart.image,
            left,
            bottom_y,
            width=chart_w,
            height=chart_h,
            preserveAspectRatio=True,
            anchor="n",  # top-align within slot to avoid floating charts
        )


def _draw_footer(
    c: canvas.Canvas,
    generated_at: str,
    page_width: float,
) -> None:
    y = PAGE_MARGIN + 2
    # Separator line above footer text
    c.setStrokeColor(colors.HexColor(PALETTE["light_gray"]))
    c.setLineWidth(0.5)
    c.line(PAGE_MARGIN, y + 12, page_width - PAGE_MARGIN, y + 12)
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor(PALETTE["gray"]))
    c.drawString(PAGE_MARGIN, y, f"Generated: {generated_at}")
    c.drawRightString(page_width - PAGE_MARGIN, y, "eduGAIN Quality Analysis")


def _render_page(
    c: canvas.Canvas,
    title: str,
    subtitle: str,
    stats: dict,
    include_validation: bool,
    page_number: int,
    total_pages: int,
    generated_at: str,
    include_content_validation: bool = False,
) -> None:
    page_width, page_height = A4

    kpis = _build_kpis(stats, include_content_validation)
    charts = _build_charts(stats, include_validation, include_content_validation)

    content_top = _draw_header(
        c, title, subtitle, page_number, total_pages, page_width, page_height
    )
    kpi_bottom = _draw_kpi_blocks(c, kpis, content_top, page_width)
    charts_top = kpi_bottom - 16
    charts_bottom = PAGE_MARGIN + FOOTER_HEIGHT

    _draw_chart_grid(c, charts, charts_top, charts_bottom, page_width)
    _draw_footer(c, generated_at, page_width)

    for chart in charts:
        chart.buffer.close()


def generate_pdf_report(
    stats: dict,
    federation_stats: dict,
    output_path: str,
    report_context: str,
    include_validation: bool,
    include_content_validation: bool = False,
) -> str:
    """Generate a multi-page graphical PDF report."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    sorted_federations = sorted(
        federation_stats.items(), key=lambda x: x[1]["total_entities"], reverse=True
    )
    total_pages = 1 + len(sorted_federations) if sorted_federations else 1
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    c = canvas.Canvas(str(output), pagesize=A4)

    summary_subtitle = f"{report_context} | Federations: {len(sorted_federations)}"
    _render_page(
        c,
        "eduGAIN Quality Analysis Report",
        summary_subtitle,
        stats,
        include_validation,
        1,
        total_pages,
        generated_at,
        include_content_validation=include_content_validation,
    )
    if sorted_federations:
        c.showPage()

    for idx, (federation_name, fed_stats) in enumerate(sorted_federations, start=2):
        total = fed_stats.get("total_entities", 0)
        total_sps = fed_stats.get("total_sps", 0)
        total_idps = fed_stats.get("total_idps", 0)
        subtitle = f"{total:,} entities (SPs: {total_sps:,}, IdPs: {total_idps:,})"
        _render_page(
            c,
            f"Federation: {federation_name}",
            subtitle,
            fed_stats,
            include_validation,
            idx,
            total_pages,
            generated_at,
        )
        if idx < total_pages:
            c.showPage()

    c.save()
    return str(output)
