from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pymongo import MongoClient
from bson import ObjectId

from utils.auth_dependency import get_current_user, require_role

router = APIRouter()

client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]
alerts_collection = db["alerts"]

# Get all alerts
@router.get(
    "",
    dependencies=[Depends(require_role(["ADMIN"]))]
)
def get_all_alerts():
    return list(alerts_collection.find({}, {"_id": 0}))


# Get alerts for a specific warehouse
@router.get("/warehouse/{warehouse_id}")
def get_alerts_by_warehouse(
    warehouse_id: str,
    user=Depends(get_current_user)
):
    if user["role"] != "ADMIN" and user.get("warehouse_id") != warehouse_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return list(
        alerts_collection.find(
            {"warehouse_id": warehouse_id},
            {"_id": 0}
        )
    )


# Get alerts for a specific batch
@router.get("/batch/{batch_id}")
def get_alerts_by_batch(
    batch_id: str,
    user=Depends(get_current_user)
):
    query = {"batch_id": batch_id}

    if user["role"] != "ADMIN":
        query["warehouse_id"] = user["warehouse_id"]

    return list(alerts_collection.find(query, {"_id": 0}))


# Get only unresolved alerts
@router.get("/active")
def get_active_alerts(user=Depends(get_current_user)):

    if user["role"] not in {"ADMIN", "MANAGER"}:
        raise HTTPException(status_code=403, detail="Access denied")

    query = {"resolved": False}

    if user["role"] == "MANAGER":
        query["warehouse_id"] = user["warehouse_id"]

    return list(alerts_collection.find(query, {"_id": 0}))


# Acknowledge alert
@router.post(
    "/acknowledge/{alert_id}",
    dependencies=[Depends(require_role(["MANAGER"]))]
)
def acknowledge_alert(
    alert_id: str,
    user=Depends(get_current_user)
):
    result = alerts_collection.update_one(
        {
            "_id": ObjectId(alert_id),
            "warehouse_id": user["warehouse_id"],
            "resolved": False
        },
        {
            "$set": {
                "resolved": True,
                "resolved_at": datetime.utcnow(),
                "resolved_by": user["user_id"],
                "resolution_type": "ACKNOWLEDGED"
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found or already resolved")

    return {
        "status": "ACKNOWLEDGED",
        "alert_id": alert_id
    }


# resolve alert
@router.post(
    "/resolve/{alert_id}",
    dependencies=[Depends(require_role(["MANAGER"]))]
)
def resolve_alert(
    alert_id: str,
    user=Depends(get_current_user)
):
    result = alerts_collection.update_one(
        {"_id": ObjectId(alert_id)},
        {
            "$set": {
                "resolved": True,
                "resolved_at": datetime.utcnow(),
                "resolved_by": user["user_id"],
                "resolution_type": "FORCE_RESOLVED"
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {
        "status": "RESOLVED",
        "alert_id": alert_id
    }
