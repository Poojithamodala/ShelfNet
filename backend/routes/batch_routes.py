from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from database import batches_collection
from models.batch_model import BatchCreate
from utils.id_generator import generate_batch_id
from utils.auth_dependency import require_role, get_current_user

router = APIRouter()

@router.post(
    "",
    dependencies=[Depends(require_role(["MANAGER"]))]
)
def create_batch(
    batch: BatchCreate,
    user=Depends(get_current_user)
):
    """
    MANAGER can create batch only for their warehouse
    """

    # 1. Enforce warehouse ownership from token
    if user["warehouse_id"] != batch.warehouse_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized for this warehouse"
        )

    # 2. Generate batch ID
    count = batches_collection.count_documents(
        {"fruit": batch.fruit}
    ) + 1

    batch_id = generate_batch_id(batch.fruit, count)

    # 3. Create batch document
    doc = {
        "batch_id": batch_id,
        **batch.dict(),
        "status": "ACTIVE",
        "created_at": datetime.utcnow(),
        "created_by_user_id": user["user_id"]
    }

    batches_collection.insert_one(doc)

    return {
        "batch_id": batch_id,
        "status": "ACTIVE"
    }

# ALL --- ADMIN
# BATCH --- MANAGER
@router.get("")
def list_batches(user=Depends(get_current_user)):

    role = user["role"]

    # ADMIN → all batches
    if role == "ADMIN":
        return list(batches_collection.find({}, {"_id": 0}))

    # MANAGER / SALES → only their warehouse
    return list(
        batches_collection.find(
            {"warehouse_id": user["warehouse_id"]},
            {"_id": 0}
        )
    )

