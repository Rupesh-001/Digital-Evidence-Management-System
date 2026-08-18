"""JSON REST API — protected by JWT."""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.evidence import Case, Evidence, CustodyLog, AuditLog
from app.models.user import User

api_bp = Blueprint("api", __name__)


def _db():
    return current_app.db

def _serialize(doc):
    """Make a MongoDB doc JSON-serialisable."""
    if doc is None:
        return None
    d = dict(doc)
    d.pop("_id", None)
    for k, v in d.items():
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
    return d


@api_bp.route("/dashboard")
@jwt_required()
def api_dashboard():
    db = _db()
    cases    = Case.all(db)
    evidence = Evidence.all(db)
    custody  = CustodyLog.all(db)
    return jsonify({
        "total_cases":     len(cases),
        "open_cases":      sum(1 for c in cases if c["status"] in ("Open","Under Review")),
        "closed_cases":    sum(1 for c in cases if c["status"] == "Closed"),
        "total_evidence":  len(evidence),
        "verified":        sum(1 for e in evidence if e["status"] == "Verified"),
        "custody_records": len(custody),
    })


@api_bp.route("/cases")
@jwt_required()
def api_cases():
    db = _db()
    return jsonify([_serialize(c) for c in Case.all(db)])


@api_bp.route("/cases/<case_id>")
@jwt_required()
def api_case(case_id):
    db   = _db()
    case = Case.get(db, case_id)
    if not case:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_serialize(case))


@api_bp.route("/evidence")
@jwt_required()
def api_evidence():
    db = _db()
    return jsonify([_serialize(e) for e in Evidence.all(db)])


@api_bp.route("/evidence/<ev_id>")
@jwt_required()
def api_evidence_item(ev_id):
    db = _db()
    ev = Evidence.get(db, ev_id)
    if not ev:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_serialize(ev))


@api_bp.route("/custody")
@jwt_required()
def api_custody():
    db = _db()
    return jsonify([_serialize(l) for l in CustodyLog.all(db)])


@api_bp.route("/audit")
@jwt_required()
def api_audit():
    claims = get_jwt()
    if claims.get("role") != "Administrator":
        return jsonify({"error": "Administrators only"}), 403
    db = _db()
    return jsonify([_serialize(a) for a in AuditLog.all(db, limit=500)])
