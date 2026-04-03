from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
from typing import Optional

from database import batches_collection, warehouses_collection, alerts_collection
from models.batch_model import BatchCreate
from utils.id_generator import generate_batch_id
from utils.auth_dependency import require_role, get_current_user
from services.prediction_service import predict_static

router = APIRouter()


def serialize_doc(doc: dict) -> dict:
    result = {}
    for k, v in doc.items():
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        else:
            result[k] = v
    result.pop("_id", None)
    return result


@router.post(
    "",
    dependencies=[Depends(require_role(["MANAGER"]))],
)
def create_batch(
    batch: BatchCreate,
    user=Depends(get_current_user)
):
    if user["warehouse_id"] != batch.warehouse_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized for this warehouse"
        )

    warehouse = warehouses_collection.find_one(
        {"warehouse_id": batch.warehouse_id, "status": "ACTIVE"}
    )
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    count    = batches_collection.count_documents({"fruit": batch.fruit}) + 1
    batch_id = generate_batch_id(batch.fruit, count)

    # ── Static prediction at creation time using fruit profile defaults ───────
    from simulator import FRUIT_PROFILES, DEFAULT_PROFILE
    profile = FRUIT_PROFILES.get(batch.fruit, DEFAULT_PROFILE)
    default_sensor = {
        "temperature_c":    sum(profile["temperature"]) / 2,
        "humidity_percent": sum(profile["humidity"]) / 2,
        "ethylene_ppm":     sum(profile["ethylene"]) / 2,
        "co2_ppm":          1.0,
        "o2_percent":       20.0,
    }

    try:
        # FIX: pass fruit so model uses correct fruit_encoded feature
        initial_prediction = predict_static(default_sensor, fruit=batch.fruit)
    except Exception as e:
        print(f"⚠️ Initial prediction failed: {e}")
        initial_prediction = None

    batch_doc = {
        "batch_id":    batch_id,
        **batch.dict(),
        "status":      "ACTIVE",
        "created_at":  datetime.utcnow(),
        "created_by_user_id": user["user_id"],
        # ✅ Prediction available immediately on creation
        "predicted_remaining_shelf_life_days": initial_prediction,
        "last_predicted_at": datetime.utcnow() if initial_prediction else None,
    }

    batches_collection.insert_one(batch_doc)

    warehouses_collection.update_one(
        {"warehouse_id": batch.warehouse_id},
        {"$inc": {"active_batches_count": 1}}
    )

    return {
        "batch_id":   batch_id,
        "status":     "ACTIVE",
        "predicted_remaining_shelf_life_days": initial_prediction
    }


@router.get("")
def list_batches(
    warehouse_id: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    from services.prediction_service import predict_for_batch

    role  = user["role"]
    query = {} if role == "ADMIN" else {"warehouse_id": user["warehouse_id"]}
    if role == "ADMIN" and warehouse_id:
        query["warehouse_id"] = warehouse_id

    batches = list(batches_collection.find(query, {"_id": 0}))

    for b in batches:
        try:
            predicted = predict_for_batch(b["batch_id"])
            b["predicted_remaining_shelf_life_days"] = predicted
        except Exception as e:
            print(f"⚠️ Prediction failed for {b['batch_id']}: {e}")

    return [serialize_doc(b) for b in batches]


@router.get("/debug-alerts/{batch_id}")
def debug_alerts(batch_id: str):
    alerts = list(alerts_collection.find({"batch_id": batch_id}, {"_id": 0}))
    return {"count": len(alerts), "alerts": alerts}


@router.post(
    "/{batch_id}/close",
    dependencies=[Depends(require_role(["SALES", "MANAGER"]))]
)
def close_batch(
    batch_id: str,
    user=Depends(get_current_user)
):
    batch = batches_collection.find_one({"batch_id": batch_id, "status": "ACTIVE"})
    if not batch:
        raise HTTPException(status_code=404, detail="Active batch not found")

    if batch["warehouse_id"] != user["warehouse_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    batches_collection.update_one(
        {"batch_id": batch_id},
        {"$set": {"status": "INACTIVE", "closed_at": datetime.utcnow()}}
    )
    warehouses_collection.update_one(
        {"warehouse_id": batch["warehouse_id"]},
        {"$inc": {"active_batches_count": -1}}
    )
    alerts_collection.update_many(
        {"batch_id": batch_id, "resolved": {"$in": [False, None]}},
        {"$set": {"resolved": True, "resolved_at": datetime.utcnow()}}
    )

    return {"status": "CLOSED"}