import os
import hmac
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.core.logging import log_event

security = HTTPBasic()
router = APIRouter()

def verify_admin_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.environ.get("ADMIN_USERNAME")
    correct_password = os.environ.get("ADMIN_PASSWORD")
    if not correct_username or not correct_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Administrator credentials are not configured.",
        )
    username_matches = hmac.compare_digest(credentials.username, correct_username)
    password_matches = hmac.compare_digest(credentials.password, correct_password)
    if not (username_matches and password_matches):
        log_event(credentials.username, "admin_auth_check", "failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    log_event(credentials.username, "admin_auth_check", "success")
    return credentials

@router.get("/admin/auth/check")
def admin_auth_check(credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    return {"detail": "Admin authentication successful."}
