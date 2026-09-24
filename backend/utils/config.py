import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent.parent
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
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
