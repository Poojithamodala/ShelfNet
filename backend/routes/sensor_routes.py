from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import uuid

from database import sensors_collection, batches_collection
from models.sensor_model import SensorCreate
from utils.auth_dependency import get_current_user, require_role

router = APIRouter()

@router.post(
    "",
    dependencies=[Depends(require_role(["MANAGER"]))]
)
def register_sensor(
    sensor: SensorCreate,
    user=Depends(get_current_user)
):
    # Manager can only add sensor to own warehouse
    if sensor.warehouse_id != user["warehouse_id"]:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized for this warehouse"
        )

    sensor_id = f"SNS-{str(uuid.uuid4())[:4].upper()}"

    doc = {
        "sensor_id": sensor_id,
        **sensor.dict(),
        "status": "ACTIVE",
        "installed_at": datetime.utcnow(),
        "registered_by": user["user_id"]
    }

    sensors_collection.insert_one(doc)

    return {
        "sensor_id": sensor_id,
        "status": "ACTIVE"
    }


@router.get("")
def list_sensors(user=Depends(get_current_user)):

    # ADMIN → all sensors
    if user["role"] == "ADMIN":
        return list(sensors_collection.find({}, {"_id": 0}))

    # MANAGER → own warehouse only
    if user["role"] == "MANAGER":
        return list(
            sensors_collection.find(
                {"warehouse_id": user["warehouse_id"]},
                {"_id": 0}
            )
        )

    raise HTTPException(status_code=403, detail="Access denied")


@router.put(
    "/{sensor_id}/assign-batch",
    dependencies=[Depends(require_role(["MANAGER"]))]
)
def assign_batch_to_sensor(
    sensor_id: str,
    batch_id: str,
    user=Depends(get_current_user)
):
    # Fetch sensor
    sensor = sensors_collection.find_one(
        {"sensor_id": sensor_id},
        {"_id": 0}
    )

    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    # Warehouse ownership
    if sensor["warehouse_id"] != user["warehouse_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Validate batch
    batch = batches_collection.find_one(
        {"batch_id": batch_id, "warehouse_id": user["warehouse_id"]},
        {"_id": 0}
    )

    if not batch:
        raise HTTPException(
            status_code=400,
            detail="Invalid batch for this warehouse"
        )

    sensors_collection.update_one(
        {"sensor_id": sensor_id},
        {"$set": {"current_batch_id": batch_id}}
    )

    return {
        "sensor_id": sensor_id,
        "current_batch_id": batch_id
    }
