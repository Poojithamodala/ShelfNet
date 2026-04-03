from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import uuid

from database import sensors_collection, batches_collection, sensor_readings_collection
from models.sensor_model import SensorCreate
from models.sensor_reading_model import SensorReading
from utils.auth_dependency import get_current_user, require_role
from services.prediction_service import predict_for_batch

router = APIRouter()


@router.post(
    "",
    dependencies=[Depends(require_role(["MANAGER"]))]
)
def register_sensor(
    sensor: SensorCreate,
    user=Depends(get_current_user)
):
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
    if user["role"] == "ADMIN":
        return list(sensors_collection.find({}, {"_id": 0}))

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
    sensor = sensors_collection.find_one({"sensor_id": sensor_id}, {"_id": 0})
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    if sensor["warehouse_id"] != user["warehouse_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

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

    return {"sensor_id": sensor_id, "current_batch_id": batch_id}


# ── NEW: Submit a sensor reading ────────────────────────────────────────────

@router.post("/{sensor_id}/readings")
def submit_reading(
    sensor_id: str,
    reading: SensorReading
):
    """
    Accepts a sensor reading, stores it, then triggers
    shelf life prediction if >= 10 readings exist for the batch.
    Called by the simulator or real IoT devices.
    No auth required so IoT devices can post freely.
    """
    sensor = sensors_collection.find_one({"sensor_id": sensor_id}, {"_id": 0})
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    batch_id     = sensor.get("current_batch_id")
    warehouse_id = sensor.get("warehouse_id")

    if not batch_id:
        raise HTTPException(
            status_code=400,
            detail="Sensor is not assigned to any batch"
        )

    doc = {
        "sensor_id":    sensor_id,
        "batch_id":     batch_id,
        "warehouse_id": warehouse_id,
        "timestamp":    reading.timestamp or datetime.utcnow(),
        "temperature":  reading.temperature,
        "humidity":     reading.humidity,
        "ethylene":     reading.ethylene,
        "co2":          reading.co2,
        "o2":           reading.o2,
        "light":        reading.light,
        "vibration":    reading.vibration,
        "power_status": reading.power_status,
    }

    readings_collection.insert_one(doc)

    # Trigger prediction once enough readings have accumulated
    reading_count = readings_collection.count_documents({"batch_id": batch_id})
    prediction    = None

    if reading_count >= 10:
        try:
            prediction = predict_for_batch(batch_id, force=True)
        except Exception as exc:
            print(f"Prediction skipped: {exc}")

    return {
        "status":          "READING_STORED",
        "batch_id":        batch_id,
        "reading_count":   reading_count,
        "prediction_days": prediction
    }