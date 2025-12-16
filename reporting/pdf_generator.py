"""
PDF Report Generator Module
Creates professional KYC/AML assessment reports using ReportLab.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from datetime import datetime
import os


def generate_pdf(report_data: dict, output_path: str) -> str:
    """
    Generate a professional KYC/AML assessment PDF report.

    Args:
        report_data: Dictionary containing all report information
            - client_data: Client information dict
            - risk_result: Risk assessment results
            - documents: List of submitted documents
            - sow_category: Source of wealth category
            - timestamp: Report generation timestamp

        output_path: Path where PDF should be saved

    Returns:
        Path to the generated PDF file
    """

    # Create the PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define custom styles
    styles = getSampleStyleSheet()

    # Custom title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Custom heading style
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    # Normal text style
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 14

    # Extract data
    client = report_data.get('client_data', {})
    risk = report_data.get('risk_result', {})
    documents = report_data.get('documents', {})
    sow_category = report_data.get('sow_category', 'Not Detected')
    timestamp = report_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # ===== HEADER =====
    title = Paragraph("KYC/AML ASSESSMENT REPORT", title_style)
    elements.append(title)

    # Report metadata
    report_info = f"<b>Report Generated:</b> {timestamp}<br/><b>Report ID:</b> {client.get('id', 'N/A')}"
    elements.append(Paragraph(report_info, normal_style))
    elements.append(Spacer(1, 20))

    # ===== CLIENT INFORMATION =====
    elements.append(Paragraph("Client Information", heading_style))

    client_data_table = [
        ['Full Name:', client.get('name', 'N/A')],
        ['Date of Birth:', str(client.get('dob', 'N/A'))],
        ['Nationality:', client.get('nationality', 'N/A')],
        ['Address:', client.get('address', 'N/A')],
        ['Email:', client.get('email', 'N/A')],
        ['Occupation:', client.get('occupation', 'N/A')],
        ['Transaction Amount:', f"${client.get('amount', 0):,.2f}"],
        ['Purpose:', client.get('purpose', 'N/A')],
    ]

    client_table = Table(client_data_table, colWidths=[2*inch, 4.5*inch])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F4F8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 20))

    # ===== DOCUMENT SUMMARY =====
    elements.append(Paragraph("Document Summary", heading_style))

    doc_labels = {
        'id_doc': 'ID Document',
        'selfie': 'Selfie Photo',
        'proof_address': 'Proof of Address',
        'sow_doc': 'Source of Wealth Document'
    }

    doc_data_table = [['Document Type', 'Status']]
    for doc_key, doc_label in doc_labels.items():
        status = '✓ Submitted' if documents.get(doc_key) else '✗ Missing'
        doc_data_table.append([doc_label, status])

    doc_table = Table(doc_data_table, colWidths=[3.5*inch, 3*inch])
    doc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(doc_table)
    elements.append(Spacer(1, 20))

    # ===== RISK ASSESSMENT =====
    elements.append(Paragraph("Risk Assessment", heading_style))

    risk_score = risk.get('score', 0)
    risk_band = risk.get('band', 'Unknown')

    # Determine risk band color
    risk_colors = {
        'Low': colors.HexColor('#28a745'),
        'Medium': colors.HexColor('#ffc107'),
        'High': colors.HexColor('#dc3545')
    }
    risk_color = risk_colors.get(risk_band, colors.grey)

    risk_summary_table = [
        ['Risk Score:', f"{risk_score} / 100"],
        ['Risk Band:', risk_band],
        ['Source of Wealth Category:', sow_category],
    ]

    risk_table = Table(risk_summary_table, colWidths=[2.5*inch, 4*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F4F8')),
        ('BACKGROUND', (1, 1), (1, 1), risk_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(risk_table)
    elements.append(Spacer(1, 20))

    # ===== TRIGGERED FLAGS =====
    elements.append(Paragraph("Triggered Risk Flags", heading_style))

    reasons = risk.get('reasons', [])
    if reasons:
        flag_data = [['Rule', 'Points', 'Description']]
        for reason in reasons:
            flag_data.append([
                reason.get('rule', ''),
                str(reason.get('points', 0)),
                reason.get('description', '')
            ])

        flag_table = Table(flag_data, colWidths=[1.8*inch, 0.8*inch, 4*inch])
        flag_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(flag_table)
    else:
        elements.append(Paragraph("No risk flags triggered.", normal_style))

    elements.append(Spacer(1, 20))

    # ===== RECOMMENDED ACTION =====
    elements.append(Paragraph("Recommended Action", heading_style))

    from risk_engine import get_recommended_action
    action = get_recommended_action(risk_band)

    action_para = Paragraph(f"<b>{action}</b>", normal_style)
    elements.append(action_para)
    elements.append(Spacer(1, 20))

    # ===== SOURCE OF WEALTH DETAILS =====
    if client.get('source_of_wealth'):
        elements.append(Paragraph("Source of Wealth Details", heading_style))
        sow_text = client.get('source_of_wealth', 'Not provided')
        # Truncate if too long
        if len(sow_text) > 500:
            sow_text = sow_text[:500] + "..."
        sow_para = Paragraph(sow_text, normal_style)
        elements.append(sow_para)
        elements.append(Spacer(1, 20))

    # ===== DISCLAIMER =====
    elements.append(Spacer(1, 30))
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_JUSTIFY
    )

    disclaimer_text = """
    <b>DISCLAIMER:</b> This report is generated automatically based on the information provided and
    reference data available at the time of assessment. This is a demonstration system using mock
    PEP/sanctions and adverse media lists. The risk assessment is for illustrative purposes only
    and should not be used for actual compliance decisions. All decisions should be made by
    qualified compliance officers following appropriate due diligence procedures and regulatory
    requirements. The information in this report is confidential and should be handled in
    accordance with data protection regulations.
    """
    elements.append(Paragraph(disclaimer_text, disclaimer_style))

    # ===== BUILD PDF =====
    doc.build(elements)

    return output_path
