from datetime import datetime
from utils.config import LOG_DIR

LOG_FILE = LOG_DIR / "server_events.log"


def log_event(user: str, event_type: str, details: str):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] user={user} event={event_type} details={details}\n") 