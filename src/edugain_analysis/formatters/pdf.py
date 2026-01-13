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

PALETTE = {
    "blue": "#1E5AA8",
    "green": "#2E7D32",
    "orange": "#EF6C00",
    "red": "#C62828",
    "teal": "#00897B",
    "gray": "#455A64",
    "light_gray": "#F4F5F6",
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
    fig, ax = plt.subplots(figsize=(3.4, 2.5), dpi=150)
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
                fontsize=9,
                fontweight="bold",
            )

    if labels:
        ax.legend(
            wedges,
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.15),
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
    bars = ax.bar(labels, values, color=colors_list)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percent", fontsize=8)
    ax.set_title(title, fontsize=10, pad=8)
    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", labelsize=8)

    for bar, value in zip(bars, values, strict=False):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 1,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.tight_layout()
    return _image_from_figure(fig)


def _build_kpis(stats: dict) -> list[tuple[str, str]]:
    total = stats.get("total_entities", 0)
    total_sps = stats.get("total_sps", 0)
    total_idps = stats.get("total_idps", 0)

    privacy_pct = _pct(stats.get("sps_has_privacy", 0), total_sps)
    security_pct = _pct(stats.get("total_has_security", 0), total)
    sirtfi_pct = _pct(stats.get("total_has_sirtfi", 0), total)

    return [
        ("Total Entities", f"{total:,}"),
        ("Service Providers", f"{total_sps:,}"),
        ("Identity Providers", f"{total_idps:,}"),
        (
            "Privacy Coverage (SPs)",
            "N/A"
            if total_sps == 0
            else f"{stats.get('sps_has_privacy', 0):,}/{total_sps:,} ({privacy_pct:.1f}%)",
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


def _build_charts(stats: dict, include_validation: bool) -> list[ChartImage]:
    charts: list[ChartImage] = []
    total = stats.get("total_entities", 0)
    total_sps = stats.get("total_sps", 0)
    total_idps = stats.get("total_idps", 0)

    if total_sps > 0:
        with_privacy = stats.get("sps_has_privacy", 0)
        missing_privacy = stats.get("sps_missing_privacy", 0)
        privacy_pct = _pct(with_privacy, total_sps)
        charts.append(
            _pie_chart(
                [with_privacy, missing_privacy],
                [
                    f"With ({with_privacy:,})",
                    f"Missing ({missing_privacy:,})",
                ],
                [PALETTE["green"], PALETTE["red"]],
                "Privacy Statements (SPs)",
                donut=True,
                center_label=f"{privacy_pct:.1f}%",
            )
        )

    if total > 0:
        labels = []
        values = []
        colors_list = []

        if total_sps > 0:
            sp_security_pct = _pct(stats.get("sps_has_security", 0), total_sps)
            labels.append(f"SPs\n{stats.get('sps_has_security', 0):,}/{total_sps:,}")
            values.append(sp_security_pct)
            colors_list.append(PALETTE["blue"])

        if total_idps > 0:
            idp_security_pct = _pct(stats.get("idps_has_security", 0), total_idps)
            labels.append(f"IdPs\n{stats.get('idps_has_security', 0):,}/{total_idps:,}")
            values.append(idp_security_pct)
            colors_list.append(PALETTE["teal"])

        if labels:
            charts.append(
                _bar_chart(
                    labels,
                    values,
                    colors_list,
                    "Security Contacts (by Entity Type)",
                )
            )

    if total > 0:
        labels = []
        values = []
        colors_list = []

        if total_sps > 0:
            sp_sirtfi_pct = _pct(stats.get("sps_has_sirtfi", 0), total_sps)
            labels.append(f"SPs\n{stats.get('sps_has_sirtfi', 0):,}/{total_sps:,}")
            values.append(sp_sirtfi_pct)
            colors_list.append(PALETTE["green"])

        if total_idps > 0:
            idp_sirtfi_pct = _pct(stats.get("idps_has_sirtfi", 0), total_idps)
            labels.append(f"IdPs\n{stats.get('idps_has_sirtfi', 0):,}/{total_idps:,}")
            values.append(idp_sirtfi_pct)
            colors_list.append(PALETTE["orange"])

        if labels:
            charts.append(
                _bar_chart(
                    labels,
                    values,
                    colors_list,
                    "SIRTFI Coverage (by Entity Type)",
                )
            )

    if total_sps > 0:
        sp_missing_both = stats.get("sps_missing_both", 0)
        sp_has_both = stats.get("sps_has_both", 0)
        sp_has_at_least_one = total_sps - sp_missing_both
        sp_partial = sp_has_at_least_one - sp_has_both
        charts.append(
            _pie_chart(
                [sp_has_both, sp_partial, sp_missing_both],
                [
                    f"Both ({sp_has_both:,})",
                    f"Partial ({sp_partial:,})",
                    f"None ({sp_missing_both:,})",
                ],
                [PALETTE["green"], PALETTE["orange"], PALETTE["red"]],
                "SP Compliance (Privacy + Security)",
            )
        )

    if include_validation and stats.get("urls_checked", 0) > 0:
        urls_checked = stats.get("urls_checked", 0)
        urls_accessible = stats.get("urls_accessible", 0)
        urls_broken = stats.get("urls_broken", 0)
        validation_pct = _pct(urls_accessible, urls_checked)
        charts.append(
            _pie_chart(
                [urls_accessible, urls_broken],
                [
                    f"Accessible ({urls_accessible:,})",
                    f"Broken ({urls_broken:,})",
                ],
                [PALETTE["blue"], PALETTE["red"]],
                "Privacy URL Accessibility",
                donut=True,
                center_label=f"{validation_pct:.1f}%",
            )
        )

        # Add error breakdown chart if there are broken URLs
        error_breakdown = stats.get("error_breakdown", {})
        if error_breakdown and urls_broken > 0:
            # Sort by count (descending) and take top 8 error types
            sorted_errors = sorted(
                error_breakdown.items(), key=lambda x: x[1], reverse=True
            )[:8]

            error_labels = []
            error_values = []
            error_colors = []

            # Color mapping for different error types
            color_map = {
                "Cloudflare": PALETTE["purple"],
                "AWS WAF": PALETTE["orange"],
                "Akamai": PALETTE["teal"],
                "Not Found": PALETTE["red"],
                "SSL Certificate": PALETTE["yellow"],
                "Connection": PALETTE["gray"],
                "Timeout": PALETTE["purple"],
            }

            for error_type, count in sorted_errors:
                error_labels.append(f"{error_type}\n({count:,})")
                error_pct = _pct(count, urls_broken)
                error_values.append(error_pct)

                # Choose color based on error type keywords
                color = PALETTE["gray"]  # default
                for keyword, col in color_map.items():
                    if keyword.lower() in error_type.lower():
                        color = col
                        break
                error_colors.append(color)

            if error_labels:
                charts.append(
                    _bar_chart(
                        error_labels,
                        error_values,
                        error_colors,
                        "Error Breakdown (Top 8)",
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
    return top - HEADER_HEIGHT


def _draw_kpi_blocks(
    c: canvas.Canvas, kpis: list[tuple[str, str]], top: float, page_width: float
) -> float:
    rows = max(1, math.ceil(len(kpis) / KPI_COLS))
    block_w = (page_width - (2 * PAGE_MARGIN) - (KPI_COLS - 1) * KPI_ROW_GAP) / KPI_COLS
    block_h = KPI_ROW_HEIGHT

    for idx, (label, value) in enumerate(kpis):
        row = idx // KPI_COLS
        col = idx % KPI_COLS
        x = PAGE_MARGIN + col * (block_w + KPI_ROW_GAP)
        y_top = top - row * (block_h + KPI_ROW_GAP)
        y = y_top - block_h

        c.setFillColor(colors.HexColor(PALETTE["light_gray"]))
        c.roundRect(x, y, block_w, block_h, 6, fill=1, stroke=0)

        c.setFillColor(colors.HexColor(PALETTE["gray"]))
        c.setFont("Helvetica", 8)
        c.drawString(x + 8, y + block_h - 12, label)

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor(PALETTE["blue"]))
        c.drawString(x + 8, y + 10, value)

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
    chart_h = (available_height - (rows - 1) * CHART_GAP) / rows

    for idx, chart in enumerate(charts):
        row = idx // cols
        col = idx % cols
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
            anchor="c",
        )


def _draw_footer(
    c: canvas.Canvas,
    generated_at: str,
    page_width: float,
) -> None:
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor(PALETTE["gray"]))
    c.drawString(PAGE_MARGIN, PAGE_MARGIN - 6, f"Generated: {generated_at}")
    c.drawRightString(
        page_width - PAGE_MARGIN, PAGE_MARGIN - 6, "eduGAIN Quality Analysis"
    )


def _render_page(
    c: canvas.Canvas,
    title: str,
    subtitle: str,
    stats: dict,
    include_validation: bool,
    page_number: int,
    total_pages: int,
    generated_at: str,
) -> None:
    page_width, page_height = A4

    kpis = _build_kpis(stats)
    charts = _build_charts(stats, include_validation)

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
