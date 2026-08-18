"""Authentication blueprint — login, register, logout."""
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, current_app, session)
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token
from app.models.user import User
from app.models.evidence import AuditLog

auth_bp = Blueprint("auth", __name__)


def _db():
    return current_app.db


def _ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.get_by_email(_db(), email)
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html")

        if user.status != "Active":
            flash("This account is suspended. Contact an administrator.", "error")
            return render_template("auth/login.html")

        login_user(user, remember=True)
        AuditLog.log(_db(), user.name, user.id, "LOGIN", "System",
                     f"{user.role} signed in", _ip(), "Auth")

        next_page = request.args.get("next")
        return redirect(next_page or url_for("dashboard.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        badge = request.form.get("badge", "").strip()
        role = request.form.get("role", "Officer")

        if not name or not email or not password:
            flash("Name, email, and password are required.", "error")
            return render_template("auth/register.html", roles=current_app.config["ROLES"])

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("auth/register.html", roles=current_app.config["ROLES"])

        if User.get_by_email(_db(), email):
            flash("An account with that email already exists.", "error")
            return render_template("auth/register.html", roles=current_app.config["ROLES"])

        if role not in current_app.config["ROLES"]:
            role = "Officer"

        user = User.create(_db(), name, email, password, role, badge)
        AuditLog.log(_db(), user.name, user.id, "USER_REGISTER", user.id,
                     f"New {role} account registered", _ip(), "Auth")

        flash("Account created! Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", roles=current_app.config["ROLES"])


@auth_bp.route("/logout")
@login_required
def logout():
    AuditLog.log(_db(), current_user.name, current_user.id, "LOGOUT", "System",
                 "User signed out", _ip(), "Auth")
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/api/token", methods=["POST"])
def api_token():
    """Return a JWT for API / programmatic access."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    user = User.get_by_email(_db(), email)
    if not user or not user.check_password(password) or user.status != "Active":
        return {"error": "Invalid credentials"}, 401
    token = create_access_token(identity=user.id,
                                additional_claims={"role": user.role, "name": user.name})
    return {"access_token": token, "token_type": "Bearer"}
