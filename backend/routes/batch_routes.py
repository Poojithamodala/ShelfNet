from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime

from database import batches_collection, warehouses_collection
from models.batch_model import BatchCreate
from utils.id_generator import generate_batch_id
from utils.auth_dependency import require_role, get_current_user
from services.prediction_service import predict_for_batch

router = APIRouter()

@router.post(
    "",
    dependencies=[Depends(require_role(["MANAGER"]))],
)
def create_batch(
    batch: BatchCreate,
    user=Depends(get_current_user)
):
    # 1. Enforce warehouse ownership
    if user["warehouse_id"] != batch.warehouse_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized for this warehouse"
        )

    # 2. Ensure warehouse exists & active
    warehouse = warehouses_collection.find_one(
        {"warehouse_id": batch.warehouse_id, "status": "ACTIVE"}
    )
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    # 3. Generate batch ID
    count = batches_collection.count_documents(
        {"fruit": batch.fruit}
    ) + 1
    batch_id = generate_batch_id(batch.fruit, count)

    # 4. Insert batch
    batch_doc = {
        "batch_id": batch_id,
        **batch.dict(),
        "status": "ACTIVE",
        "created_at": datetime.utcnow(),
        "created_by_user_id": user["user_id"]
    }

    batches_collection.insert_one(batch_doc)

    # 5. Increment warehouse counter (ATOMIC)
    warehouses_collection.update_one(
        {"warehouse_id": batch.warehouse_id},
        {"$inc": {"active_batches_count": 1}}
    )

    return {
        "batch_id": batch_id,
        "status": "ACTIVE"
    }


@router.get("")
def list_batches(
    warehouse_id: str | None = Query(None),
    user=Depends(get_current_user)
):
    role = user["role"]

    # Build query
    if role == "ADMIN":
        query = {}
        if warehouse_id:
            query["warehouse_id"] = warehouse_id
    else:
        # MANAGER / SALES → forced warehouse from token
        query = {"warehouse_id": user["warehouse_id"]}

    batches = list(batches_collection.find(query, {"_id": 0}))

    # AUTO-REFRESH PREDICTIONS (lazy live update)
    for b in batches:
        try:
            predict_for_batch(b["batch_id"])
        except Exception:
            # Do not break UI if one batch fails
            pass

    # Fetch again to return updated predictions
    return list(batches_collection.find(query, {"_id": 0}))


@router.post("/{batch_id}/close")
def close_batch(
    batch_id: str,
    user=Depends(get_current_user)
):
    batch = batches_collection.find_one(
        {"batch_id": batch_id, "status": "ACTIVE"}
    )

    if not batch:
        raise HTTPException(status_code=404, detail="Active batch not found")

    if user["role"] == "MANAGER" and batch["warehouse_id"] != user["warehouse_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # 1. Mark batch inactive
    batches_collection.update_one(
        {"batch_id": batch_id},
        {"$set": {"status": "INACTIVE", "closed_at": datetime.utcnow()}}
    )

    # 2. 🔥 Decrement warehouse counter
    warehouses_collection.update_one(
        {"warehouse_id": batch["warehouse_id"]},
        {"$inc": {"active_batches_count": -1}}
    )

    return {"status": "CLOSED"}
