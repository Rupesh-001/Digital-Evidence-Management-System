"""Evidence management blueprint."""
import os, hashlib
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, abort, current_app, send_from_directory, jsonify)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.evidence import Evidence, Case, CustodyLog, AuditLog

evidence_bp = Blueprint("evidence", __name__, url_prefix="/evidence")


def _db():
    return current_app.db

def _ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)

def _allowed(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]["all"]

def _sha256_stream(file_obj) -> str:
    h = hashlib.sha256()
    file_obj.seek(0)
    for chunk in iter(lambda: file_obj.read(65536), b""):
        h.update(chunk)
    file_obj.seek(0)
    return h.hexdigest()


@evidence_bp.route("/")
@login_required
def view_evidence():
    db   = _db()
    q        = request.args.get("q", "")
    ev_type  = request.args.get("type", "")
    status   = request.args.get("status", "")
    case_id  = request.args.get("case_id", "")
    items    = Evidence.search(db, q=q, ev_type=ev_type, status=status, case_id=case_id)
    cases    = Case.all(db)
    return render_template("evidence/view_evidence.html",
                           items=items, cases=cases,
                           q=q, ev_type=ev_type, status=status, case_id=case_id)


@evidence_bp.route("/<ev_id>")
@login_required
def evidence_details(ev_id):
    db  = _db()
    ev  = Evidence.get(db, ev_id)
    if not ev:
        abort(404)
    custody = CustodyLog.by_evidence(db, ev_id)
    case    = Case.get(db, ev["case_id"])
    AuditLog.log(db, current_user.name, current_user.id,
                 "EVIDENCE_VIEW", ev_id, f"Viewed evidence {ev['name']}", _ip(), "Evidence")
    return render_template("evidence/evidence_details.html",
                           ev=ev, custody=custody, case=case)


@evidence_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_evidence():
    if not current_user.can_upload_evidence:
        flash("You do not have permission to upload evidence.", "error")
        return redirect(url_for("evidence.view_evidence"))

    db = _db()
    if request.method == "POST":
        f        = request.files.get("file")
        name     = request.form.get("name", "").strip()
        ev_type  = request.form.get("type", "Document")
        case_id  = request.form.get("case_id", "")
        location = request.form.get("location", "")
        notes    = request.form.get("notes", "")

        if not f or f.filename == "":
            flash("No file selected.", "error")
        elif not _allowed(f.filename):
            flash("File type not allowed.", "error")
        elif not case_id:
            flash("Please select a case.", "error")
        else:
            filename  = secure_filename(f.filename)
            save_dir  = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(save_dir, exist_ok=True)
            filepath  = os.path.join(save_dir, filename)

            # Compute hash before saving (from stream)
            sha = _sha256_stream(f)
            f.save(filepath)
            size_bytes = os.path.getsize(filepath)
            size_str   = f"{size_bytes / (1024*1024):.2f} MB"

            ev = Evidence.create(
                db, case_id=case_id, name=name or filename,
                ev_type=ev_type, filepath=filepath, filename=filename,
                file_size=size_str, location=location, notes=notes,
                collected_by_id=current_user.id,
                collected_by_name=current_user.name,
            )
            # Use the hash we already computed
            Evidence.update(db, ev["evidence_id"], hash=sha)

            CustodyLog.add(db, ev["evidence_id"], "Collected", "Intake",
                           location or "Unassigned", current_user.id,
                           current_user.name, "Initial evidence intake & hashing",
                           location or "Intake")
            AuditLog.log(db, current_user.name, current_user.id,
                         "EVIDENCE_UPLOAD", ev["evidence_id"],
                         f"Uploaded {name} to {case_id}", _ip(), "Evidence")

            flash(f"Evidence {ev['evidence_id']} catalogued. SHA-256: {sha[:16]}…", "success")
            return redirect(url_for("evidence.evidence_details", ev_id=ev["evidence_id"]))

    cases = Case.all(db)
    preselect = request.args.get("case_id", "")
    return render_template("evidence/upload_evidence.html", cases=cases, preselect=preselect)


@evidence_bp.route("/<ev_id>/download")
@login_required
def download_evidence(ev_id):
    db = _db()
    ev = Evidence.get(db, ev_id)
    if not ev or not ev.get("filepath"):
        abort(404)
    CustodyLog.add(db, ev_id, "Downloaded", ev["location"], current_user.name,
                   current_user.id, current_user.name, "Evidence downloaded",
                   ev["location"])
    AuditLog.log(db, current_user.name, current_user.id,
                 "EVIDENCE_DOWNLOAD", ev_id, f"Downloaded {ev['name']}", _ip(), "Evidence")
    directory = os.path.dirname(ev["filepath"])
    filename  = os.path.basename(ev["filepath"])
    return send_from_directory(directory, filename, as_attachment=True)


@evidence_bp.route("/verify", methods=["GET", "POST"])
@login_required
def verify_hash():
    db     = _db()
    result = None
    all_ev = Evidence.all(db)

    if request.method == "POST":
        ev_id = request.form.get("ev_id", "")
        f     = request.files.get("file")

        if ev_id and f and f.filename:
            # Save temp file, compute hash
            tmp_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"_verify_{secure_filename(f.filename)}")
            f.save(tmp_path)
            match, stored, computed = Evidence.verify_hash(db, ev_id, tmp_path)
            os.remove(tmp_path)

            action = "HASH_VERIFY" if match else "HASH_MISMATCH"
            detail = f"Hash {'verified — match' if match else 'MISMATCH detected'}"
            CustodyLog.add(db, ev_id, "Verified", "Custodian",
                           Evidence.get(db, ev_id)["location"],
                           current_user.id, current_user.name,
                           f"Hash verification — {'match' if match else 'mismatch'}",
                           Evidence.get(db, ev_id)["location"],
                           "Verified" if match else "Compromised")
            AuditLog.log(db, current_user.name, current_user.id,
                         action, ev_id, detail, _ip(), "Evidence")
            result = {"match": match, "stored": stored, "computed": computed,
                      "ev": Evidence.get(db, ev_id)}
        elif request.form.get("hash_a") and request.form.get("hash_b"):
            a = request.form["hash_a"].strip().lower()
            b = request.form["hash_b"].strip().lower()
            result = {"manual": True, "match": a == b, "hash_a": a, "hash_b": b}

    return render_template("evidence/verify_hash.html", evidence=all_ev, result=result)


@evidence_bp.route("/<ev_id>/transfer", methods=["POST"])
@login_required
def transfer_evidence(ev_id):
    db = _db()
    ev = Evidence.get(db, ev_id)
    if not ev:
        abort(404)
    to_party = request.form.get("to_party", "").strip()
    reason   = request.form.get("reason", "").strip()
    location = request.form.get("location", ev["location"]).strip()
    if not to_party:
        flash("Recipient is required.", "error")
        return redirect(url_for("evidence.evidence_details", ev_id=ev_id))

    CustodyLog.add(db, ev_id, "Transferred", ev["location"], to_party,
                   current_user.id, current_user.name, reason or "Transfer", location)
    Evidence.update(db, ev_id, location=location)
    AuditLog.log(db, current_user.name, current_user.id,
                 "EVIDENCE_TRANSFER", ev_id,
                 f"Transferred to {to_party}", _ip(), "Evidence")
    flash(f"Evidence transferred to {to_party}.", "success")
    return redirect(url_for("evidence.evidence_details", ev_id=ev_id))
