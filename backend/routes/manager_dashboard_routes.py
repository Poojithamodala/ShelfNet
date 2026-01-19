from fastapi import APIRouter, HTTPException, Depends
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId

from utils.auth_dependency import require_role, get_current_user

router = APIRouter(
    prefix="/manager",
    tags=["Manager Dashboard"],
    dependencies=[Depends(require_role(["MANAGER", "ADMIN"]))]
)

client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]

batches_col = db["batches"]
alerts_col = db["alerts"]
sensors_col = db["sensors"]
readings_col = db["sensor_readings"]

def check_warehouse_access(user, warehouse_id: str):
    if user["role"] == "MANAGER" and user.get("warehouse_id") != warehouse_id:
        raise HTTPException(status_code=403, detail="Access denied to this warehouse")

@router.get("/{warehouse_id}/kpis")
def get_manager_kpis(
    warehouse_id: str,
    user=Depends(get_current_user)
):
    check_warehouse_access(user, warehouse_id)

    return {
        "active_batches": batches_col.count_documents({
            "warehouse_id": warehouse_id,
            "status": "ACTIVE"
        }),
        "critical_alerts": alerts_col.count_documents({
            "warehouse_id": warehouse_id,
            "alert_type": "CRITICAL",
            "resolved": False
        }),
        "expiring_batches": batches_col.count_documents({
            "warehouse_id": warehouse_id,
            "predicted_remaining_shelf_life_days": {"$lte": 5}
        }),
        "sensors_online": sensors_col.count_documents({
            "warehouse_id": warehouse_id,
            "status": "ACTIVE"
        }),
        "sensors_total": sensors_col.count_documents({
            "warehouse_id": warehouse_id
        })
    }


@router.get("/{warehouse_id}/alerts")
def get_warehouse_alerts(
    warehouse_id: str,
    user=Depends(get_current_user)
):
    check_warehouse_access(user, warehouse_id)

    return list(
        alerts_col.find(
            {"warehouse_id": warehouse_id, "resolved": False},
            {"_id": 0}
        ).sort("created_at", -1)
    )


@router.get("/{warehouse_id}/batches")
def get_active_batches(
    warehouse_id: str,
    user=Depends(get_current_user)
):
    check_warehouse_access(user, warehouse_id)

    batches = list(
        batches_col.find(
            {"warehouse_id": warehouse_id, "status": "ACTIVE"},
            {"_id": 0}
        )
    )

    for batch in batches:
        alert_count = alerts_col.count_documents({
            "batch_id": batch["batch_id"],
            "resolved": False
        })

        remaining = batch.get("predicted_remaining_shelf_life_days", 999)

        batch["active_alerts"] = alert_count
        batch["risk_level"] = (
            "CRITICAL" if remaining <= 2 else
            "WARNING" if remaining <= 5 else
            "SAFE"
        )

    return batches


@router.get("/batch/{batch_id}/details")
def get_batch_details(
    batch_id: str,
    user=Depends(get_current_user)
):
    batch = batches_col.find_one({"batch_id": batch_id}, {"_id": 0})
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    check_warehouse_access(user, batch["warehouse_id"])

    sensor = sensors_col.find_one({"current_batch_id": batch_id}, {"_id": 0})

    latest_reading = readings_col.find_one(
        {"batch_id": batch_id},
        {"_id": 0},
        sort=[("timestamp", -1)]
    )

    alerts = list(
        alerts_col.find({"batch_id": batch_id}, {"_id": 0})
        .sort("created_at", -1)
    )

    return {
        "batch": batch,
        "sensor": sensor,
        "latest_reading": latest_reading,
        "alerts": alerts
    }


@router.get("/batch/{batch_id}/trends")
def get_sensor_trends(
    batch_id: str,
    hours: int = 24,
    user=Depends(get_current_user)
):
    batch = batches_col.find_one({"batch_id": batch_id})
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    check_warehouse_access(user, batch["warehouse_id"])

    since = datetime.utcnow() - timedelta(hours=hours)

    return list(
        readings_col.find(
            {"batch_id": batch_id, "timestamp": {"$gte": since}},
            {"_id": 0}
        ).sort("timestamp", 1)
    )


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: str,
    user=Depends(get_current_user)
):
    alert = alerts_col.find_one({"_id": ObjectId(alert_id)})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    check_warehouse_access(user, alert["warehouse_id"])

    alerts_col.update_one(
        {"_id": ObjectId(alert_id)},
        {
            "$set": {
                "resolved": True,
                "resolved_at": datetime.utcnow(),
                "resolved_by": user["user_id"],
                "resolution_type": "MANUAL"
            }
        }
    )

    return {"status": "RESOLVED"}
