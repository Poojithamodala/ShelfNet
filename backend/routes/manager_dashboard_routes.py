from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from bson import ObjectId
from typing import Optional
from pydantic import BaseModel

from utils.auth_dependency import require_role, get_current_user
from services.prediction_service import predict_for_batch, predict_static
from database import (
    batches_collection as batches_col,
    alerts_collection as alerts_col,
    sensors_collection as sensors_col,
    sensor_readings_collection as readings_col
)

router = APIRouter(
    prefix="/manager",
    tags=["Manager Dashboard"],
    dependencies=[Depends(require_role(["MANAGER", "ADMIN"]))]
)

def check_warehouse_access(user, warehouse_id: str):
    if user["role"] == "MANAGER" and user.get("warehouse_id") != warehouse_id:
        raise HTTPException(status_code=403, detail="Access denied to this warehouse")


class SensorReadingInput(BaseModel):
    temperature_c:    Optional[float] = None
    humidity_percent: Optional[float] = None
    ethylene_ppm:     Optional[float] = None
    co2_ppm:          Optional[float] = None
    o2_percent:       Optional[float] = None

class CreateBatchRequest(BaseModel):
    fruit:                    str
    quantity_kg:              float
    arrival_date:             str
    expected_shelf_life_days: int = 30
    warehouse_id:             str
    sensor_reading:           Optional[SensorReadingInput] = None


@router.post("/{warehouse_id}/batches/create")
def create_batch(
    warehouse_id: str,
    payload: CreateBatchRequest,
    user=Depends(get_current_user)
):
    check_warehouse_access(user, warehouse_id)

    import uuid
    batch_id = f"BATCH-{uuid.uuid4().hex[:8].upper()}"

    batch_doc = {
        "batch_id":                 batch_id,
        "fruit":                    payload.fruit,
        "quantity_kg":              payload.quantity_kg,
        "arrival_date":             datetime.fromisoformat(payload.arrival_date),
        "expected_shelf_life_days": payload.expected_shelf_life_days,
        "warehouse_id":             warehouse_id,
        "status":                   "ACTIVE",
        "created_at":               datetime.utcnow(),
        "predicted_remaining_shelf_life_days": None,
        "last_predicted_at":        None,
    }

    if payload.sensor_reading:
        sensor_dict = payload.sensor_reading.dict(exclude_none=True)
        try:
            prediction = predict_static(sensor_dict)
            batch_doc["predicted_remaining_shelf_life_days"] = prediction
            batch_doc["last_predicted_at"] = datetime.utcnow()
        except Exception as exc:
            print(f"WARNING: Static prediction failed ({exc}), skipping.")

    batches_col.insert_one(batch_doc)

    return {
        "status": "CREATED",
        "batch_id": batch_id,
        "predicted_remaining_shelf_life_days": batch_doc["predicted_remaining_shelf_life_days"]
    }


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
        "selled_batches": batches_col.count_documents({
            "warehouse_id": warehouse_id,
            "status": "INACTIVE"
        }),
        "total_batches": batches_col.count_documents({
            "warehouse_id": warehouse_id
        }),
        "active_alerts": alerts_col.count_documents({
            "warehouse_id": warehouse_id,
            "resolved": {"$in": [False, None]}
        }),
        "critical_alerts": alerts_col.count_documents({
            "warehouse_id": warehouse_id,
            "alert_type": "CRITICAL",
            "resolved": {"$in": [False, None]}
        }),
        "resolved_alerts": alerts_col.count_documents({
            "warehouse_id": warehouse_id,
            "resolved": True
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


@router.get("/{warehouse_id}/analytics/batch-status")
def manager_batch_status(
    warehouse_id: str,
    user=Depends(get_current_user)
):
    check_warehouse_access(user, warehouse_id)

    active = batches_col.count_documents({"warehouse_id": warehouse_id, "status": "ACTIVE"})
    sold   = batches_col.count_documents({"warehouse_id": warehouse_id, "status": "INACTIVE"})
    total  = batches_col.count_documents({"warehouse_id": warehouse_id})

    return [
        {"label": "Active", "count": active},
        {"label": "Sold",   "count": sold},
        {"label": "Other",  "count": max(0, total - active - sold)},
    ]


@router.get("/{warehouse_id}/analytics/alerts")
def manager_alert_breakdown(
    warehouse_id: str,
    user=Depends(get_current_user)
):
    check_warehouse_access(user, warehouse_id)

    pipeline = [
        {"$match": {"warehouse_id": warehouse_id}},
        {
            "$group": {
                "_id": "$alert_type",
                "active":   {"$sum": {"$cond": [{"$in": ["$resolved", [False, None]]}, 1, 0]}},
                "resolved": {"$sum": {"$cond": [{"$eq": ["$resolved", True]}, 1, 0]}}
            }
        },
        {"$sort": {"active": -1}}
    ]

    data = list(alerts_col.aggregate(pipeline))

    return [
        {
            "alert_type": d["_id"],
            "active":     d["active"],
            "resolved":   d["resolved"]
        }
        for d in data
    ]


@router.get("/{warehouse_id}/analytics/fruit-shelf-life")
def manager_fruit_shelf_life(
    warehouse_id: str,
    user=Depends(get_current_user)
):
    check_warehouse_access(user, warehouse_id)

    pipeline = [
        {
            "$match": {
                "warehouse_id": warehouse_id,
                "status": "ACTIVE",
                "predicted_remaining_shelf_life_days": {"$exists": True}
            }
        },
        {
            "$group": {
                "_id": "$fruit",
                "avg_remaining_shelf_life": {"$avg": "$predicted_remaining_shelf_life_days"},
                "total_batches": {"$sum": 1}
            }
        },
        {"$sort": {"avg_remaining_shelf_life": 1}}
    ]

    data = list(batches_col.aggregate(pipeline))

    return [
        {
            "fruit": d["_id"],
            "avg_remaining_shelf_life": (
                round(d["avg_remaining_shelf_life"], 2)
                if d.get("avg_remaining_shelf_life") is not None else None
            ),
            "total_batches": d["total_batches"]
        }
        for d in data
    ]


@router.get("/{warehouse_id}/analytics/sensor-health")
def manager_sensor_health(
    warehouse_id: str,
    user=Depends(get_current_user)
):
    check_warehouse_access(user, warehouse_id)

    total   = sensors_col.count_documents({"warehouse_id": warehouse_id})
    online  = sensors_col.count_documents({"warehouse_id": warehouse_id, "status": "ACTIVE"})
    offline = total - online

    return [
        {"name": "Online",  "value": online},
        {"name": "Offline", "value": offline},
    ]


@router.get("/{warehouse_id}/analytics/expiry-distribution")
def manager_expiry_distribution(
    warehouse_id: str,
    user=Depends(get_current_user)
):
    check_warehouse_access(user, warehouse_id)

    base_query = {
        "warehouse_id": warehouse_id,
        "status": "ACTIVE",
        "predicted_remaining_shelf_life_days": {"$exists": True}
    }

    buckets = [
        {"label": "0–2 days (Critical)", "min": 0,  "max": 2},
        {"label": "3–5 days (Warning)",  "min": 3,  "max": 5},
        {"label": "6–10 days",           "min": 6,  "max": 10},
        {"label": "11–20 days",          "min": 11, "max": 20},
        {"label": "20+ days",            "min": 21, "max": 99999},
    ]

    result = []
    for bucket in buckets:
        count = batches_col.count_documents({
            **base_query,
            "predicted_remaining_shelf_life_days": {
                "$gte": bucket["min"],
                "$lte": bucket["max"]
            }
        })
        result.append({"label": bucket["label"], "count": count})

    return result


@router.get("/{warehouse_id}/alerts")
def get_warehouse_alerts(
    warehouse_id: str,
    user=Depends(get_current_user)
):
    check_warehouse_access(user, warehouse_id)

    return list(
        alerts_col.find(
            {"warehouse_id": warehouse_id},
            {"_id": 0}
        ).sort("created_at", -1)
    )


@router.get("/{warehouse_id}/batches")
def get_warehouse_batches(
    warehouse_id: str,
    user=Depends(get_current_user)
):
    check_warehouse_access(user, warehouse_id)

    batches = list(batches_col.find({"warehouse_id": warehouse_id}, {"_id": 0}))

    active_batches = [b for b in batches if b.get("status") == "ACTIVE"]
    for batch in active_batches:
        try:
            predict_for_batch(batch["batch_id"])
        except Exception:
            pass

    batches = list(batches_col.find({"warehouse_id": warehouse_id}, {"_id": 0}))

    for batch in batches:
        alert_count = alerts_col.count_documents({
            "batch_id": batch["batch_id"],
            "resolved": {"$in": [False, None]}
        })
        remaining = batch.get("predicted_remaining_shelf_life_days", 999)
        batch["active_alerts"] = alert_count
        batch["risk_level"] = (
            "CRITICAL" if remaining <= 2 else
            "WARNING"  if remaining <= 5 else
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

    sensor         = sensors_col.find_one({"current_batch_id": batch_id}, {"_id": 0})
    latest_reading = readings_col.find_one(
        {"batch_id": batch_id}, {"_id": 0}, sort=[("timestamp", -1)]
    )
    alerts = list(alerts_col.find({"batch_id": batch_id}, {"_id": 0}).sort("created_at", -1))

    return {
        "batch":          batch,
        "sensor":         sensor,
        "latest_reading": latest_reading,
        "alerts":         alerts
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
                "resolved":        True,
                "resolved_at":     datetime.utcnow(),
                "resolved_by":     user["user_id"],
                "resolution_type": "MANUAL"
            }
        }
    )

    return {"status": "RESOLVED"}