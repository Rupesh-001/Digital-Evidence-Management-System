from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from app.models.evidence import Case, Evidence, CustodyLog, AuditLog

dashboard_bp = Blueprint("dashboard", __name__)


def _db():
    return current_app.db


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    db = _db()
    cases    = Case.all(db)
    evidence = Evidence.all(db)
    custody  = CustodyLog.all(db)
    audits   = AuditLog.all(db, limit=10)

    from app.models.user import User
    users = User.all(db)

    stats = {
        "total_cases":    len(cases),
        "open_cases":     sum(1 for c in cases if c["status"] in ("Open", "Under Review")),
        "closed_cases":   sum(1 for c in cases if c["status"] == "Closed"),
        "total_evidence": len(evidence),
        "verified":       sum(1 for e in evidence if e["status"] == "Verified"),
        "in_analysis":    sum(1 for e in evidence if e["status"] == "In Analysis"),
        "total_users":    len(users),
        "custody_records":len(custody),
    }

    recent_cases   = cases[:5]
    recent_custody = custody[:6]

    # Enrich custody with evidence names
    ev_map = {e["evidence_id"]: e for e in evidence}
    for c in recent_custody:
        c["_evidence"] = ev_map.get(c["evidence_id"], {})

    return render_template("dashboard.html",
                           stats=stats,
                           recent_cases=recent_cases,
                           recent_custody=recent_custody,
                           recent_audits=audits)
