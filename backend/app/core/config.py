import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
REPOSITORY_ROOT = BACKEND_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


def get_path_setting(name: str, default: Path) -> Path:
    value = os.getenv(name, "").strip()
    path = Path(value).expanduser() if value else default
    return path if path.is_absolute() else REPOSITORY_ROOT / path


UPLOADS_DIR = get_path_setting("UPLOADS_DIR", REPOSITORY_ROOT)
LOG_DIR = get_path_setting("LOG_DIR", REPOSITORY_ROOT)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
MAX_DOCUMENT_UPLOAD_BYTES = int(
    os.getenv(
        "MAX_DOCUMENT_UPLOAD_BYTES",
        os.getenv("MAX_PDF_UPLOAD_BYTES", str(20 * 1024 * 1024)),
    )
)
MAX_PDF_UPLOAD_BYTES = MAX_DOCUMENT_UPLOAD_BYTES
CORS_ALLOWED_ORIGINS = tuple(
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:4000,http://127.0.0.1:4000,http://localhost:4001,http://127.0.0.1:4001",
    ).split(",")
    if origin.strip()
)
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "12"))
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").strip().lower() == "true"
