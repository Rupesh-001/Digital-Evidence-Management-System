"""Reports blueprint — HTML views + PDF/Excel export."""
import io, os
from datetime import datetime, timezone
from flask import (Blueprint, render_template, current_app, request,
                   abort, send_file, redirect, url_for)
from flask_login import login_required, current_user
from app.models.evidence import Case, Evidence, CustodyLog, AuditLog

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _db():
    return current_app.db


@reports_bp.route("/")
@login_required
def generate_report():
    db    = _db()
    cases = Case.all(db)
    evs   = Evidence.all(db)
    return render_template("reports/generate_report.html", cases=cases, evidence=evs)


@reports_bp.route("/case/<case_id>")
@login_required
def case_report(case_id):
    db   = _db()
    case = Case.get(db, case_id)
    if not case:
        abort(404)
    evidence = Evidence.by_case(db, case_id)
    return render_template("reports/case_report.html", case=case, evidence=evidence)


@reports_bp.route("/evidence/<ev_id>")
@login_required
def evidence_report(ev_id):
    db  = _db()
    ev  = Evidence.get(db, ev_id)
    if not ev:
        abort(404)
    custody = CustodyLog.by_evidence(db, ev_id)
    case    = Case.get(db, ev["case_id"])
    return render_template("reports/evidence_report.html", ev=ev, custody=custody, case=case)


@reports_bp.route("/custody")
@login_required
def custody_report():
    db  = _db()
    ev_id = request.args.get("ev_id", "")
    ev    = Evidence.get(db, ev_id) if ev_id else None
    logs  = CustodyLog.by_evidence(db, ev_id) if ev_id else CustodyLog.all(db)
    evs   = Evidence.all(db)
    return render_template("reports/custody_report.html",
                           ev=ev, logs=logs, evidence=evs, ev_id=ev_id)


@reports_bp.route("/audit")
@login_required
def audit_report():
    db     = _db()
    audits = AuditLog.all(db, limit=1000)
    return render_template("reports/audit_report.html", audits=audits)


# ── PDF Export ────────────────────────────────────────────────────────────────

@reports_bp.route("/export/pdf/<report_type>")
@login_required
def export_pdf(report_type):
    db = _db()
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                        Paragraph, Spacer)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
    except ImportError:
        abort(500, "ReportLab not installed.")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    elements = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def add_title(text, sub=""):
        elements.append(
            Paragraph(
                "<b>EvidenceChain</b>",
                ParagraphStyle(
                    "brand",
                    parent=styles["Heading1"],
                    fontSize=24,
                    textColor=colors.HexColor("#0f172a"),
                    alignment=1
                )
            )
        )

        elements.append(
            Paragraph(
                text,
                ParagraphStyle(
                    "title",
                    parent=styles["Heading2"],
                    fontSize=16,
                    textColor=colors.HexColor("#2563eb"),
                    alignment=1
                )
            )
        )

        if sub:
            elements.append(
                Paragraph(
                    sub,
                    ParagraphStyle(
                        "sub",
                        parent=styles["Normal"],
                        fontSize=9,
                        textColor=colors.grey,
                        alignment=1
                    )
                )
            )

        elements.append(Spacer(1, 0.8 * cm))

    def add_table(headers, rows, col_widths=None):
        data = [headers] + rows

        table = Table(
            data,
            colWidths=col_widths,
            repeatRows=1
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0),
             colors.HexColor("#0f172a")),

            ("TEXTCOLOR", (0, 0), (-1, 0),
             colors.white),

            ("FONTNAME", (0, 0), (-1, 0),
             "Helvetica-Bold"),

            ("FONTSIZE", (0, 0), (-1, -1),
             9),

            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f8fafc")]),

            ("GRID", (0, 0), (-1, -1),
             0.5,
             colors.HexColor("#d1d5db")),

            ("VALIGN", (0, 0), (-1, -1),
             "TOP"),

            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.7 * cm))

    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(
            2 * cm,
            1 * cm,
            "EvidenceChain Digital Evidence Management System"
        )
        canvas.drawRightString(
            19 * cm,
            1 * cm,
            f"Generated: {now_str}"
        )
        canvas.restoreState()

    if report_type == "cases":
        add_title("Digital Case Report", f"Generated on {now_str} by {current_user.name}")
        cases = Case.all(db)
        add_table(
            ["Case ID", "Title", "Type", "Status", "Priority", "Lead"],
            [[c["case_id"], c["title"][:40], c["type"], c["status"], c["priority"], c["lead"]]
             for c in cases],
        )

    elif report_type == "evidence":
        add_title("Digital Evidence Report", f"Generated on {now_str} by {current_user.name}")
        evs = Evidence.all(db)
        add_table(
            ["Evidence ID", "Name", "Type", "Case", "Status", "Collected By"],
            [[e["evidence_id"], e["name"][:35], e["type"], e["case_id"],
              e["status"], e["collected_by"]] for e in evs],
        )

    elif report_type == "audit":
        add_title("System Audit Report", f"Generated on {now_str} by {current_user.name}")
        audits = AuditLog.all(db, limit=500)
        add_table(
            ["Timestamp", "Actor", "Action", "Target", "Detail"],
            [[str(a["timestamp"])[:16], a["actor"], a["action"],
              a["target"][:20], a["detail"][:45]] for a in audits],
        )

    elif report_type == "custody":
        add_title("Chain of Custody Report", f"Generated on {now_str} by {current_user.name}")
        logs = CustodyLog.all(db)
        add_table(
            ["Timestamp", "Evidence ID", "Action", "From", "To", "Handler"],
            [[str(l["timestamp"])[:16], l["evidence_id"], l["action"],
              l["from_party"][:20], l["to_party"][:20], l["handler"]] for l in logs],
        )
    else:
        abort(404)

    doc.build(
        elements,
        onFirstPage=add_footer,
        onLaterPages=add_footer
    )
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf",
                     download_name=f"evidencechain_{report_type}_{now_str[:10]}.pdf",
                     as_attachment=True)


# ── Excel Export ──────────────────────────────────────────────────────────────

@reports_bp.route("/export/excel/<report_type>")
@login_required
def export_excel(report_type):
    db = _db()
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        abort(500, "openpyxl not installed.")

    wb = openpyxl.Workbook()
    ws = wb.active

    header_font  = Font(bold=True, color="FFFFFF")
    header_fill  = PatternFill("solid", fgColor="2563EB")
    header_align = Alignment(horizontal="center")

    def set_headers(cols):
        ws.append(cols)
        for cell in ws[1]:
            cell.font  = header_font
            cell.fill  = header_fill
            cell.alignment = header_align

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if report_type == "cases":
        ws.title = "Cases"
        set_headers(["Case ID","Title","Type","Status","Priority","Lead","Location","Created"])
        for c in Case.all(db):
            ws.append([c["case_id"], c["title"], c["type"], c["status"],
                        c["priority"], c["lead"], c.get("location",""),
                        str(c["created"])[:16]])

    elif report_type == "evidence":
        ws.title = "Evidence"
        set_headers(["Evidence ID","Name","Type","Case ID","Status","Hash","Collected By","Date"])
        for e in Evidence.all(db):
            ws.append([e["evidence_id"], e["name"], e["type"], e["case_id"],
                        e["status"], e["hash"], e["collected_by"],
                        str(e["collected_at"])[:16]])

    elif report_type == "audit":
        ws.title = "Audit Log"
        set_headers(["Timestamp","Actor","Action","Module","Target","Detail","IP"])
        for a in AuditLog.all(db, limit=5000):
            ws.append([str(a["timestamp"])[:19], a["actor"], a["action"],
                        a.get("module",""), a["target"], a["detail"], a.get("ip","")])

    elif report_type == "custody":
        ws.title = "Chain of Custody"
        set_headers(["Timestamp","Evidence ID","Action","From","To","Handler","Reason","Integrity"])
        for l in CustodyLog.all(db):
            ws.append([str(l["timestamp"])[:19], l["evidence_id"], l["action"],
                        l["from_party"], l["to_party"], l["handler"],
                        l.get("reason",""), l.get("integrity","")])
    else:
        abort(404)

    # Auto-width
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     download_name=f"evidencechain_{report_type}_{now_str[:10]}.xlsx",
                     as_attachment=True)