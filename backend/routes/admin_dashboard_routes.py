from fastapi import APIRouter, Depends
from pymongo import MongoClient
from datetime import datetime, timedelta

from utils.auth_dependency import require_role, get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"],
    dependencies=[Depends(require_role(["ADMIN"]))]
)

client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]

warehouses_col = db["warehouses"]
batches_col = db["batches"]
alerts_col = db["alerts"]
sensors_col = db["sensors"]
readings_col = db["sensor_readings"]
users_col = db["users"]

@router.get("/kpis")
def get_admin_kpis():

    total_warehouses = warehouses_col.count_documents({})
    total_batches = batches_col.count_documents({"status": "ACTIVE"})
    total_sensors = sensors_col.count_documents({})
    active_alerts = alerts_col.count_documents({"resolved": False})
    critical_batches = alerts_col.count_documents({
        "alert_type": "CRITICAL",
        "resolved": False
    })

    return {
        "total_warehouses": total_warehouses,
        "active_batches": total_batches,
        "total_sensors": total_sensors,
        "active_alerts": active_alerts,
        "critical_batches": critical_batches
    }

@router.get("/warehouses/summary")
def warehouse_summary():

    result = []

    warehouses = list(warehouses_col.find({}, {"_id": 0}))

    for wh in warehouses:
        warehouse_id = wh["warehouse_id"]

        batches = batches_col.count_documents({
            "warehouse_id": warehouse_id,
            "status": "ACTIVE"
        })

        alerts = alerts_col.count_documents({
            "warehouse_id": warehouse_id,
            "resolved": False
        })

        result.append({
            "warehouse_id": warehouse_id,
            "name": wh["name"],
            "location": wh["location"],
            "active_batches": batches,
            "active_alerts": alerts
        })

    return result

@router.get("/alerts/analytics")
def alert_analytics():

    pipeline = [
        {
            "$group": {
                "_id": "$alert_type",
                "count": {"$sum": 1}
            }
        }
    ]

    data = list(alerts_col.aggregate(pipeline))

    return [
        {
            "alert_type": d["_id"],
            "count": d["count"]
        }
        for d in data
    ]

@router.get("/fruits/overview")
def fruit_overview():

    pipeline = [
        {
            "$group": {
                "_id": "$fruit",
                "total_batches": {"$sum": 1},
                "avg_shelf_life": {
                    "$avg": "$predicted_remaining_shelf_life_days"
                }
            }
        }
    ]

    data = list(batches_col.aggregate(pipeline))

    return [
        {
            "fruit": d["_id"],
            "total_batches": d["total_batches"],
            "avg_remaining_shelf_life": (
                round(d["avg_shelf_life"], 2)
                if d.get("avg_shelf_life") is not None
                else None
            )
        }
        for d in data
    ]


@router.get("/sensors/health")
def sensor_health():

    total = sensors_col.count_documents({})
    offline = sensors_col.count_documents({"status": {"$ne": "ACTIVE"}})

    return {
        "total_sensors": total,
        "offline_sensors": offline,
        "online_sensors": total - offline
    }

@router.get("/users/summary")
def users_summary():

    pipeline = [
        {
            "$group": {
                "_id": "$role",
                "count": {"$sum": 1}
            }
        }
    ]

    data = list(users_col.aggregate(pipeline))

    return [
        {
            "role": d["_id"],
            "count": d["count"]
        }
        for d in data
    ]

@router.get("/reports/spoilage")
def spoilage_report():

    spoiled = alerts_col.find(
        {"alert_type": "SPOILED"},
        {"_id": 0}
    )

    return list(spoiled)
