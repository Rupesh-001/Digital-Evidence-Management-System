from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, abort, current_app)
from flask_login import login_required, current_user
from app.models.evidence import Case, Evidence, AuditLog
from app.models.user import User

cases_bp = Blueprint("cases", __name__, url_prefix="/cases")


def _db():
    return current_app.db

def _ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)


@cases_bp.route("/")
@login_required
def view_cases():
    db = _db()
    q        = request.args.get("q", "")
    status   = request.args.get("status", "")
    priority = request.args.get("priority", "")
    cases    = Case.search(db, q=q, status=status, priority=priority)
    ev_all   = Evidence.all(db)
    ev_count = {}
    for e in ev_all:
        ev_count[e["case_id"]] = ev_count.get(e["case_id"], 0) + 1
    return render_template("cases/view_cases.html",
                           cases=cases, ev_count=ev_count,
                           q=q, status=status, priority=priority)


@cases_bp.route("/<case_id>")
@login_required
def case_details(case_id):
    db   = _db()
    case = Case.get(db, case_id)
    if not case:
        abort(404)
    evidence = Evidence.by_case(db, case_id)
    AuditLog.log(_db(), current_user.name, current_user.id,
                 "CASE_VIEW", case_id, f"Viewed case {case['title']}", _ip(), "Cases")
    return render_template("cases/case_details.html", case=case, evidence=evidence)


@cases_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_case():
    if not current_user.can_manage_cases:
        flash("You do not have permission to create cases.", "error")
        return redirect(url_for("cases.view_cases"))

    db = _db()
    if request.method == "POST":
        title       = request.form.get("title", "").strip()
        case_type   = request.form.get("type", "Other")
        priority    = request.form.get("priority", "Medium")
        lead        = request.form.get("lead", current_user.name)
        location    = request.form.get("location", "")
        description = request.form.get("description", "")

        if not title:
            flash("Case title is required.", "error")
        else:
            c = Case.create(db, title, case_type, priority, lead, location,
                            description, current_user.id)
            AuditLog.log(db, current_user.name, current_user.id,
                         "CASE_CREATE", c["case_id"],
                         f"Created case {title}", _ip(), "Cases")
            flash(f"Case {c['case_id']} created successfully.", "success")
            return redirect(url_for("cases.case_details", case_id=c["case_id"]))

    users = [u for u in User.all(db) if u.status == "Active"]
    return render_template("cases/create_case.html", users=users)


@cases_bp.route("/<case_id>/edit", methods=["GET", "POST"])
@login_required
def edit_case(case_id):
    if not current_user.can_manage_cases:
        flash("You do not have permission to edit cases.", "error")
        return redirect(url_for("cases.view_cases"))

    db   = _db()
    case = Case.get(db, case_id)
    if not case:
        abort(404)

    if request.method == "POST":
        updates = {
            "title":       request.form.get("title", "").strip(),
            "type":        request.form.get("type", case["type"]),
            "status":      request.form.get("status", case["status"]),
            "priority":    request.form.get("priority", case["priority"]),
            "lead":        request.form.get("lead", case["lead"]),
            "location":    request.form.get("location", ""),
            "description": request.form.get("description", ""),
        }
        if not updates["title"]:
            flash("Case title is required.", "error")
        else:
            Case.update(db, case_id, **updates)
            AuditLog.log(db, current_user.name, current_user.id,
                         "CASE_UPDATE", case_id,
                         f"Updated case {updates['title']}", _ip(), "Cases")
            flash("Case updated.", "success")
            return redirect(url_for("cases.case_details", case_id=case_id))

    users = [u for u in User.all(db) if u.status == "Active"]
    return render_template("cases/edit_case.html", case=case, users=users)


@cases_bp.route("/<case_id>/delete", methods=["POST"])
@login_required
def delete_case(case_id):
    if not current_user.is_admin:
        flash("Only administrators can delete cases.", "error")
        return redirect(url_for("cases.view_cases"))

    db = _db()
    case = Case.get(db, case_id)
    if case:
        Case.delete(db, case_id)
        AuditLog.log(db, current_user.name, current_user.id,
                     "CASE_DELETE", case_id,
                     f"Deleted case {case['title']}", _ip(), "Cases")
        flash(f"Case {case_id} deleted.", "success")
    return redirect(url_for("cases.view_cases"))
