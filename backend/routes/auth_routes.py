from fastapi import APIRouter, HTTPException
from datetime import timedelta

from database import users_collection
from models.auth_model import LoginRequest
from models.auth_model import SetPasswordRequest
from utils.security import verify_password, create_access_token, hash_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
def login(data: LoginRequest):

    user = users_collection.find_one(
        {"email": data.email},
        {"_id": 0}
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user["status"] != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail=f"Account is {user['status']}. Please contact admin."
        )

    if not user.get("password_hash"):
        raise HTTPException(
            status_code=403,
            detail="Password not set. Please complete account setup."
        )

    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "user_id": user["user_id"],
        "role": user["role"],
        "warehouse_id": user.get("warehouse_id")
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "role": user["role"],
            "warehouse_id": user.get("warehouse_id")
        }
    }

@router.post("/set-password")
def set_password(data: SetPasswordRequest):

    user = users_collection.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["status"] != "ACTIVE":
        raise HTTPException(status_code=403, detail="Account not active")

    if user.get("password_set"):
        raise HTTPException(status_code=400, detail="Password already set")

    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    users_collection.update_one(
        {"email": data.email},
        {
            "$set": {
                "password_hash": hash_password(data.password),
                "password_set": True
            }
        }
    )

    return {"message": "Password set successfully"}
