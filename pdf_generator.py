"""
PetroNexa PDF Engine: Dynamic Engineering Technical Report Generator.
Converts hydraulics data and safety diagnostics into executable PDF documents.
"""

import io
from datetime import datetime, timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)


def _generate_ecd_profile_chart(results: dict, diagnostics: dict) -> io.BytesIO:
    """Renders a dynamic vertical pressure-window profile chart in memory."""
    td = results.get("total_depth_ft", 10000.0)
    mw = results.get("surface_mud_weight_ppg", 12.5)
    ecd = results.get("ecd_ppg", 13.0)

    pore_lim = diagnostics.get("pore_limit", 9.0)
    frac_lim = diagnostics.get("frac_limit", 15.0)

    depths = [0, td * 0.25, td * 0.5, td * 0.75, td]
    pore_curve = [pore_lim] * len(depths)
    frac_curve = [frac_lim] * len(depths)
    static_mw_curve = [mw] * len(depths)
    
    # Linear friction growth representation along wellbore depth
    ecd_curve = [mw + ((ecd - mw) * (d / td)) for d in depths]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(pore_curve, depths, label=f"Pore Limit ({pore_lim:.2f} ppg)", color="#d97706", linestyle="--", linewidth=1.5)
    ax.plot(frac_curve, depths, label=f"Frac Limit ({frac_lim:.2f} ppg)", color="#dc2626", linestyle="--", linewidth=1.5)
    ax.plot(static_mw_curve, depths, label=f"Static MW ({mw:.2f} ppg)", color="#2563eb", linestyle=":", linewidth=1.5)
    ax.plot(ecd_curve, depths, label=f"Dynamic ECD ({ecd:.2f} ppg)", color="#059669", linewidth=2.5)

    ax.set_ylabel("Measured Depth (ft)", fontsize=9, fontweight="bold")
    ax.set_xlabel("Equivalent Density (ppg)", fontsize=9, fontweight="bold")
    ax.invert_yaxis()
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower left", fontsize=8)
    ax.set_title("Dynamic Pressure Window Profile", fontsize=10, fontweight="bold", pad=10)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_pdf_payload(
    project_meta: dict,
    physics_results: dict,
    diagnostic_results: dict,
    engineer_name: str = "Engineer",
    cementing_results: dict = None,
) -> io.BytesIO:
    """Generates an enterprise-grade engineering PDF report payload."""
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e3a8a"),
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=10,
        spaceAfter=4,
    )
    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("PetroNexa Technical Engineering Report", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=10))

    meta_table_data = [
        [
            Paragraph(f"<b>Well / Project:</b> {project_meta.get('name', 'N/A')}", normal_style),
            Paragraph(f"<b>Rig:</b> {project_meta.get('rig_name', 'N/A')}", normal_style),
        ],
        [
            Paragraph(f"<b>Engineer:</b> {engineer_name}", normal_style),
            Paragraph(f"<b>Date:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", normal_style),
        ],
    ]
    meta_table = Table(meta_table_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Diagnostic Safety Matrix
    story.append(Paragraph("Hydraulic Safety & Operational Diagnostics", section_style))
    
    sev = diagnostic_results.get("severity", "GREEN")
    status_color = colors.HexColor("#16a34a") if sev == "GREEN" else (colors.HexColor("#ca8a04") if sev == "YELLOW" else colors.HexColor("#dc2626"))
    
    limit_basis = diagnostic_results.get("gradient_source", "Configured Limit")
    if diagnostic_results.get("is_fallback", False):
        limit_basis = f"{limit_basis} [UNVERIFIED SCREENING ONLY]"

    diag_data = [
        [Paragraph("<b>Status Severity:</b>", normal_style), Paragraph(f"<font color='{status_color.hexval()}'><b>{sev}</b></font>", normal_style)],
        [Paragraph("<b>Hazard Evaluation:</b>", normal_style), Paragraph(diagnostic_results.get("matched_hazard", "None"), normal_style)],
        [Paragraph("<b>Pressure Window Basis:</b>", normal_style), Paragraph(limit_basis, normal_style)],
        [Paragraph("<b>Detailed Diagnosis:</b>", normal_style), Paragraph(diagnostic_results.get("detailed_diagnosis", "Nominal profile."), normal_style)],
    ]
    diag_table = Table(diag_data, colWidths=[140, 400])
    diag_table.setStyle(TableStyle([
        ("PADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 10))

    # Hydraulics Summary & Chart Layout
    story.append(Paragraph("Hydraulic Performance Breakdown", section_style))
    hyd_summary_data = [
        ["Total Depth (MD)", f"{physics_results.get('total_depth_ft', 0):,.0f} ft", "Surface Mud Weight", f"{physics_results.get('surface_mud_weight_ppg', 0):.2f} ppg"],
        ["Equivalent Circulating Density", f"{physics_results.get('ecd_ppg', 0):.2f} ppg", "Hydrostatic Pressure", f"{physics_results.get('hydrostatic_pressure_psi', 0):,.1f} psi"],
        ["Annular Friction Loss", f"{physics_results.get('total_annular_dp_psi', 0):,.1f} psi", "Bottom Hole Pressure", f"{physics_results.get('bottom_hole_pressure_psi', 0):,.1f} psi"],
    ]
    hyd_table = Table(hyd_summary_data, colWidths=[140, 130, 140, 130])
    hyd_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f8fafc")),
    ]))
    
    chart_buf = _generate_ecd_profile_chart(physics_results, diagnostic_results)
    chart_img = Image(chart_buf, width=240, height=160)

    side_by_side = Table([[hyd_table, chart_img]], colWidths=[300, 240])
    side_by_side.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(side_by_side)
    story.append(Spacer(1, 10))

    # Segment Breakdown Table
    story.append(Paragraph("Wellbore Geometry & Velocity Distribution", section_style))
    seg_headers = ["Segment Name", "Top (ft)", "Bottom (ft)", "Annular Vel (ft/min)", "Annular dP (psi)"]
    seg_rows = [seg_headers]
    for seg in physics_results.get("segment_breakdown", []):
        seg_rows.append([
            seg.get("segment_name", ""),
            f"{seg.get('top_depth_ft', 0):,.0f}",
            f"{seg.get('bottom_depth_ft', 0):,.0f}",
            f"{seg.get('annular_velocity_ft_min', 0):.1f}",
            f"{seg.get('annular_dp_psi', 0):.1f}",
        ])
    seg_table = Table(seg_rows, colWidths=[160, 80, 80, 110, 110])
    seg_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(seg_table)

    # Optional Cementing Section
    if cementing_results:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Primary Cementing Operations Summary", section_style))
        cem_data = [
            ["Lead Slurry Volume", f"{cementing_results.get('lead_slurry_volume_bbl', 0):.2f} bbl", "Tail Slurry Volume", f"{cementing_results.get('tail_slurry_volume_bbl', 0):.2f} bbl"],
            ["Spacer Volume", f"{cementing_results.get('spacer_volume_bbl', 0):.2f} bbl", "Displacement Volume", f"{cementing_results.get('displacement_volume_bbl', 0):.2f} bbl"],
            ["Bumping Pressure", f"{cementing_results.get('recommended_plug_bumping_pressure_psi', 0):,.1f} psi", "Status", "DESIGN COMPLETE"],
        ]
        cem_table = Table(cem_data, colWidths=[140, 130, 140, 130])
        cem_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f8fafc")),
        ]))
        story.append(cem_table)

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer
