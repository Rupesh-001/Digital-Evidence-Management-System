"""Admin blueprint — user management, audit logs."""
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, abort, current_app)
from flask_login import login_required, current_user
from app.models.user import User
from app.models.evidence import AuditLog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _db():
    return current_app.db

def _ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)

def _require_admin():
    if not current_user.is_admin:
        abort(403)


@admin_bp.route("/users")
@login_required
def users():
    _require_admin()
    db     = _db()
    q      = request.args.get("q", "")
    role   = request.args.get("role", "")
    all_u  = User.all(db)
    if role:
        all_u = [u for u in all_u if u.role == role]
    if q:
        ql = q.lower()
        all_u = [u for u in all_u if ql in u.name.lower() or ql in u.email.lower()]
    return render_template("admin/users.html",
                           users=all_u, q=q, role=role,
                           roles=current_app.config["ROLES"])


@admin_bp.route("/users/create", methods=["POST"])
@login_required
def create_user():
    _require_admin()
    db       = _db()
    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip() or "changeme123"
    badge    = request.form.get("badge", "").strip()
    role     = request.form.get("role", "Officer")
    status   = request.form.get("status", "Active")

    if not name or not email:
        flash("Name and email are required.", "error")
    elif User.get_by_email(db, email):
        flash("Email already in use.", "error")
    else:
        u = User.create(db, name, email, password, role, badge, status)
        AuditLog.log(db, current_user.name, current_user.id,
                     "USER_CREATE", u.id, f"Created user {name}", _ip(), "Admin")
        flash(f"User {name} created.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<user_id>/edit", methods=["POST"])
@login_required
def edit_user(user_id):
    _require_admin()
    db   = _db()
    user = User.get_by_id(db, user_id)
    if not user:
        abort(404)
    updates = {
        "name":   request.form.get("name", user.name).strip(),
        "badge":  request.form.get("badge", user.badge).strip(),
        "role":   request.form.get("role", user.role),
        "status": request.form.get("status", user.status),
    }
    new_pw = request.form.get("password", "").strip()
    if new_pw:
        updates["password"] = new_pw
    user.update(db, **updates)
    AuditLog.log(db, current_user.name, current_user.id,
                 "USER_UPDATE", user_id, f"Updated user {user.name}", _ip(), "Admin")
    flash(f"User {user.name} updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<user_id>/toggle", methods=["POST"])
@login_required
def toggle_user(user_id):
    _require_admin()
    db   = _db()
    user = User.get_by_id(db, user_id)
    if not user or user.id == current_user.id:
        abort(400)
    new_status = "Active" if user.status == "Suspended" else "Suspended"
    user.update(db, status=new_status)
    AuditLog.log(db, current_user.name, current_user.id,
                 "USER_STATUS", user_id,
                 f"{user.name} set to {new_status}", _ip(), "Admin")
    flash(f"{user.name} is now {new_status}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    _require_admin()
    db   = _db()
    user = User.get_by_id(db, user_id)
    if not user or user.id == current_user.id:
        abort(400)
    name = user.name
    user.delete(db)
    AuditLog.log(db, current_user.name, current_user.id,
                 "USER_DELETE", user_id, f"Deleted user {name}", _ip(), "Admin")
    flash(f"User {name} removed.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/audit")
@login_required
def audit_logs():
    _require_admin()
    db     = _db()
    q      = request.args.get("q", "")
    action = request.args.get("action", "")
    logs   = AuditLog.search(db, q=q, action=action)
    actions = AuditLog.distinct_actions(db)
    return render_template("admin/audit_logs.html",
                           logs=logs, q=q, action=action, actions=actions)
