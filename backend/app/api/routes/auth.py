import hashlib
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter()

class NurseLoginRequest(BaseModel):
    username: str
    password: str

# Prototype hashed password for admin
# username: admin, password: admin1234
MOCK_NURSE_USER = "admin"
MOCK_PASSWORD_HASH = hashlib.sha256("admin1234".encode("utf-8")).hexdigest()

@router.post("/auth/nurse/login")
def nurse_login(req: NurseLoginRequest):
    input_hash = hashlib.sha256(req.password.encode("utf-8")).hexdigest()
    if req.username.strip().lower() == MOCK_NURSE_USER and input_hash == MOCK_PASSWORD_HASH:
        return {
            "access_token": "medivoice_nurse_jwt_token_sample_2026",
            "token_type": "bearer",
            "username": req.username,
            "role": "triage_nurse"
        }
    raise HTTPException(status_code=401, detail="Invalid nurse credentials")
