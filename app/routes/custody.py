"""Custody logs blueprint."""
from flask import Blueprint, render_template, current_app, request
from flask_login import login_required, current_user
from app.models.evidence import CustodyLog, Evidence

custody_bp = Blueprint("custody", __name__, url_prefix="/custody")

def _db():
    return current_app.db

@custody_bp.route("/")
@login_required
def custody_logs():
    db     = _db()
    q      = request.args.get("q", "")
    action = request.args.get("action", "")
    logs   = CustodyLog.search(db, q=q, action=action)
    ev_map = {e["evidence_id"]: e for e in Evidence.all(db)}
    for log in logs:
        log["_evidence"] = ev_map.get(log["evidence_id"], {})
    return render_template("custody/custody_logs.html", logs=logs, q=q, action=action)
