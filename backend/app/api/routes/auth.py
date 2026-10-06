import hashlib
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter()

class NurseLoginRequest(BaseModel):
    username: str
    password: str

# Prototype hashed passwords for nurse dashboard
# 1. username: admin, password: admin1234 (Frontend Demo)
# 2. username: nurse_admin, password: medivoice_nurse_2026 (Automated Test Suite)
MOCK_ACCOUNTS = {
    "admin": hashlib.sha256("admin1234".encode("utf-8")).hexdigest(),
    "nurse_admin": hashlib.sha256("medivoice_nurse_2026".encode("utf-8")).hexdigest(),
}

@router.post("/auth/nurse/login")
def nurse_login(req: NurseLoginRequest):
    username = req.username.strip().lower()
    input_hash = hashlib.sha256(req.password.encode("utf-8")).hexdigest()
    if username in MOCK_ACCOUNTS and input_hash == MOCK_ACCOUNTS[username]:
        return {
            "access_token": "medivoice_nurse_jwt_token_sample_2026",
            "token_type": "bearer",
            "username": req.username,
            "role": "triage_nurse"
        }
    raise HTTPException(status_code=401, detail="Invalid nurse credentials")
