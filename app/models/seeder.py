"""Seed demo data into a fresh MongoDB Atlas database."""
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.evidence import AuditLog
import random, string

def _dt(days_ago):
    return datetime.now(timezone.utc) - timedelta(days=days_ago)

def seed_demo_data(db):
    print("[seeder] Seeding demo data into MongoDB...")

    # ── Users ─────────────────────────────────────────────────────
    users_data = [
        ("Sarah Mitchell", "admin@dem.gov",      "admin123",    "Administrator",  "DET-1042"),
        ("James Okafor",   "j.okafor@dem.gov",   "invest123",   "Investigator",   "INV-2231"),
        ("Lena Park",      "l.park@dem.gov",      "tech123",     "Forensic Analyst","FA-7781"),
        ("Marco Reyes",    "m.reyes@dem.gov",     "officer123",  "Officer",        "OFF-5590"),
    ]
    user_ids = {}
    user_names = {}
    for name, email, pw, role, badge in users_data:
        status = "Suspended" if name == "Marco Reyes" else "Active"
        u = User.create(db, name, email, pw, role, badge, status)
        user_ids[name] = u.id
        user_names[name] = name

    admin_id   = user_ids["Sarah Mitchell"]
    inv_id     = user_ids["James Okafor"]
    analyst_id = user_ids["Lena Park"]
    officer_id = user_ids["Marco Reyes"]

    # ── Cases ─────────────────────────────────────────────────────
    cases = [
        {
            "case_id": "CASE-2024-0481",
            "title": "Riverside Warehouse Breach",
            "type": "Cyber Intrusion",
            "status": "Open",
            "priority": "High",
            "lead": "James Okafor",
            "description": "Unauthorized access to industrial control systems at the Riverside facility.",
            "location": "Riverside Industrial Park",
            "created": _dt(18),
            "created_by": inv_id,
            "updated": _dt(2),
        },
        {
            "case_id": "CASE-2024-0455",
            "title": "Operation Nightowl",
            "type": "Fraud",
            "status": "Open",
            "priority": "Critical",
            "lead": "Sarah Mitchell",
            "description": "Large-scale financial fraud involving falsified ledgers and offshore transfers.",
            "location": "Downtown Financial District",
            "created": _dt(32),
            "created_by": admin_id,
            "updated": _dt(5),
        },
        {
            "case_id": "CASE-2024-0399",
            "title": "Maple Street Robbery",
            "type": "Theft",
            "status": "Under Review",
            "priority": "Medium",
            "lead": "James Okafor",
            "description": "Armed robbery with recovered CCTV footage and a seized mobile device.",
            "location": "412 Maple Street",
            "created": _dt(55),
            "created_by": inv_id,
            "updated": _dt(10),
        },
        {
            "case_id": "CASE-2024-0287",
            "title": "Harbor Smuggling Ring",
            "type": "Contraband",
            "status": "Closed",
            "priority": "High",
            "lead": "Sarah Mitchell",
            "description": "Coordinated smuggling operation. All evidence catalogued and archived.",
            "location": "Harbor Terminal 3",
            "created": _dt(110),
            "created_by": admin_id,
            "updated": _dt(30),
        },
    ]
    db.cases.insert_many(cases)

    # ── Evidence ──────────────────────────────────────────────────
    evidence = [
        {
            "evidence_id": "EV-100231",
            "case_id": "CASE-2024-0481",
            "name": "Seized Laptop — Dell Latitude",
            "type": "Digital Device",
            "status": "In Analysis",
            "hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            "filename": "laptop_image.bin",
            "filepath": "",
            "file_size": "512 GB",
            "location": "Evidence Locker A-12",
            "notes": "Encrypted volume detected on drive.",
            "collected_by_id": analyst_id,
            "collected_by": "Lena Park",
            "collected_at": _dt(17),
            "integrity_verified_at": None,
        },
        {
            "evidence_id": "EV-100232",
            "case_id": "CASE-2024-0481",
            "name": "USB Flash Drive (Black)",
            "type": "Storage Media",
            "status": "Secured",
            "hash": "ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d",
            "filename": "usb_image.bin",
            "filepath": "",
            "file_size": "64 GB",
            "location": "Evidence Locker A-12",
            "notes": "Recovered from suspect's desk drawer.",
            "collected_by_id": analyst_id,
            "collected_by": "Lena Park",
            "collected_at": _dt(17),
            "integrity_verified_at": None,
        },
        {
            "evidence_id": "EV-100210",
            "case_id": "CASE-2024-0455",
            "name": "Financial Ledger Scan (PDF)",
            "type": "Document",
            "status": "Verified",
            "hash": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
            "filename": "ledger_scan.pdf",
            "filepath": "",
            "file_size": "14 MB",
            "location": "Digital Vault",
            "notes": "Original document secured; working copy hashed.",
            "collected_by_id": inv_id,
            "collected_by": "James Okafor",
            "collected_at": _dt(31),
            "integrity_verified_at": _dt(30),
        },
        {
            "evidence_id": "EV-100188",
            "case_id": "CASE-2024-0399",
            "name": "CCTV Footage — Front Entrance",
            "type": "Video",
            "status": "Verified",
            "hash": "fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
            "filename": "cctv_front.mp4",
            "filepath": "",
            "file_size": "2.3 GB",
            "location": "Digital Vault",
            "notes": "8-hour continuous recording.",
            "collected_by_id": officer_id,
            "collected_by": "Marco Reyes",
            "collected_at": _dt(54),
            "integrity_verified_at": _dt(53),
        },
        {
            "evidence_id": "EV-100189",
            "case_id": "CASE-2024-0399",
            "name": "Suspect Mobile Phone",
            "type": "Digital Device",
            "status": "In Analysis",
            "hash": "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4",
            "filename": "phone_dump.bin",
            "filepath": "",
            "file_size": "128 GB",
            "location": "Evidence Locker B-04",
            "notes": "PIN-locked; extraction in progress.",
            "collected_by_id": analyst_id,
            "collected_by": "Lena Park",
            "collected_at": _dt(53),
            "integrity_verified_at": None,
        },
    ]
    db.evidence.insert_many(evidence)

    # ── Custody Logs ──────────────────────────────────────────────
    import random as rnd
    def cust_id():
        return "CUST-" + "".join(rnd.choices(string.digits, k=6))

    custody = [
        {"custody_id": cust_id(), "evidence_id": "EV-100231", "action": "Collected",   "from_party": "Crime Scene",        "to_party": "Lena Park",          "handler_id": analyst_id, "handler": "Lena Park",    "reason": "Initial seizure at scene",          "location": "Riverside Industrial Park", "integrity": "Verified", "timestamp": _dt(17)},
        {"custody_id": cust_id(), "evidence_id": "EV-100231", "action": "Transferred", "from_party": "Lena Park",          "to_party": "Evidence Locker A-12","handler_id": analyst_id, "handler": "Lena Park",    "reason": "Secured storage",                   "location": "Evidence Locker A-12",     "integrity": "Verified", "timestamp": _dt(16)},
        {"custody_id": cust_id(), "evidence_id": "EV-100231", "action": "Checked Out", "from_party": "Evidence Locker A-12","to_party": "Forensic Lab",       "handler_id": analyst_id, "handler": "Lena Park",    "reason": "Forensic imaging",                  "location": "Forensic Lab 2",           "integrity": "Verified", "timestamp": _dt(10)},
        {"custody_id": cust_id(), "evidence_id": "EV-100210", "action": "Collected",   "from_party": "Field",              "to_party": "James Okafor",       "handler_id": inv_id,     "handler": "James Okafor", "reason": "Document seizure",                  "location": "Downtown Financial District","integrity": "Verified", "timestamp": _dt(31)},
        {"custody_id": cust_id(), "evidence_id": "EV-100210", "action": "Verified",    "from_party": "James Okafor",       "to_party": "Digital Vault",      "handler_id": admin_id,   "handler": "Sarah Mitchell","reason": "Hash verification & archival",      "location": "Digital Vault",            "integrity": "Verified", "timestamp": _dt(30)},
        {"custody_id": cust_id(), "evidence_id": "EV-100188", "action": "Collected",   "from_party": "Crime Scene",        "to_party": "Marco Reyes",        "handler_id": officer_id, "handler": "Marco Reyes",  "reason": "CCTV export",                       "location": "412 Maple Street",         "integrity": "Verified", "timestamp": _dt(54)},
    ]
    db.custody.insert_many(custody)

    # ── Audit Logs ────────────────────────────────────────────────
    audits = [
        {"audit_id": "AUD-001", "actor": "Sarah Mitchell", "actor_id": admin_id,   "action": "LOGIN",           "target": "System",        "detail": "Administrator signed in",         "module": "Auth",     "ip": "10.0.4.21", "timestamp": _dt(0)},
        {"audit_id": "AUD-002", "actor": "Lena Park",      "actor_id": analyst_id, "action": "EVIDENCE_UPLOAD", "target": "EV-100231",     "detail": "Uploaded Seized Laptop image",     "module": "Evidence", "ip": "10.0.4.55", "timestamp": _dt(17)},
        {"audit_id": "AUD-003", "actor": "James Okafor",   "actor_id": inv_id,     "action": "CASE_CREATE",     "target": "CASE-2024-0481","detail": "Created Riverside Warehouse Breach","module": "Cases",    "ip": "10.0.4.33", "timestamp": _dt(18)},
        {"audit_id": "AUD-004", "actor": "Sarah Mitchell", "actor_id": admin_id,   "action": "HASH_VERIFY",     "target": "EV-100210",     "detail": "Hash verified — match",            "module": "Evidence", "ip": "10.0.4.21", "timestamp": _dt(30)},
    ]
    db.audit.insert_many(audits)

    print("[seeder] Demo data seeded successfully.")
