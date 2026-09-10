"""
PDF Report Generation module for PetroNexa wellbore telemetry & physics.
"""
import io
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_hydraulics_pdf_report(results: Dict[str, Any]) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=12
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=12,
        spaceAfter=8
    )
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14)

    story = []

    # Title Section
    story.append(Paragraph("PetroNexa Engineering Report", title_style))
    story.append(Paragraph("Drilling Hydraulics & ECD Summary", section_style))
    story.append(Spacer(1, 10))

    # Summary Metrics Table
    summary_data = [
        ["Parameter", "Value", "Unit"],
        ["Rheology Model", str(results.get("rheology_model_used")), "-"],
        ["Flow Rate", f"{results.get('flow_rate_gpm', 0.0):.1f}", "GPM"],
        ["Total Depth (MD)", f"{results.get('total_depth_ft', 0.0):.1f}", "ft"],
        ["True Vertical Depth (TVD)", f"{results.get('true_vertical_depth_ft', 0.0):.1f}", "ft"],
        ["Mud Weight", f"{results.get('surface_mud_weight_ppg', 0.0):.2f}", "ppg"],
        ["Bottomhole ECD", f"{results.get('equivalent_circulating_density_ecd_ppg', 0.0):.3f}", "ppg"],
        ["Standpipe Pressure (SPP)", f"{results.get('standpipe_pressure_spp_psi', 0.0):.1f}", "psi"],
    ]

    t_summary = Table(summary_data, colWidths=[200, 150, 100])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 15))

    # Segment Breakdown Table
    story.append(Paragraph("Wellbore Segment Hydraulics", section_style))
    segment_data = [["Seg #", "Length (ft)", "TVD (ft)", "Ann. Vel (fpm)", "Ann. Loss (psi)", "ECD (ppg)"]]
    for seg in results.get("segment_breakdown", []):
        segment_data.append([
            str(seg.get("segment_index")),
            f"{seg.get('length_ft', 0.0):.1f}",
            f"{seg.get('tvd_length_ft', 0.0):.1f}",
            f"{seg.get('annular_velocity_fpm', 0.0):.1f}",
            f"{seg.get('annular_loss_psi', 0.0):.1f}",
            f"{seg.get('local_ecd_ppg', 0.0):.3f}",
        ])

    t_seg = Table(segment_data, colWidths=[40, 80, 80, 100, 100, 80])
    t_seg.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#475569')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(t_seg)

    doc.build(story)
    buffer.seek(0)
    return buffer
