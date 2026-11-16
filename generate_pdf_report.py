"""
PDF Report Generator for Quantum Transport Course Project (Problem 8)
Generates a publication-grade, styled PDF with embedded simulation figures.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, "figures")
PDF_PATH = os.path.join(BASE_DIR, "PROJECT_REPORT.pdf")


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "Fundamentals of Quantum Transport & Nanoelectronics | Problem 8")
            self.drawRightString(612 - 54, 755, "Josephson Junctions & SQUID Interference")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 748, 612 - 54, 748)
            
        # Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 38, page_str)
        self.drawString(54, 38, "Course Project Report — Academic Submission 2026")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 612 - 54, 48)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=14
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#0369a1'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.2,
        leading=13.5,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )

    formula_style = ParagraphStyle(
        'FormulaText',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#0369a1'),
        backColor=colors.HexColor('#f0f9ff'),
        borderColor=colors.HexColor('#bae6fd'),
        borderWidth=0.5,
        borderPadding=5,
        spaceBefore=4,
        spaceAfter=6
    )

    caption_style = ParagraphStyle(
        'FigCaption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.2,
        leading=11.5,
        textColor=colors.HexColor('#475569'),
        alignment=1, # Center
        spaceBefore=3,
        spaceAfter=8
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Fundamental of Quantum Transport and Nanoelectronics", subtitle_style))
    story.append(Paragraph("Josephson Junctions and Superconducting Quantum Interference: Mathematical Modeling, Numerical Simulation, and Applications", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10))

    meta_text = "<b>Course Project Topic:</b> Problem 8 &bull; <b>Model:</b> RCSJ & DC SQUID &bull; <b>Academic Year:</b> 2026"
    story.append(Paragraph(meta_text, body_style))
    story.append(Spacer(1, 6))

    # Executive Summary Box
    summary_html = (
        "<b>Executive Summary:</b> This project develops a comprehensive theoretical and numerical investigation of "
        "Josephson junctions and DC Superconducting Quantum Interference Devices (SQUIDs). We formulate the macroscopic "
        "quantum order parameter Ψ = √n<sub>s</sub> e<sup>iθ</sup> and derive the fundamental Josephson relations "
        "from Feynman's coupled two-state tunneling equations. The Resistively and Capacitively Shunted Junction (RCSJ) "
        "model is mapped to a classical particle in a tilted washboard potential. Using adaptive Runge-Kutta numerical integration, "
        "we investigate the phase evolution, I-V characteristics, damping hysteresis, microwave-induced Shapiro steps, "
        "and magnetic flux interference. In addition, an interactive visual simulation dashboard has been constructed to "
        "provide real-time demonstration of Cooper pair tunneling and quantum interference."
    )
    summary_table = Table([[Paragraph(summary_html, body_style)]], colWidths=[504])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 9),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # Section 1: Introduction
    story.append(Paragraph("1. Physical Formulation & Objectives", h1_style))
    story.append(Paragraph(
        "In superconductors below critical temperature T<sub>c</sub>, electrons condense into Cooper pairs (charge q = -2e, mass m* = 2m<sub>e</sub>), "
        "forming a single macroscopic quantum wave. Across a thin insulator (SIS junction), Cooper pairs tunnel coherently without "
        "breaking up. This leads to the DC Josephson effect (zero-voltage supercurrent up to I<sub>c</sub>) and the AC Josephson effect "
        "(high-frequency microwave oscillations under an applied DC voltage). When two junctions are combined in a superconducting loop, "
        "the SQUID acts as a quantum double-slit interferometer for Cooper pairs, with critical current modulated by magnetic flux Φ<sub>ext</sub> with period Φ<sub>0</sub> = h/2e ≈ 2.068 fWb.",
        body_style
    ))

    # Section 2: Theory & Derivations
    story.append(Paragraph("2. Quantum Mechanical Principles & Governing Equations", h1_style))
    story.append(Paragraph("<b>2.1 Feynman Two-State Model & Josephson Relations</b>", h2_style))
    story.append(Paragraph(
        "Let ψ<sub>1</sub> and ψ<sub>2</sub> represent the condensate amplitudes in each superconductor, coupled by tunneling matrix element K:<br/>"
        "iℏ ∂ψ<sub>1</sub>/∂t = -eV ψ<sub>1</sub> + K ψ<sub>2</sub> &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; "
        "iℏ ∂ψ<sub>2</sub>/∂t = +eV ψ<sub>2</sub> + K ψ<sub>1</sub><br/>"
        "Writing ψ<sub>j</sub> = √n<sub>s</sub> e<sup>iθ<sub>j</sub></sup> and separating into real and imaginary parts yields the two Josephson relations:",
        body_style
    ))
    story.append(Paragraph(
        "First Josephson Relation (DC): &nbsp;&nbsp;<b>I<sub>s</sub> = I<sub>c</sub> sin(φ)</b><br/>"
        "Second Josephson Relation (AC): &nbsp;<b>dφ/dt = (2e/ℏ) V = (2π/Φ<sub>0</sub>) V</b>",
        formula_style
    ))

    story.append(Paragraph("<b>2.2 RCSJ Model & Tilted Washboard Potential</b>", h2_style))
    story.append(Paragraph(
        "Accounting for barrier capacitance C and normal quasiparticle resistance R, Kirchhoff's law gives:<br/>"
        "I = C (dV/dt) + V/R + I<sub>c</sub> sin(φ)<br/>"
        "In dimensionless form with time τ = ω<sub>c</sub> t and Stewart-McCumber parameter β<sub>C</sub> = 2e I<sub>c</sub> R<sup>2</sup> C / ℏ:",
        body_style
    ))
    story.append(Paragraph(
        "<b>β<sub>C</sub> (d<sup>2</sup>φ/dτ<sup>2</sup>) + (dφ/dτ) + sin(φ) = I / I<sub>c</sub></b><br/>"
        "Potential Energy: &nbsp;<b>U(φ) = -E<sub>J</sub> [ cos(φ) + (I / I<sub>c</sub>) φ ]</b>, &nbsp;&nbsp; where E<sub>J</sub> = ℏI<sub>c</sub> / 2e",
        formula_style
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>2.3 DC SQUID & Fluxoid Quantization</b>", h2_style))
    story.append(Paragraph(
        "Single-valuedness of the macroscopic wavefunction enforces phase quantization around the closed loop: "
        "φ<sub>2</sub> - φ<sub>1</sub> = 2π (Φ<sub>total</sub> / Φ<sub>0</sub>). Summing the supercurrents yields:",
        body_style
    ))
    story.append(Paragraph(
        "General: &nbsp;&nbsp;<b>I<sub>c,total</sub>(Φ) = √[ (I<sub>c1</sub> - I<sub>c2</sub>)<sup>2</sup> + 4 I<sub>c1</sub> I<sub>c2</sub> cos<sup>2</sup>(π Φ / Φ<sub>0</sub>) ]</b><br/>"
        "Symmetric: <b>I<sub>c,total</sub>(Φ) = 2 I<sub>c</sub> |cos(π Φ / Φ<sub>0</sub>)|</b>",
        formula_style
    ))

    # Figure 1
    story.append(Spacer(1, 6))
    fig1_img = os.path.join(FIG_DIR, "fig1_josephson_energy_phase.png")
    if os.path.exists(fig1_img):
        story.append(Image(fig1_img, width=490, height=188))
        story.append(Paragraph("<b>Figure 1:</b> (a) Current-phase relation (CPR). (b) Tilted washboard potential landscape U(φ) at various bias currents I/I<sub>c</sub>.", caption_style))

    # Section 3: Numerical Results
    story.append(Paragraph("3. Numerical Simulation Results & Parameter Studies", h1_style))
    story.append(Paragraph(
        "The dynamical equations were numerically solved using the Runge-Kutta 4th/5th order Dormand-Prince integrator (`scipy.integrate.solve_ivp`). "
        "Below are the primary parameter investigations required by the project specifications.",
        body_style
    ))

    # Figure 2
    fig2_img = os.path.join(FIG_DIR, "fig2_rcsj_dynamics_iv_curve.png")
    if os.path.exists(fig2_img):
        story.append(Image(fig2_img, width=490, height=315))
        story.append(Paragraph("<b>Figure 2:</b> RCSJ model dynamics: (a) Phase evolution φ(τ), (b) Instantaneous AC voltage pulses V(τ), (c) I-V characteristics showing Stewart-McCumber damping hysteresis for β<sub>C</sub> = 3.0.", caption_style))

    # Figure 3
    story.append(Spacer(1, 4))
    fig3_img = os.path.join(FIG_DIR, "fig3_squid_flux_interference.png")
    if os.path.exists(fig3_img):
        story.append(Image(fig3_img, width=490, height=192))
        story.append(Paragraph("<b>Figure 3:</b> SQUID critical current I<sub>c</sub> vs applied flux Φ/Φ<sub>0</sub>: (a) Effect of junction asymmetry α = I<sub>c2</sub>/I<sub>c1</sub>. (b) Effect of loop screening inductance β<sub>L</sub> = 2 L I<sub>c</sub> / Φ<sub>0</sub>.", caption_style))

    # Parameter Study Explanations
    story.append(Paragraph("<b>Analysis of Changing Physical Parameters:</b>", h2_style))
    param_text = (
        "1. <b>Applied Magnetic Flux (Φ/Φ<sub>0</sub>):</b> Modulates critical current with exact period Φ<sub>0</sub>. At half-integer flux quanta "
        "(Φ = 0.5 Φ<sub>0</sub>), destructive interference reduces the supercurrent to a minimum.<br/>"
        "2. <b>Junction Asymmetry (α = I<sub>c2</sub>/I<sub>c1</sub>):</b> For symmetric junctions (α = 1.0), cancellation at Φ = 0.5 Φ<sub>0</sub> is complete (I<sub>min</sub> = 0). "
        "As asymmetry increases (α < 1), incomplete interference elevates the minimum to I<sub>min</sub> = (1 - α) I<sub>c1</sub>.<br/>"
        "3. <b>Screening Inductance (β<sub>L</sub> = 2 L I<sub>c</sub> / Φ<sub>0</sub>):</b> In finite-inductance loops, circulating screening currents "
        "generate opposing magnetic flux, flattening the interference peaks and distorting the response into a sheared profile.<br/>"
        "4. <b>Capacitive Damping (β<sub>C</sub>):</b> Low damping (β<sub>C</sub> > 1) produces massive hysteresis in the I-V curve, where phase particle "
        "inertia maintains a resistive state down to the retrapping current I<sub>r</sub> ≈ (4 / π√β<sub>C</sub>) I<sub>c</sub>."
    )
    story.append(Paragraph(param_text, body_style))

    # Figure 4 & 5
    story.append(Spacer(1, 6))
    fig4_img = os.path.join(FIG_DIR, "fig4_shapiro_steps.png")
    if os.path.exists(fig4_img):
        story.append(Image(fig4_img, width=490, height=196))
        story.append(Paragraph("<b>Figure 4:</b> (a) AC Josephson frequency relation f<sub>J</sub> = 483.6 MHz/μV. (b) Quantized Shapiro voltage steps under microwave irradiation V<sub>n</sub> = n (h f / 2e).", caption_style))

    story.append(Spacer(1, 4))
    fig5_img = os.path.join(FIG_DIR, "fig5_quantum_phase_coherence_summary.png")
    if os.path.exists(fig5_img):
        story.append(Image(fig5_img, width=490, height=182))
        story.append(Paragraph("<b>Figure 5:</b> Nanoelectronics applications: (a) SQUID flux-to-voltage transfer function for brain MEG magnetometry. (b) Transmon qubit anharmonic energy levels enabled by non-linear Josephson inductance L<sub>J</sub>(φ).", caption_style))

    # Section 4: Quantitative Table
    story.append(Paragraph("4. Quantitative Parameter Comparison Table", h1_style))
    table_data = [
        [Paragraph('<b>Parameter</b>', body_style), Paragraph('<b>Symbol / Formula</b>', body_style), Paragraph('<b>Tested Range</b>', body_style), Paragraph('<b>Observed Physical Impact</b>', body_style)],
        [Paragraph('Magnetic Flux', body_style), Paragraph('Φ / Φ<sub>0</sub>', body_style), Paragraph('-2.5 to +2.5', body_style), Paragraph('Periodic quantum interference with period Φ<sub>0</sub>', body_style)],
        [Paragraph('Asymmetry', body_style), Paragraph('α = I<sub>c2</sub>/I<sub>c1</sub>', body_style), Paragraph('0.1 to 1.0', body_style), Paragraph('Elevates null to I<sub>min</sub> = (1-α)I<sub>c1</sub>', body_style)],
        [Paragraph('Screening Inductance', body_style), Paragraph('β<sub>L</sub> = 2 L I<sub>c</sub> / Φ<sub>0</sub>', body_style), Paragraph('0.0 to 2.0', body_style), Paragraph('Attenuates modulation depth, shears CPR', body_style)],
        [Paragraph('Stewart-McCumber', body_style), Paragraph('β<sub>C</sub> = ω<sub>c</sub> R<sup>2</sup> C', body_style), Paragraph('0.2 to 3.0', body_style), Paragraph('Controls hysteresis and retrapping current I<sub>r</sub>', body_style)],
        [Paragraph('Microwave Drive', body_style), Paragraph('f = ω<sub>rf</sub> / 2π', body_style), Paragraph('0.5 ω<sub>c</sub>', body_style), Paragraph('Induces quantized Shapiro voltage steps V<sub>n</sub> = n Φ<sub>0</sub> f', body_style)]
    ]
    t = Table(table_data, colWidths=[110, 115, 85, 194])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)

    # Section 5: Physical Discussion & Nanoelectronics
    story.append(Paragraph("5. Physical Discussion & Nanoelectronic Applications", h1_style))
    story.append(Paragraph(
        "<b>1. Quantum Phase Coherence & Rigidity:</b> In normal metals, electron phase coherence is destroyed within nanometers by inelastic scattering. "
        "In superconductors, off-diagonal long-range order locks the phase across macroscopic centimeters, producing the non-local phase interference observed in SQUIDs.<br/>"
        "<b>2. Ultra-Sensitive Magnetometry (MEG):</b> Operating a SQUID at its maximum transfer slope |dV/dΦ| achieves magnetic flux noise on the order of "
        "10<sup>-6</sup> Φ<sub>0</sub> / √Hz, enabling non-invasive detection of femtotesla synaptic brain activity.<br/>"
        "<b>3. Superconducting Quantum Computing (Transmon Qubits):</b> A Josephson junction provides a non-dissipative, non-linear inductance "
        "L<sub>J</sub>(φ) = Φ<sub>0</sub> / (2π I<sub>c</sub> cos φ). This non-linearity yields negative anharmonicity, selectively isolating the |0⟩ and |1⟩ "
        "qubit states without leakage into higher energy levels.",
        body_style
    ))

    # Section 6: Conclusions & References
    story.append(Paragraph("6. Conclusions & References", h1_style))
    story.append(Paragraph(
        "This project successfully modeled and simulated Josephson junction dynamics and SQUID quantum interference. "
        "The numerical simulations fully confirm theoretical predictions of Cooper pair matter wave interference, "
        "RCSJ washboard mechanics, damping hysteresis, and Shapiro step quantization.<br/><br/>"
        "<b>Key References:</b><br/>"
        "[1] B. D. Josephson, <i>Phys. Lett.</i> <b>1</b>, 251 (1962).<br/>"
        "[2] R. C. Jaklevic et al., <i>Phys. Rev. Lett.</i> <b>12</b>, 159 (1964).<br/>"
        "[3] M. Tinkham, <i>Introduction to Superconductivity</i>, 2nd ed. (Dover, 2004).<br/>"
        "[4] J. Clarke and A. I. Braginski, <i>The SQUID Handbook</i> (Wiley-VCH, 2004).<br/>"
        "[5] J. Koch et al., <i>Phys. Rev. A</i> <b>76</b>, 042319 (2007).",
        body_style
    ))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Publication PDF Report successfully built: {PDF_PATH}")


if __name__ == "__main__":
    build_pdf()
