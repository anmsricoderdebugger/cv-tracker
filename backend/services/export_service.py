import csv
import io
from uuid import UUID

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from backend.services.matcher import get_leaderboard


def export_leaderboard_csv(db: Session, jd_id: UUID) -> bytes:
    entries = get_leaderboard(db, jd_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "Candidate", "Overall Score", "Fit Status",
        "Skills Score", "Experience Score", "Projects Score", "Keywords Score",
        "Matched Skills", "Missing Skills", "Strengths", "Gaps", "Explanation",
    ])
    for e in entries:
        writer.writerow([
            e["rank"],
            e["candidate_name"],
            f"{e['overall_score']:.1f}",
            e["fit_status"],
            f"{e['skills_score']:.0f}",
            f"{e['experience_score']:.0f}",
            f"{e['projects_score']:.0f}",
            f"{e['keywords_score']:.0f}",
            "; ".join(e.get("matched_skills", [])),
            "; ".join(e.get("missing_skills", [])),
            "; ".join(e.get("strengths", [])),
            "; ".join(e.get("gaps", [])),
            e.get("explanation", ""),
        ])
    return output.getvalue().encode("utf-8")


def export_leaderboard_xlsx(db: Session, jd_id: UUID) -> bytes:
    entries = get_leaderboard(db, jd_id)
    wb = Workbook()
    ws = wb.active
    ws.title = "Leaderboard"

    headers = [
        "Rank", "Candidate", "Overall Score", "Fit Status",
        "Skills Score", "Experience Score", "Projects Score", "Keywords Score",
        "Matched Skills", "Missing Skills", "Strengths", "Gaps", "Explanation",
    ]
    ws.append(headers)

    # Style header row
    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)

    for e in entries:
        ws.append([
            e["rank"],
            e["candidate_name"],
            round(e["overall_score"], 1),
            e["fit_status"].title(),
            round(e["skills_score"]),
            round(e["experience_score"]),
            round(e["projects_score"]),
            round(e["keywords_score"]),
            "; ".join(e.get("matched_skills", [])),
            "; ".join(e.get("missing_skills", [])),
            "; ".join(e.get("strengths", [])),
            "; ".join(e.get("gaps", [])),
            e.get("explanation", ""),
        ])

    # Auto-width columns
    for col in ws.columns:
        max_length = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 50)

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def export_leaderboard_pdf(db: Session, jd_id: UUID) -> bytes:
    entries = get_leaderboard(db, jd_id)
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), topMargin=0.5 * inch)

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("CV Tracker - Candidate Leaderboard", styles["Title"]))
    elements.append(Spacer(1, 12))

    headers = ["Rank", "Candidate", "Score", "Fit", "Skills", "Exp", "Projects", "Keywords"]
    data = [headers]

    for e in entries:
        data.append([
            str(e["rank"]),
            e["candidate_name"][:30],
            f"{e['overall_score']:.1f}%",
            e["fit_status"].title(),
            f"{e['skills_score']:.0f}",
            f"{e['experience_score']:.0f}",
            f"{e['projects_score']:.0f}",
            f"{e['keywords_score']:.0f}",
        ])

    table = Table(data, repeatRows=1)

    fit_colors = {"Green": colors.lightgreen, "Yellow": colors.lightyellow, "Red": colors.pink}
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
    ]

    for i, e in enumerate(entries, 1):
        bg = fit_colors.get(e["fit_status"].title())
        if bg:
            style_cmds.append(("BACKGROUND", (3, i), (3, i), bg))

    table.setStyle(TableStyle(style_cmds))
    elements.append(table)

    doc.build(elements)
    return output.getvalue()
