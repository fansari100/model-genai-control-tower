"""
PDF generator for certification packs and committee reports.

Uses ReportLab to produce audit-grade PDF documents.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_certification_pack_pdf(
    pack_data: dict[str, Any],
) -> bytes:
    """
    Generate a professional certification pack PDF.

    Args:
        pack_data: The certification pack data from the API.

    Returns:
        PDF content as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()
    elements: list = []

    # Custom styles
    title_style = ParagraphStyle(
        "CertTitle",
        parent=styles["Title"],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor("#1a1a2e"),
    )
    heading_style = ParagraphStyle(
        "CertHeading",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor("#16213e"),
    )
    sub_heading_style = ParagraphStyle(
        "CertSubHeading",
        parent=styles["Heading2"],
        fontSize=13,
        spaceAfter=8,
        textColor=colors.HexColor("#0f3460"),
    )
    body_style = ParagraphStyle(
        "CertBody",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=6,
        leading=14,
    )

    # ── Title Page ────────────────────────────────────────────
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph("Control Tower", title_style))
    elements.append(Paragraph("Certification Evidence Pack", heading_style))
    elements.append(Spacer(1, 0.5 * inch))

    use_case_name = pack_data.get("use_case_name", "Unknown Use Case")
    elements.append(Paragraph(f"<b>Use Case:</b> {use_case_name}", body_style))
    elements.append(Paragraph(f"<b>Pack ID:</b> {pack_data.get('pack_id', 'N/A')}", body_style))
    elements.append(
        Paragraph(
            f"<b>Generated:</b> {pack_data.get('generated_at', datetime.now(UTC).isoformat())}",
            body_style,
        )
    )
    elements.append(
        Paragraph(
            f"<b>Risk Rating:</b> {pack_data.get('risk_rating', 'N/A')}",
            body_style,
        )
    )
    elements.append(
        Paragraph(
            f"<b>Overall Status:</b> {pack_data.get('overall_status', 'N/A')}",
            body_style,
        )
    )
    elements.append(PageBreak())

    # ── Table of Contents ─────────────────────────────────────
    elements.append(Paragraph("Table of Contents", heading_style))
    sections = pack_data.get("sections", [])
    for i, section in enumerate(sections, 1):
        elements.append(Paragraph(f"{i}. {section.get('title', 'Section')}", body_style))
    elements.append(PageBreak())

    # ── Sections ──────────────────────────────────────────────
    for section in sections:
        elements.append(Paragraph(section.get("title", "Section"), heading_style))

        content = section.get("content", {})
        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, dict):
                    elements.append(Paragraph(f"<b>{_humanize(key)}</b>", sub_heading_style))
                    for k2, v2 in value.items():
                        elements.append(
                            Paragraph(f"  {_humanize(k2)}: {_format_value(v2)}", body_style)
                        )
                elif isinstance(value, list):
                    elements.append(Paragraph(f"<b>{_humanize(key)}</b>", sub_heading_style))
                    if value and isinstance(value[0], dict):
                        # Render as table
                        table = _dict_list_to_table(value)
                        if table:
                            elements.append(table)
                    else:
                        for item in value:
                            elements.append(Paragraph(f"  • {item}", body_style))
                else:
                    elements.append(
                        Paragraph(f"<b>{_humanize(key)}:</b> {_format_value(value)}", body_style)
                    )

        elements.append(Spacer(1, 0.3 * inch))

    # ── Summary Footer ────────────────────────────────────────
    elements.append(PageBreak())
    elements.append(Paragraph("Certification Summary", heading_style))
    summary = pack_data.get("summary", {})
    for key, value in summary.items():
        elements.append(Paragraph(f"<b>{_humanize(key)}:</b> {_format_value(value)}", body_style))

    elements.append(Spacer(1, inch))
    elements.append(
        Paragraph(
            "<i>This document was auto-generated by Control Tower Certification Engine v1.0. "
            "All evidence artifacts are content-addressed (SHA-256) and stored in the "
            "immutable evidence registry.</i>",
            body_style,
        )
    )

    doc.build(elements)
    return buffer.getvalue()


def _humanize(key: str) -> str:
    """Convert snake_case to human-readable."""
    return key.replace("_", " ").title()


def _format_value(value: Any) -> str:
    """Format a value for display."""
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _dict_list_to_table(items: list[dict]) -> Table | None:
    """Convert a list of dicts into a ReportLab Table."""
    if not items:
        return None

    headers = list(items[0].keys())
    data = [headers]
    for item in items[:20]:  # Limit rows
        data.append([_format_value(item.get(h, "")) for h in headers])

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f5f5")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
            ]
        )
    )
    return table
