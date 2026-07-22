"""
models/evidence.py  — Case, Evidence, CustodyLog, AuditLog
All operations go through MongoDB Atlas via PyMongo.
"""
from bson import ObjectId
from datetime import datetime, timezone
import hashlib, os, random, string


# ── Helpers ──────────────────────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc)

def _uid(prefix, db_col=None):
    """Generate a unique-ish human-readable ID."""
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{prefix}-{rand}"

def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Case ─────────────────────────────────────────────────────────────────────

class Case:
    COL = "cases"

    @staticmethod
    def create(db, title, case_type, priority, lead, location, description, created_by_id):
        year = datetime.now().year
        rand4 = "".join(random.choices(string.digits, k=4))
        case_id = f"CASE-{year}-{rand4}"
        doc = {
            "case_id": case_id,
            "title": title.strip(),
            "type": case_type,
            "status": "Open",
            "priority": priority,
            "lead": lead,
            "location": location.strip(),
            "description": description.strip(),
            "created": _now(),
            "created_by": created_by_id,
            "updated": _now(),
        }
        db[Case.COL].insert_one(doc)
        return doc

    @staticmethod
    def all(db, filters=None):
        query = filters or {}
        return list(db[Case.COL].find(query).sort("created", -1))

    @staticmethod
    def get(db, case_id: str):
        return db[Case.COL].find_one({"case_id": case_id})

    @staticmethod
    def update(db, case_id: str, **kwargs):
        kwargs["updated"] = _now()
        db[Case.COL].update_one({"case_id": case_id}, {"$set": kwargs})

    @staticmethod
    def delete(db, case_id: str):
        db[Case.COL].delete_one({"case_id": case_id})

    @staticmethod
    def search(db, q="", status="", priority=""):
        query = {}
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if q:
            query["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"case_id": {"$regex": q, "$options": "i"}},
                {"lead": {"$regex": q, "$options": "i"}},
                {"type": {"$regex": q, "$options": "i"}},
            ]
        return list(db[Case.COL].find(query).sort("created", -1))


# ── Evidence ─────────────────────────────────────────────────────────────────

class Evidence:
    COL = "evidence"

    @staticmethod
    def create(db, case_id, name, ev_type, filepath, filename, file_size,
               location, notes, collected_by_id, collected_by_name):
        ev_id = "EV-" + "".join(random.choices(string.digits, k=6))
        sha = sha256_file(filepath)
        doc = {
            "evidence_id": ev_id,
            "case_id": case_id,
            "name": name.strip(),
            "type": ev_type,
            "status": "Secured",
            "hash": sha,
            "filename": filename,
            "filepath": filepath,
            "file_size": file_size,
            "location": location.strip() or "Unassigned",
            "notes": notes.strip(),
            "collected_by_id": collected_by_id,
            "collected_by": collected_by_name,
            "collected_at": _now(),
            "integrity_verified_at": None,
        }
        db[Evidence.COL].insert_one(doc)
        return doc

    @staticmethod
    def all(db, filters=None):
        return list(db[Evidence.COL].find(filters or {}).sort("collected_at", -1))

    @staticmethod
    def get(db, ev_id: str):
        return db[Evidence.COL].find_one({"evidence_id": ev_id})

    @staticmethod
    def update(db, ev_id: str, **kwargs):
        db[Evidence.COL].update_one({"evidence_id": ev_id}, {"$set": kwargs})

    @staticmethod
    def delete(db, ev_id: str):
        db[Evidence.COL].delete_one({"evidence_id": ev_id})

    @staticmethod
    def by_case(db, case_id: str):
        return list(db[Evidence.COL].find({"case_id": case_id}).sort("collected_at", -1))

    @staticmethod
    def search(db, q="", ev_type="", status="", case_id=""):
        query = {}
        if ev_type:
            query["type"] = ev_type
        if status:
            query["status"] = status
        if case_id:
            query["case_id"] = case_id
        if q:
            query["$or"] = [
                {"evidence_id": {"$regex": q, "$options": "i"}},
                {"name": {"$regex": q, "$options": "i"}},
                {"case_id": {"$regex": q, "$options": "i"}},
                {"collected_by": {"$regex": q, "$options": "i"}},
            ]
        return list(db[Evidence.COL].find(query).sort("collected_at", -1))

    @staticmethod
    def verify_hash(db, ev_id: str, uploaded_filepath: str):
        """Returns (match: bool, stored_hash: str, computed_hash: str)."""
        ev = Evidence.get(db, ev_id)
        if not ev:
            return False, None, None
        computed = sha256_file(uploaded_filepath)
        stored = ev["hash"]
        match = computed.lower() == stored.lower()
        new_status = "Verified" if match else "Compromised"
        Evidence.update(db, ev_id, status=new_status, integrity_verified_at=_now())
        return match, stored, computed


# ── Custody Log ──────────────────────────────────────────────────────────────

class CustodyLog:
    COL = "custody"

    @staticmethod
    def add(db, evidence_id, action, from_party, to_party, handler_id,
            handler_name, reason, location, integrity="Verified"):
        cust_id = "CUST-" + "".join(random.choices(string.digits, k=6))
        doc = {
            "custody_id": cust_id,
            "evidence_id": evidence_id,
            "action": action,
            "from_party": from_party,
            "to_party": to_party,
            "handler_id": handler_id,
            "handler": handler_name,
            "reason": reason,
            "location": location,
            "integrity": integrity,
            "timestamp": _now(),
        }
        db[CustodyLog.COL].insert_one(doc)
        return doc

    @staticmethod
    def all(db, filters=None):
        return list(db[CustodyLog.COL].find(filters or {}).sort("timestamp", -1))

    @staticmethod
    def by_evidence(db, ev_id: str):
        return list(db[CustodyLog.COL].find({"evidence_id": ev_id}).sort("timestamp", 1))

    @staticmethod
    def search(db, q="", action=""):
        query = {}
        if action:
            query["action"] = action
        if q:
            query["$or"] = [
                {"evidence_id": {"$regex": q, "$options": "i"}},
                {"handler": {"$regex": q, "$options": "i"}},
                {"from_party": {"$regex": q, "$options": "i"}},
                {"to_party": {"$regex": q, "$options": "i"}},
            ]
        return list(db[CustodyLog.COL].find(query).sort("timestamp", -1))


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLog:
    COL = "audit"

    @staticmethod
    def log(db, actor_name, actor_id, action, target, detail, ip="—", module="System"):
        doc = {
            "audit_id": "AUD-" + "".join(random.choices(string.digits, k=6)),
            "actor": actor_name,
            "actor_id": actor_id,
            "action": action,
            "target": target,
            "detail": detail,
            "module": module,
            "ip": ip,
            "timestamp": _now(),
        }
        db[AuditLog.COL].insert_one(doc)
        return doc

    @staticmethod
    def all(db, filters=None, limit=500):
        return list(db[AuditLog.COL].find(filters or {}).sort("timestamp", -1).limit(limit))

    @staticmethod
    def search(db, q="", action=""):
        query = {}
        if action:
            query["action"] = action
        if q:
            query["$or"] = [
                {"actor": {"$regex": q, "$options": "i"}},
                {"target": {"$regex": q, "$options": "i"}},
                {"detail": {"$regex": q, "$options": "i"}},
            ]
        return list(db[AuditLog.COL].find(query).sort("timestamp", -1).limit(500))

    @staticmethod
    def distinct_actions(db):
        return sorted(db[AuditLog.COL].distinct("action"))
