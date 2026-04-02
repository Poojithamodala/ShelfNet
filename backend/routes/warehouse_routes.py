from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import uuid

from database import batches_collection, warehouses_collection
from models.warehouse_model import WarehouseCreate
from utils.auth_dependency import get_current_user, require_role

router = APIRouter()

@router.post(
    "",
    dependencies=[Depends(require_role(["ADMIN"]))]
)
def create_warehouse(
    wh: WarehouseCreate,
    user=Depends(get_current_user)
):
    warehouse_id = f"WH-{str(uuid.uuid4())[:4].upper()}"

    doc = {
        "warehouse_id": warehouse_id,
        **wh.dict(),
        "status": "ACTIVE",
        "active_batches_count": 0, 
        "created_at": datetime.utcnow(),
        "created_by": user["user_id"]
    }

    warehouses_collection.insert_one(doc)

    return {
        "warehouse_id": warehouse_id,
        "status": "ACTIVE"
    }


@router.get(
    "",
    dependencies=[Depends(require_role(["ADMIN"]))]
)
def list_warehouses():
    return list(
        warehouses_collection.find({}, {"_id": 0})
    )


@router.get(
    "/{warehouse_id}",
    dependencies=[Depends(require_role(["ADMIN", "MANAGER"]))]
)
def get_warehouse(warehouse_id: str, user=Depends(get_current_user)):
    warehouse = warehouses_collection.find_one(
        {"warehouse_id": warehouse_id},
        {"_id": 0}
    )
    
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Manager can only view their assigned warehouse
    if user["role"] == "MANAGER" and user.get("warehouse_id") != warehouse_id:
        raise HTTPException(status_code=403, detail="Access denied to this warehouse")
    
    return warehouse

