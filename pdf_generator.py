"""
PetroNexa Document Engine - PDF Generation Module
"""
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ReportGenerator:
    @staticmethod
    def generate_hydraulics_report(data: dict) -> bytes:
        """Generates a structured PDF report in memory for hydraulics and cementing runs."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1E3A8A"),
            spaceAfter=12
        )
        body_style = styles['Normal']

        elements = []

        # Document Header
        elements.append(Paragraph("<b>PETRONEXA ENGINEERING REPORT</b>", title_style))
        elements.append(Paragraph("<b>Module:</b> Drilling Hydraulics & Cementing Analysis", body_style))
        elements.append(Spacer(1, 12))

        # Output Summary Data Table
        table_data = [
            [Paragraph("<b>Parameter</b>", body_style), Paragraph("<b>Value</b>", body_style)]
        ]
        
        for key, value in data.items():
            formatted_key = str(key).replace("_", " ").title()
            table_data.append([Paragraph(formatted_key, body_style), Paragraph(str(value), body_style)])

        summary_table = Table(table_data, colWidths=[250, 250])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#111827")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(summary_table)

        # Build Document
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
