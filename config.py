import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env when running locally.
# On Render, the variables will come from Render Environment Variables.
load_dotenv()


class Config:

    # ============================================================
    # FLASK
    # ============================================================

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "development-secret-key-change-in-production"
    )

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600


    # ============================================================
    # MONGODB ATLAS
    # ============================================================

    MONGO_URI = os.environ.get("MONGO_URI")

    MONGO_DBNAME = os.environ.get(
        "MONGO_DBNAME",
        "evidencechain"
    )


    # ============================================================
    # JWT
    # ============================================================

    JWT_SECRET_KEY = os.environ.get(
        "JWT_SECRET_KEY",
        "development-jwt-secret-change-in-production"
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=8
    )

    JWT_COOKIE_SECURE = True

    JWT_TOKEN_LOCATION = [
        "headers",
        "cookies"
    ]

    JWT_COOKIE_CSRF_PROTECT = False


    # ============================================================
    # SESSIONS
    # ============================================================

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SECURE = True

    SESSION_COOKIE_SAMESITE = "Lax"

    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=8
    )


    # ============================================================
    # FILE UPLOADS
    # ============================================================

    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        "uploads"
    )

    REPORTS_FOLDER = os.environ.get(
        "REPORTS_FOLDER",
        "reports"
    )

    MAX_CONTENT_LENGTH = 500 * 1024 * 1024


    # ============================================================
    # ALLOWED FILE EXTENSIONS
    # ============================================================

    ALLOWED_EXTENSIONS = {

        "images": {
            "png",
            "jpg",
            "jpeg",
            "gif",
            "bmp",
            "webp",
            "tiff"
        },

        "videos": {
            "mp4",
            "avi",
            "mov",
            "mkv",
            "wmv",
            "flv",
            "webm"
        },

        "documents": {
            "pdf",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "txt",
            "csv",
            "odt",
            "ppt",
            "pptx"
        },

        "all": {
            "png",
            "jpg",
            "jpeg",
            "gif",
            "bmp",
            "webp",
            "tiff",

            "mp4",
            "avi",
            "mov",
            "mkv",
            "wmv",
            "flv",
            "webm",

            "pdf",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "txt",
            "csv",
            "odt",
            "ppt",
            "pptx"
        }
    }


    # ============================================================
    # RATE LIMITING
    # ============================================================

    RATELIMIT_DEFAULT = (
        "200 per day;"
        "50 per hour"
    )

    # Suitable for the current minor-project deployment.
    # For a larger production deployment, Redis can be used later.
    RATELIMIT_STORAGE_URI = "memory://"


    # ============================================================
    # ROLES
    # ============================================================

    ROLES = [
        "Administrator",
        "Investigator",
        "Forensic Analyst",
        "Officer"
    ]