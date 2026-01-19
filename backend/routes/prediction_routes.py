from fastapi import APIRouter, HTTPException, Depends
from services.prediction_service import predict_for_batch
from database import batches_collection
from utils.auth_dependency import get_current_user

router = APIRouter()

@router.get("/{batch_id}")
def predict(
    batch_id: str,
    user=Depends(get_current_user)
):
    # Fetch batch
    batch = batches_collection.find_one(
        {"batch_id": batch_id},
        {"_id": 0}
    )

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Warehouse isolation (ADMIN bypass)
    if user["role"] != "ADMIN":
        if user.get("warehouse_id") != batch["warehouse_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied for this batch"
            )

    try:
        prediction = predict_for_batch(batch_id)

        return {
            "batch_id": batch_id,
            "fruit": batch["fruit"],
            "warehouse_id": batch["warehouse_id"],
            "predicted_remaining_shelf_life_days": prediction
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

