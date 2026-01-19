from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import uuid

from database import users_collection
from models.user_model import UserCreate
from utils.security import hash_password
from utils.auth_dependency import require_role

router = APIRouter()

VALID_ROLES = {"ADMIN", "MANAGER", "SALES"}

from utils.security import hash_password

@router.post("")
def create_user(user: UserCreate):

    if user.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    if user.role in {"MANAGER", "SALES"} and not user.warehouse_id:
        raise HTTPException(status_code=400, detail="warehouse_id required")

    if user.role == "ADMIN" and not user.password:
        raise HTTPException(status_code=400, detail="Admin password required")

    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    user_id = f"USR-{str(uuid.uuid4())[:4].upper()}"

    doc = {
        "user_id": user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "warehouse_id": None if user.role == "ADMIN" else user.warehouse_id,
        "status": "ACTIVE" if user.role == "ADMIN" else "PENDING",
        "created_at": datetime.utcnow(),
        "password_set": False
    }

    if user.role == "ADMIN":
        doc["password_hash"] = hash_password(user.password)
        doc["password_set"] = True

    users_collection.insert_one(doc)

    return {
        "user_id": user_id,
        "status": doc["status"],
        "message": (
            "Admin created successfully"
            if user.role == "ADMIN"
            else "Registration submitted. Await admin approval."
        )
    }

@router.get("/pending")
def list_pending_users(
    _=Depends(require_role(["ADMIN"]))
):
    return list(
        users_collection.find({"status": "PENDING"}, {"_id": 0})
    )


@router.post("/{user_id}/approve")
def approve_user(
    user_id: str,
    _=Depends(require_role(["ADMIN"]))
):

    result = users_collection.update_one(
        {"user_id": user_id, "status": "PENDING"},
        {
            "$set": {
                "status": "ACTIVE",
                "approved_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Pending user not found")

    return {
        "user_id": user_id,
        "status": "ACTIVE",
        "message": "User approved successfully"
    }


@router.post("/{user_id}/disable")
def disable_user(
    user_id: str,
    _=Depends(require_role(["ADMIN"]))
):

    result = users_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "status": "DISABLED",
                "disabled_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_id,
        "status": "DISABLED"
    }


@router.get("")
def list_users(
    _=Depends(require_role(["ADMIN"]))
):
    return list(users_collection.find({}, {"_id": 0}))
