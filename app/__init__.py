from flask import Flask
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from config import Config
import os

# Extensions (initialised without app)
login_manager = LoginManager()
jwt = JWTManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

# Global DB reference
mongo_client = None
db = None


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    # Ensure upload / reports folders exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["REPORTS_FOLDER"], exist_ok=True)

    # ── MongoDB ──────────────────────────────────────────────────
    global mongo_client, db
    mongo_client = MongoClient(app.config["MONGO_URI"])
    db = mongo_client[app.config["MONGO_DBNAME"]]
    app.db = db

    # Indexes for performance & uniqueness
    db.users.create_index("email", unique=True)
    db.cases.create_index("case_id", unique=True)
    db.evidence.create_index("evidence_id", unique=True)
    db.audit.create_index("timestamp")
    db.custody.create_index("evidence_id")

    # ── Extensions ───────────────────────────────────────────────
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to access this page."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # ── User loader ──────────────────────────────────────────────
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(db, user_id)

    # ── Blueprints ───────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.cases import cases_bp
    from app.routes.evidence import evidence_bp
    from app.routes.custody import custody_bp
    from app.routes.reports import reports_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(cases_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(custody_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ── Seed demo data if DB is empty ────────────────────────────
    from app.models.seeder import seed_demo_data
    if db.users.count_documents({}) == 0:
        seed_demo_data(db)

    return app
