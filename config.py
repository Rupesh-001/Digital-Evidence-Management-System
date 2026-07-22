import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-secret-key-xyz")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # MongoDB Atlas
    MONGO_URI = os.environ.get(
        "MONGO_URI",
        "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/evidencechain?retryWrites=true&w=majority"
    )
    MONGO_DBNAME = os.environ.get("MONGO_DBNAME", "evidencechain")

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-in-production-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_COOKIE_SECURE = True          # Set True in production (HTTPS)
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_CSRF_PROTECT = False

    # Sessions
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # File uploads
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    REPORTS_FOLDER = os.environ.get("REPORTS_FOLDER", "reports")
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024   # 500 MB
    ALLOWED_EXTENSIONS = {
        "images": {"png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff"},
        "videos": {"mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"},
        "documents": {"pdf", "doc", "docx", "xls", "xlsx", "txt", "csv", "odt", "ppt", "pptx"},
        "all": {"png","jpg","jpeg","gif","bmp","webp","tiff","mp4","avi","mov","mkv",
                "wmv","flv","webm","pdf","doc","docx","xls","xlsx","txt","csv","odt","ppt","pptx"},
    }

    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"

    # Roles
    ROLES = ["Administrator", "Investigator", "Forensic Analyst", "Officer"]
