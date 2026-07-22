from flask_login import UserMixin
from bson import ObjectId
import bcrypt
from datetime import datetime, timezone


class User(UserMixin):
    """Wraps a MongoDB user document for Flask-Login."""

    def __init__(self, doc):
        self._doc = doc

    # ── Flask-Login required ─────────────────────────────────────
    def get_id(self):
        return str(self._doc["_id"])

    @property
    def is_active(self):
        return self._doc.get("status", "Active") == "Active"

    # ── Convenience accessors ────────────────────────────────────
    @property
    def id(self):
        return str(self._doc["_id"])

    @property
    def name(self):
        return self._doc.get("name", "")

    @property
    def email(self):
        return self._doc.get("email", "")

    @property
    def role(self):
        return self._doc.get("role", "Officer")

    @property
    def badge(self):
        return self._doc.get("badge", "—")

    @property
    def status(self):
        return self._doc.get("status", "Active")

    @property
    def created(self):
        return self._doc.get("created", datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "badge": self.badge,
            "status": self.status,
            "created": self.created.isoformat() if hasattr(self.created, "isoformat") else str(self.created),
        }

    # ── Password helpers ─────────────────────────────────────────
    @staticmethod
    def hash_password(plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    def check_password(self, plain: str) -> bool:
        stored = self._doc.get("password_hash", "")
        try:
            return bcrypt.checkpw(plain.encode(), stored.encode())
        except Exception:
            return False

    # ── DB queries ───────────────────────────────────────────────
    @classmethod
    def get_by_id(cls, db, user_id: str):
        try:
            doc = db.users.find_one({"_id": ObjectId(user_id)})
            return cls(doc) if doc else None
        except Exception:
            return None

    @classmethod
    def get_by_email(cls, db, email: str):
        doc = db.users.find_one({"email": email.lower().strip()})
        return cls(doc) if doc else None

    @classmethod
    def create(cls, db, name, email, password, role, badge="—", status="Active"):
        doc = {
            "name": name.strip(),
            "email": email.lower().strip(),
            "password_hash": cls.hash_password(password),
            "role": role,
            "badge": badge.strip() or "—",
            "status": status,
            "created": datetime.now(timezone.utc),
        }
        result = db.users.insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls(doc)

    @classmethod
    def all(cls, db):
        return [cls(d) for d in db.users.find().sort("name", 1)]

    def update(self, db, **kwargs):
        if "password" in kwargs:
            kwargs["password_hash"] = self.hash_password(kwargs.pop("password"))
        if "email" in kwargs:
            kwargs["email"] = kwargs["email"].lower().strip()
        db.users.update_one({"_id": ObjectId(self.id)}, {"$set": kwargs})
        self._doc.update(kwargs)

    def delete(self, db):
        db.users.delete_one({"_id": ObjectId(self.id)})

    # ── RBAC helpers ─────────────────────────────────────────────
    @property
    def is_admin(self):
        return self.role == "Administrator"

    @property
    def can_manage_cases(self):
        return self.role in ("Administrator", "Investigator")

    @property
    def can_upload_evidence(self):
        return self.role in ("Administrator", "Investigator", "Forensic Analyst")

    @property
    def can_verify_hash(self):
        return self.role in ("Administrator", "Investigator", "Forensic Analyst")
