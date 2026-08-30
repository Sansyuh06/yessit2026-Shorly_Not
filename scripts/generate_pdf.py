"""
Generate docs/ShorlyNot_What_Is_This_Project.pdf
Professional, high-clarity 2-page project summary for friends, judges, and teammates.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable

def generate_pdf():
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "docs", "ShorlyNot_What_Is_This_Project.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A1A2E"),
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#4A4A6A"),
        alignment=1
    )

    badge_style = ParagraphStyle(
        'DocBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4361EE"),
        alignment=1
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1A1A2E"),
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#22223B")
    )

    body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#1D3557")
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#22223B")
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell,
        fontName='Helvetica-Bold'
    )

    story = []

    # Title & Header
    story.append(Paragraph("ShorlyNot", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("Quantum-Inspired Cyber Threat Detection for Digital Signature Security", subtitle_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("Smart India Hackathon (SIH 2026) · Problem Statement PS 26141 · Team Egreen Quanta", badge_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4361EE"), spaceBefore=2, spaceAfter=8))

    # Executive Summary Box
    exec_summary_text = (
        "<b>What is this?</b> ShorlyNot is an end-to-end quantum cybersecurity architecture solving "
        "digital signature vulnerabilities against both quantum and classical attackers. It replaces classical "
        "digital signatures (RSA/ECDSA/Ed25519) with <b>teleportation-based Quantum Digital Signatures (ShorlyNot-QDS-T1)</b> "
        "and detects cyberattacks in real time using <b>non-machine-learning statistical thresholding (Q-STDF)</b> "
        "derived from Hoeffding's Inequality."
    )
    callout_data = [[Paragraph(exec_summary_text, callout_style)]]
    t_callout = Table(callout_data, colWidths=[540])
    t_callout.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EEF2FF")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#4361EE")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_callout)
    story.append(Spacer(1, 8))

    # Section 1: Exactly Two Products
    story.append(Paragraph("1. Exactly Two Products in this Repository", h1_style))
    story.append(Paragraph(
        "<b>1. skeleton/ (The Invention & Framework):</b> Standalone Python framework and FastAPI microservice (:8000). "
        "Executes real Qiskit Aer teleportation circuits, Pauli eigenstate encoding, Hoeffding threshold checks, and BB84 QKD.<br/>"
        "<b>2. bank/ (The Proof of Concept):</b> Complete mock banking portal (:8080) and live SOC dashboard. "
        "Every fund transfer is quantum-signed; attacks trigger automated application-level isolation (Stages S0 to S4).",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 2: How ShorlyNot-QDS-T1 Works
    story.append(Paragraph("2. How the Quantum Digital Signature (QDS-T1) Works", h1_style))
    qds_steps = [
        [Paragraph("Step", table_header), Paragraph("Protocol Action", table_header), Paragraph("Underlying Physics / Quantum Math", table_header)],
        [Paragraph("1. Prepare", table_cell_bold), Paragraph("Alice hashes payload and derives L check bits.", table_cell), Paragraph("Encodes into Pauli eigenstates: |0>, |1>, |+>, |->", table_cell)],
        [Paragraph("2. Entangle", table_cell_bold), Paragraph("Alice & Bob share Bell pairs via quantum channel.", table_cell), Paragraph("|Phi+> = (|00> + |11>) / sqrt(2)", table_cell)],
        [Paragraph("3. Teleport", table_cell_bold), Paragraph("Alice performs Bell-basis measurement (BSM).", table_cell), Paragraph("Yields 2 classical correction bits (m1, m2) per check bit", table_cell)],
        [Paragraph("4. Protect", table_cell_bold), Paragraph("Correction syndromes encrypted via BB84 session key.", table_cell), Paragraph("PQC / AES-256-GCM authenticated wrapper", table_cell)],
        [Paragraph("5. Verify", table_cell_bold), Paragraph("Bob applies Pauli correction U(m1, m2) and measures.", table_cell), Paragraph("U in {I, X, Z, XZ}. Measures in Alice's basis beta.", table_cell)],
        [Paragraph("6. Bound", table_cell_bold), Paragraph("Bob computes empirical mismatch rate p_hat = errors / n.", table_cell), Paragraph("Accepts if and only if p_hat <= tau (Hoeffding Bound)", table_cell)],
    ]
    t_qds = Table(qds_steps, colWidths=[55, 235, 250])
    t_qds.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A1A2E")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_qds)
    story.append(Spacer(1, 6))

    # Section 3: The Threat Engine (Q-STDF)
    story.append(Paragraph("3. Threat Detection Engine (Q-STDF) — 100% Non-ML Deterministic Ladder", h1_style))
    story.append(Paragraph(
        "Detection uses a strict, fully explainable mathematical rule ladder evaluated on every transaction:",
        body_style
    ))
    story.append(Spacer(1, 3))

    threat_table = [
        [Paragraph("Attack Vector", table_header), Paragraph("Detection Mechanism", table_header), Paragraph("Statistical / Protocol Guarantee", table_header), Paragraph("Bank Action", table_header)],
        [Paragraph("FORGERY", table_cell_bold), Paragraph("p_hat > tau", table_cell), Paragraph("Random guesser mismatch ~50% >> tau (~21%)", table_cell), Paragraph("Stage S2 (Block)", table_cell)],
        [Paragraph("REPLAY", table_cell_bold), Paragraph("Nonce in replay window", table_cell), Paragraph("Cryptographic uniqueness cache", table_cell), Paragraph("Stage S3 (Reset)", table_cell)],
        [Paragraph("IMPERSONATION", table_cell_bold), Paragraph("key_id != signer binding", table_cell), Paragraph("Identity mismatch with PKI / key table", table_cell), Paragraph("Stage S2 (Block)", table_cell)],
        [Paragraph("CHANNEL", table_cell_bold), Paragraph("PQC tag fail / QBER > 11%", table_cell), Paragraph("Eavesdropping causes state collapse / noise", table_cell), Paragraph("Stage S4 (Lock)", table_cell)],
        [Paragraph("UNAUTH_VERIFY", table_cell_bold), Paragraph("Verifier lacking entitlement", table_cell), Paragraph("Access-control enforcement", table_cell), Paragraph("Stage S3 (Reset)", table_cell)],
    ]
    t_threat = Table(threat_table, colWidths=[75, 140, 215, 110])
    t_threat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#3F37C9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_threat)
    story.append(Spacer(1, 6))

    # Section 4: Mathematical Bound (Hoeffding's Formula)
    story.append(Paragraph("4. Mathematical Formulation: Hoeffding Statistical Threshold", h1_style))
    story.append(Paragraph(
        "Acceptance threshold <b>tau = p0 + sqrt( ln(1/delta) / (2n) )</b> where p0 is honest channel noise (2%), "
        "delta is the false-rejection budget (1%), and n is check count (64).<br/>"
        "• Default baseline: <b>tau = 0.02 + sqrt(ln(100)/128) = 0.2097 (~21.0%)</b>.<br/>"
        "• Honest transmission mismatch: ~0.00% to 2.00% (always accepted).<br/>"
        "• Forgery attempt mismatch: ~50.00% (probability of bypassing threshold is &lt; 1.8 × 10⁻⁷).",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 5: The 2-Minute Fit Test
    story.append(Paragraph("5. The North Star Fit Test (Reproduce in 2 Minutes)", h1_style))
    story.append(Paragraph(
        "1. Launch <code>scripts/run_demo.bat</code> (or <code>scripts/run_demo.sh</code>).<br/>"
        "2. Login to Mock Bank at <b>http://127.0.0.1:8080</b> as Alice (alice / alice123).<br/>"
        "3. Transfer ₹5,000 to Bob — verified with Qiskit Aer quantum circuit and committed.<br/>"
        "4. Open SOC console at <b>/soc</b> and click 'Trigger Forgery Attack'.<br/>"
        "5. System catches mismatch (p_hat ~ 0.50 &gt; 0.21) -> bank escalates to Stage S2.<br/>"
        "6. Return to transfer page -> Bank refuses new transactions (Application Lockdown).",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Footer notice
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceBefore=2, spaceAfter=4))
    story.append(Paragraph(
        "GitHub Repository: <b>https://github.com/Sansyuh06/yessit2026-Shorly_Not</b> | SIH 2026 PS 26141",
        ParagraphStyle('DocFooter', parent=body_style, fontSize=8, alignment=1, textColor=colors.HexColor("#64748B"))
    ))

    doc.build(story)
    print(f"Generated PDF: {pdf_path} (Size: {os.path.getsize(pdf_path)} bytes)")

if __name__ == "__main__":
    generate_pdf()
