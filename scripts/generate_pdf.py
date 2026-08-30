"""
Publication-Quality PDF Generator for ShorlyNot Project Overview.
Generates a comprehensive 2-page executive summary document: docs/ShorlyNot_What_Is_This_Project.pdf
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)


def generate_pdf():
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "docs", "ShorlyNot_What_Is_This_Project.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2563EB"),
        alignment=1
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#64748B"),
        alignment=1
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=7,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#334155")
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1E293B")
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1E293B")
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell,
        fontName='Helvetica-Bold'
    )

    story = []

    # ==================== PAGE 1: ARCHITECTURE & PROTOCOL ====================
    story.append(Paragraph("SHORLYNOT", title_style))
    story.append(Paragraph("Quantum-Inspired Cyber Threat Detection for Digital Signature Security", subtitle_style))
    story.append(Paragraph("Smart India Hackathon 2026 · Problem Statement PS 26141 · Team Egreen Quanta", meta_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceBefore=1, spaceAfter=6))

    # Executive Overview Box
    exec_box = (
        "<b>Executive Summary:</b> ShorlyNot is an end-to-end quantum security architecture solving classical "
        "digital signature vulnerability against quantum forgery and harvesting attacks. It replaces classical "
        "algorithms (RSA/ECDSA/Ed25519) with <b>teleportation-based Quantum Digital Signatures (ShorlyNot-QDS-T1)</b> "
        "running on real Qiskit Aer quantum circuits, protected by BB84 QKD and PQC layers, with real-time "
        "<b>non-machine-learning threat detection (Q-STDF)</b> governed by Hoeffding statistical bounds."
    )
    t_box = Table([[Paragraph(exec_box, callout_style)]], colWidths=[540])
    t_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#3B82F6")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_box)
    story.append(Spacer(1, 6))

    # Section 1: Exactly Two Products
    story.append(Paragraph("1. System Architecture: Exactly Two Products", h1_style))
    story.append(Paragraph(
        "• <b>skeleton/ (The Core Invention):</b> Standalone quantum framework & FastAPI service (:8000). "
        "Executes 3-qubit Bell teleportation circuits on Qiskit Aer, statistical bounding, and BB84 QKD.<br/>"
        "• <b>bank/ (The Operational Proof):</b> Full banking web app (:8080) & real-time dark SOC console. "
        "Every transaction is quantum-signed; detected threats automatically trigger application lockdown (S0 to S4).",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 2: Quantum Teleportation Signing & Verification
    story.append(Paragraph("2. ShorlyNot-QDS-T1 Teleportation Protocol Specification", h1_style))
    qds_data = [
        [Paragraph("Stage", table_header), Paragraph("Signer (Alice) / Verifier (Bob) Action", table_header), Paragraph("Underlying Quantum Physics / Math", table_header)],
        [Paragraph("1. Encode", table_cell_bold), Paragraph("Hash payload (SHA-256) & derive L=128 check positions.", table_cell), Paragraph(r"Pauli states |0&gt;, |1&gt;, |+&gt;, |-&gt; via {Z, X} bases", table_cell)],
        [Paragraph("2. Entangle", table_cell_bold), Paragraph(r"Distribute Bell pairs |&Phi;+&gt; across quantum channel.", table_cell), Paragraph(r"|&Phi;+&gt; = (|00&gt; + |11&gt;) / &radic;2", table_cell)],
        [Paragraph("3. Teleport", table_cell_bold), Paragraph("Alice executes Bell-state measurement (BSM) circuit.", table_cell), Paragraph(r"Yields 2 classical syndrome bits (m1, m2) &isin; {0,1}&sup2;", table_cell)],
        [Paragraph("4. Protect", table_cell_bold), Paragraph("Encrypt syndromes with BB84 QKD session key.", table_cell), Paragraph("PQC AES-256-GCM authenticated payload wrapper", table_cell)],
        [Paragraph("5. Correct", table_cell_bold), Paragraph("Bob applies Pauli correction matrix U(m1, m2) to his qubit.", table_cell), Paragraph(r"U &isin; {I, X, Z, XZ} restores original state", table_cell)],
        [Paragraph("6. Verify", table_cell_bold), Paragraph(r"Bob projects in Alice's basis &beta; & checks error rate p&#770;.", table_cell), Paragraph(r"Accepted if and only if p&#770; &le; &tau; (Hoeffding Bound)", table_cell)],
    ]
    t_qds = Table(qds_data, colWidths=[55, 235, 250])
    t_qds.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_qds)
    story.append(Spacer(1, 6))

    # Section 3: Pauli Correction Lookup
    story.append(Paragraph("3. Pauli Teleportation Unitary Lookup Matrix", h1_style))
    pauli_data = [
        [Paragraph("Syndrome (m1, m2)", table_header), Paragraph("Pauli Operator U", table_header), Paragraph("Matrix Representation", table_header), Paragraph("Physical Action on Bob's Entangled State", table_header)],
        [Paragraph("<code>(0, 0)</code>", table_cell_bold), Paragraph("I (Identity)", table_cell), Paragraph("[[1, 0], [0, 1]]", table_cell), Paragraph("No transformation required", table_cell)],
        [Paragraph("<code>(0, 1)</code>", table_cell_bold), Paragraph("X (Bit Flip)", table_cell), Paragraph("[[0, 1], [1, 0]]", table_cell), Paragraph(r"Flips |0&gt; &harr; |1&gt;", table_cell)],
        [Paragraph("<code>(1, 0)</code>", table_cell_bold), Paragraph("Z (Phase Flip)", table_cell), Paragraph("[[1, 0], [0, -1]]", table_cell), Paragraph(r"Inverts relative phase |+&gt; &harr; |-&gt;", table_cell)],
        [Paragraph("<code>(1, 1)</code>", table_cell_bold), Paragraph("XZ (Bit + Phase)", table_cell), Paragraph("[[0, -1], [1, 0]]", table_cell), Paragraph("Simultaneous bit & phase correction", table_cell)],
    ]
    t_pauli = Table(pauli_data, colWidths=[90, 85, 125, 240])
    t_pauli.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_pauli)
    story.append(Spacer(1, 10))

    # Page Break for Page 2
    story.append(PageBreak())

    # ==================== PAGE 2: DETECTION, MATH & DEMO ====================
    story.append(Paragraph("SHORLYNOT · Threat Engine & Mathematical Proofs", title_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceBefore=1, spaceAfter=6))

    # Section 4: Mathematical Bound (Hoeffding)
    story.append(Paragraph("4. Mathematical Formulation: Hoeffding Statistical Bound", h1_style))
    story.append(Paragraph(
        "The deterministic acceptance threshold &tau; is computed from Hoeffding's Inequality to guarantee "
        "provable bounds against forgery while allowing honest physical channel noise:<br/>"
        "&tau; = p0 + &radic;( ln(1/&delta;) / 2n )<br/>"
        "• <b>Honest Noise Floor (p0):</b> 0.02 (2.0%) · <b>Check Qubits (n):</b> 64 · <b>False Rejection Budget (&delta;):</b> 0.01 (1.0%).<br/>"
        "• <b>Calculated Threshold:</b> &tau; = 0.02 + &radic;(ln(100)/128) = <b>0.2097</b> (~21.0%).<br/>"
        "• <b>Honest Signer:</b> p&#770; &approx; 0.00 to 0.02 &le; &tau; (Accepted).<br/>"
        "• <b>Random Forger:</b> p&#770; &approx; 0.50 &gt; &tau; (Probability of bypassing threshold is P_forge &lt; 9.40 &times; 10&supmin;&sup7;).",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Section 5: Threat Ladder & Attack Vectors
    story.append(Paragraph("5. Q-STDF 6-Step Non-ML Threat Decision Ladder", h1_style))
    threat_data = [
        [Paragraph("Attack Vector", table_header), Paragraph("Decision Step & Deterministic Check", table_header), Paragraph("Mathematical / Protocol Guarantee", table_header), Paragraph("Stage Escalation", table_header)],
        [Paragraph("UNAUTH_VERIFY", table_cell_bold), Paragraph("Step 1: Check verifier identity credentials", table_cell), Paragraph("Role-based cryptographic entitlement check", table_cell), Paragraph("Stage S3 (Reset)", table_cell)],
        [Paragraph("IMPERSONATION", table_cell_bold), Paragraph("Step 2: Signer identity != registered key ID", table_cell), Paragraph("Hardware-bound identity certificate validation", table_cell), Paragraph("Stage S2 (Block)", table_cell)],
        [Paragraph("REPLAY", table_cell_bold), Paragraph("Step 3: Nonce exists in replay LRU cache", table_cell), Paragraph("Cryptographic uniqueness within time window", table_cell), Paragraph("Stage S3 (Reset)", table_cell)],
        [Paragraph("CHANNEL", table_cell_bold), Paragraph("Step 4: PQC tag validation or QBER &gt; 11%", table_cell), Paragraph("Eavesdropping breaks entanglement / flips bits", table_cell), Paragraph("Stage S4 (Lock)", table_cell)],
        [Paragraph("FORGERY", table_cell_bold), Paragraph("Step 5: Mismatch rate p&#770; &gt; &tau; (Hoeffding)", table_cell), Paragraph("Quantum state disturbance cannot be forged", table_cell), Paragraph("Stage S2 &rarr; S4", table_cell)],
        [Paragraph("OK", table_cell_bold), Paragraph("Step 6: All quantum & protocol checks passed", table_cell), Paragraph("Empirical error p&#770; &le; 0.2097 (Honest proof)", table_cell), Paragraph("Stage S0 (Normal)", table_cell)],
    ]
    t_threat = Table(threat_data, colWidths=[80, 160, 200, 100])
    t_threat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_threat)
    story.append(Spacer(1, 6))

    # Section 6: Security Stages (S0 to S4)
    story.append(Paragraph("6. Application Security Stages (S0 to S4)", h1_style))
    stage_data = [
        [Paragraph("Stage", table_header), Paragraph("State Name", table_header), Paragraph("Triggering Condition", table_header), Paragraph("Bank Application Enforcement Action", table_header)],
        [Paragraph("S0", table_cell_bold), Paragraph("Normal", table_cell), Paragraph("All checks p&#770; &le; &tau;, QBER &lt; 5%", table_cell), Paragraph("Full operations active; transactions committed ✅", table_cell)],
        [Paragraph("S1", table_cell_bold), Paragraph("Anomaly Watch", table_cell), Paragraph("QBER 5%-8% or single soft noise", table_cell), Paragraph("Soft operator alert; transactions permitted", table_cell)],
        [Paragraph("S2", table_cell_bold), Paragraph("Threat Active", table_cell), Paragraph("Signature Forgery or Impersonation", table_cell), Paragraph("New transfers blocked at application level 🚫", table_cell)],
        [Paragraph("S3", table_cell_bold), Paragraph("Pattern Alert", table_cell), Paragraph("Replay attack or unauthorized verifier", table_cell), Paragraph("Read-only ledger view; user sessions purged", table_cell)],
        [Paragraph("S4", table_cell_bold), Paragraph("Critical Lockdown", table_cell), Paragraph("Channel tampering or repeated forgeries", table_cell), Paragraph("Full application lockout page; requires ops reset 🔒", table_cell)],
    ]
    t_stage = Table(stage_data, colWidths=[40, 85, 175, 240])
    t_stage.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_stage)
    story.append(Spacer(1, 6))

    # Section 7: 90-Second Demo Walkthrough
    story.append(Paragraph("7. North Star 90-Second Live Demo Script", h1_style))
    story.append(Paragraph(
        "1. Launch <code>scripts/run_demo.bat</code> &rarr; opens Bank (:8080) and Skeleton (:8000).<br/>"
        "2. <b>Honest Transfer:</b> Login as Alice (<code>alice</code>/<code>alice123</code>), send ₹5,000 to Bob &rarr; Qiskit Aer circuit runs, p&#770; = 0.00 &le; 0.2097, balance updates.<br/>"
        "3. <b>Attack & Threshold Catch:</b> Open SOC at <code>/soc</code>, trigger 'FORGERY' &rarr; mismatch p&#770; &approx; 0.50 &gt; 0.2097, Stage escalates to S2.<br/>"
        "4. <b>Application Block:</b> Return to Bank, attempt transfer &rarr; Refused by Security Policy with parameters displayed.<br/>"
        "5. <b>Full Lockdown & Reset:</b> Trigger 'CHANNEL' on SOC &rarr; Stage escalates to S4, Bank displays lockout screen &rarr; click Reset to restore S0.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Footer notice
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceBefore=1, spaceAfter=3))
    story.append(Paragraph(
        "GitHub: <b>https://github.com/Sansyuh06/yessit2026-Shorly_Not</b> · Smart India Hackathon 2026 PS 26141",
        ParagraphStyle('DocFooter', parent=body_style, fontSize=7.5, alignment=1, textColor=colors.HexColor("#64748B"))
    ))

    doc.build(story)
    print(f"Generated High-Res Multi-Page PDF: {pdf_path} (Size: {os.path.getsize(pdf_path)} bytes)")


if __name__ == "__main__":
    generate_pdf()
