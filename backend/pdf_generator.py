"""PasteurAI — A4 PDF Report Generator

Produces a professional medical report PDF using ReportLab.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable
)
from reportlab.graphics.shapes import Drawing, Rect, String
import qrcode
from io import BytesIO
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
LOGO_PATH = PROJECT_DIR / "frontend" / "public" / "logo-ipa.png"

# ── French category labels ──
CATEGORY_LABELS: dict[str, str] = {
    "blood": "Sang",
    "liver": "Foie",
    "kidney": "Reins",
    "lipids": "Lipides",
    "heart": "Coeur",
    "diabetes": "Diabète",
    "thyroid": "Thyroïde",
    "inflammation": "Inflammation",
    "vitamins": "Vitamines",
    "iron": "Fer",
    "bone": "Os",
    "prostate": "Prostate",
    "wbc_diff": "Globules Blancs",
    "adrenal": "Surrénales",
    "hormones": "Hormones",
    "coagulation": "Coagulation",
    "electrolyte": "Électrolytes",
    "immunology": "Immunologie",
    "tumor": "Marqueurs T",
    "nutrition": "Nutrition",
    "toxicology": "Toxicologie",
    "urine": "Analyse d'Urine",
    "enzyme": "Enzymes",
    "other": "Autres",
}

CATEGORY_KEY_MAP: dict[str, str] = {
    "Blood Count": "blood",
    "Liver": "liver",
    "Liver Function": "liver",
    "Kidney": "kidney",
    "Kidney Function": "kidney",
    "Lipids": "lipids",
    "Lipid Profile": "lipids",
    "Cardiac Markers": "heart",
    "Diabetes": "diabetes",
    "Thyroid": "thyroid",
    "Inflammation": "inflammation",
    "Vitamins": "vitamins",
    "Iron": "iron",
    "Bone": "bone",
    "Prostate": "prostate",
    "White Cell Differential": "wbc_diff",
    "Adrenal": "adrenal",
    "Coagulation": "coagulation",
    "Electrolytes": "electrolyte",
    "Immunology": "immunology",
    "Tumor Markers": "tumor",
    "Nutrition": "nutrition",
    "Toxicology": "toxicology",
    "Urinalysis": "urine",
    "Enzymes": "enzyme",
    "Hematology": "blood",
    "Biochemistry": "liver",
    "Hormones": "hormones",
}

# ── Color palette (light / print) ──
PRIMARY = colors.HexColor("#1e88e5")
DARK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#475569")
SUCCESS = colors.HexColor("#16a34a")
WARNING = colors.HexColor("#f59e0b")
DANGER = colors.HexColor("#ef4444")
LIGHT_BG = colors.HexColor("#f8fafc")
WHITE = colors.white
BORDER = colors.HexColor("#e2e8f0")
HEADER_BG = colors.HexColor("#e8f0fe")
SCORE_TRACK = colors.HexColor("#e2e8f0")


def _map_category(dg: str) -> str:
    return CATEGORY_KEY_MAP.get(dg, "other")


def _category_label(dg: str) -> str:
    return CATEGORY_LABELS.get(_map_category(dg), dg)


def _status(value, r: dict | None) -> str:
    if value is None or not r:
        return "normal"
    rmin = r.get("min")
    rmax = r.get("max")
    if rmax is not None and value > rmax * 1.5:
        return "critical"
    if rmin is not None and value < rmin * 0.5:
        return "critical"
    if rmax is not None and value > rmax:
        return "elevated"
    if rmin is not None and value < rmin:
        return "low"
    return "normal"


def _status_color(status: str) -> colors.Color:
    return {"normal": SUCCESS, "elevated": WARNING, "low": WARNING, "critical": DANGER}.get(status, MUTED)


def _status_label(status: str) -> str:
    return {"normal": "Normal", "elevated": "Élevé", "low": "Bas", "critical": "Critique"}.get(status, "")


def _health_score(tests: list) -> int:
    if not tests:
        return 0
    abnormal = sum(1 for t in tests if t.get("abnormal"))
    critical = 0
    for t in tests:
        r = t.get("range")
        if not r:
            continue
        v = t.get("value")
        if v is None:
            continue
        rmax = r.get("max")
        rmin = r.get("min")
        if rmax is not None and v > rmax * 1.5:
            critical += 1
        elif rmin is not None and v < rmin * 0.5:
            critical += 1
    denom = len(tests) + critical
    ratio = 1 - (abnormal + critical * 2) / denom if denom > 0 else 1
    return max(0, min(100, round(ratio * 100)))


# ── Custom flowable: health-score gauge ──
class ScoreGauge(Drawing):
    def __init__(self, score: int, width: float = 440, height: float = 22):
        super().__init__(width, height)
        bar_color = SUCCESS if score >= 70 else (WARNING if score >= 50 else DANGER)
        r = 4
        y = (height - 12) / 2
        bar_h = 12
        self.add(Rect(0, y, width, bar_h, rx=r, ry=r, fillColor=SCORE_TRACK, strokeColor=None))
        fw = max(4, width * score / 100)
        self.add(Rect(0, y, fw, bar_h, rx=r, ry=r, fillColor=bar_color, strokeColor=None))
        self.add(String(width / 2, y - 2, f"{score}/100", textAnchor="middle",
                        fontName="Helvetica-Bold", fontSize=10, fillColor=WHITE))


# ── Page footer ──
def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(A4[0] / 2, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ── Main generator ──
def generate_pdf(report: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=18*mm, bottomMargin=22*mm)

    # Styles
    S = type("S", (), {})()
    S.title = ParagraphStyle("T", fontName="Helvetica-Bold", fontSize=18,
                              textColor=PRIMARY, spaceAfter=2, spaceBefore=0)
    S.subtitle = ParagraphStyle("St", fontSize=8.5, textColor=MUTED, spaceAfter=8)
    S.section = ParagraphStyle("Sec", fontName="Helvetica-Bold", fontSize=12,
                                textColor=DARK, spaceBefore=14, spaceAfter=6)
    S.body = ParagraphStyle("B", fontSize=9.5, textColor=DARK, leading=13)
    S.body_bold = ParagraphStyle("Bb", parent=S.body, fontName="Helvetica-Bold")
    S.mono = ParagraphStyle("M", fontName="Courier-Bold", fontSize=9.5,
                             textColor=DARK, leading=12)
    S.cell = ParagraphStyle("C", fontSize=8.5, textColor=DARK, leading=11)
    S.status = ParagraphStyle("Sts", fontSize=8.5, fontName="Helvetica-Bold", leading=11)
    S.legend = ParagraphStyle("L", fontSize=7.5, leading=10)
    S.footer = ParagraphStyle("F", fontSize=7.5, textColor=MUTED,
                               alignment=1, spaceBefore=4)
    S.qr_text = ParagraphStyle("Q", fontSize=8.5, textColor=MUTED, leading=12)
    S.header_text = ParagraphStyle("Hd", fontSize=9.5, textColor=DARK, leading=13)

    story = []

    # ── Header: logo + institution ──
    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH), width=95, height=57)
    else:
        logo = Paragraph("", S.body)

    hdr = Table(
        [[logo, Paragraph(
            "<b>INSTITUT PASTEUR D'ALGÉRIE</b><br/>"
            "Route du Petit Staouéli, Dely Brahim<br/>"
            "16320 Alger, Algérie", S.header_text)]],
        colWidths=[105, 385])
    hdr.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
    ]))
    story.append(hdr)
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY,
                            spaceAfter=8, spaceBefore=4))

    # ── Title + reference ──
    ref = report.get("report_ref", "")
    date_edition = report.get("dates", {}).get("edition", "")
    story.append(Paragraph("RAPPORT D'ANALYSES BIOMÉDICALES", S.title))
    story.append(Paragraph(
        f"Référence: {ref} &nbsp;&nbsp;|&nbsp;&nbsp; Date d'édition: {date_edition}",
        S.subtitle))

    # ── Patient info ──
    patient = report.get("patient", {})
    p_name = patient.get("name", "Non renseigné")
    p_age = patient.get("age")
    p_sex = patient.get("sex", "")
    age_sex = f"{p_age} ans" if p_age else ""
    if p_sex:
        age_sex += f" / {p_sex}" if age_sex else p_sex

    story.append(Spacer(1, 2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER,
                            spaceAfter=5, spaceBefore=2))

    tests = report.get("tests", [])
    score = _health_score(tests)

    info_rows = [
        [Paragraph(f"<b>Patient:</b>  {p_name}", S.body),
         Paragraph(f"<b>Âge / Sexe:</b>  {age_sex}", S.body)],
        [Paragraph(f"<b>Référence:</b>  {ref}", S.body),
         Paragraph(f"<b>Date:</b>  {date_edition}", S.body)],
    ]
    if score:
        info_rows.append([
            Paragraph(f"<b>Score Santé:</b>  {score}/100", S.body_bold),
            Paragraph("", S.body),
        ])
    pt = Table(info_rows, colWidths=[245, 245])
    pt.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(pt)

    # ── Score gauge ──
    if score:
        story.append(ScoreGauge(score))
        story.append(Spacer(1, 2))
        # Legend
        leg = Table([[
            Paragraph("● &nbsp;Normal (≥ 70)", S.legend),
            Paragraph("● &nbsp;À surveiller (50-69)", S.legend),
            Paragraph("● &nbsp;Attention (< 50)", S.legend),
        ]], colWidths=[145, 155, 135])
        leg.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TEXTCOLOR", (0, 0), (0, 0), SUCCESS),
            ("TEXTCOLOR", (1, 0), (1, 0), WARNING),
            ("TEXTCOLOR", (2, 0), (2, 0), DANGER),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(leg)

    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER,
                            spaceAfter=6, spaceBefore=4))

    # ── Biomarkers by system ──
    story.append(Paragraph("RÉSULTATS PAR SYSTÈME", S.section))

    grouped: dict[str, list] = {}
    for t in tests:
        key = _category_label(t.get("dashboard_group") or t.get("category") or "Other")
        grouped.setdefault(key, []).append(t)

    COL_W = [162, 58, 52, 82, 72]

    for gname, gtests in sorted(grouped.items()):
        rows = [[
            Paragraph(f"<b>{gname}</b>", S.cell),
            Paragraph("<b>Valeur</b>", S.cell),
            Paragraph("<b>Unité</b>", S.cell),
            Paragraph("<b>Norme</b>", S.cell),
            Paragraph("<b>Statut</b>", S.cell),
        ]]
        for t in gtests:
            name = t.get("test_name", "")
            val = t.get("value")
            vdisp = t.get("value_display", "")
            unit = t.get("unit", "")
            r = t.get("range", {}) or {}
            rmin = r.get("min") if r else None
            rmax = r.get("max") if r else None

            st = _status(val, r)
            sc = _status_color(st)
            sl = _status_label(st)

            if val is not None:
                vs = f"{val:g}" if isinstance(val, float) else str(val)
            else:
                vs = vdisp or "N/A"

            if rmin is not None and rmax is not None:
                rs = f"{rmin:g} – {rmax:g}"
            elif rmin is not None:
                rs = f"> {rmin:g}"
            elif rmax is not None:
                rs = f"< {rmax:g}"
            else:
                rs = ""

            vc = sc.hexval() if st != "normal" else DARK.hexval()

            rows.append([
                Paragraph(name, S.cell),
                Paragraph(f'<font color="{vc}"><b>{vs}</b></font>',
                          ParagraphStyle("V", parent=S.cell, fontSize=9,
                                         fontName="Courier-Bold")),
                Paragraph(unit, S.cell),
                Paragraph(rs, S.cell),
                Paragraph(f'<font color="{sc.hexval()}"><b>{sl}</b></font>', S.cell),
            ])

        tb = Table(rows, colWidths=COL_W)
        tbs = [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), PRIMARY),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ]
        for i in range(2, len(rows), 2):
            tbs.append(("BACKGROUND", (0, i), (-1, i), LIGHT_BG))
        tb.setStyle(TableStyle(tbs))
        story.append(tb)
        story.append(Spacer(1, 5))

    # ── AI Interpretation ──
    interpretations = report.get("interpretations", [])
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER,
                            spaceAfter=6, spaceBefore=2))
    story.append(Paragraph("INTERPRÉTATION IA", S.section))

    if interpretations:
        lines: list[str] = []
        for i in interpretations:
            sev = i.get("severity", "")
            unit = i.get("unit", "")
            val = i.get("value")
            raw = i.get("raw", "")
            part = sev
            if unit:
                part += f" ({unit})"
            if val is not None:
                part += f" : {val:g}" if isinstance(val, float) else f" : {val}"
            elif raw:
                part += f" : {raw}"
            lines.append(part)
        ai_text = ". ".join(lines) + "." if lines else ""
    else:
        if score >= 70:
            ai_text = f"Analyse basée sur {len(tests)} biomarqueurs. Profil général satisfaisant."
        elif score >= 50:
            ai_text = f"Analyse basée sur {len(tests)} biomarqueurs. Plusieurs paramètres à surveiller."
        else:
            ai_text = f"Analyse basée sur {len(tests)} biomarqueurs. Attention médicale recommandée."

    if ai_text:
        story.append(Paragraph(ai_text,
            ParagraphStyle("AI", parent=S.body, fontSize=9.5, leading=14, spaceAfter=4)))

    story.append(Paragraph(
        "<b>Recommandation :</b> Consultez votre médecin traitant pour une interprétation "
        "clinique complète de ces résultats.",
        ParagraphStyle("Rec", parent=S.body, fontSize=9, textColor=MUTED, leading=13,
                       spaceBefore=2)))

    # ── QR Code ──
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER,
                            spaceAfter=8, spaceBefore=2))

    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(ref)
    qr.make(fit=True)
    qr_pil = qr.make_image(fill_color="#" + DARK.hexval()[2:], back_color="#" + WHITE.hexval()[2:])
    qr_buf = BytesIO()
    qr_pil.save(qr_buf, format="PNG")
    qr_buf.seek(0)

    qr_tbl = Table(
        [[Image(qr_buf, width=72, height=72),
          Paragraph(
              "Scannez ce code QR pour accéder à la version numérique<br/>"
              "détaillée de votre rapport d'analyses.",
              S.qr_text)]],
        colWidths=[82, 370])
    qr_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
    ]))
    story.append(qr_tbl)

    # ── Disclaimer footer ──
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER,
                            spaceAfter=4, spaceBefore=2))
    story.append(Paragraph(
        "Résultat non contractuel — Consultez votre médecin pour une interprétation clinique.<br/>"
        "Document généré par PasteurAI — Institut Pasteur d'Algérie",
        S.footer))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
