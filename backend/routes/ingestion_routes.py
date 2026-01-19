from fastapi import APIRouter, HTTPException, Depends
from database import sensor_readings_collection, batches_collection
from models.sensor_reading_model import SensorReading
from utils.auth_dependency import require_role, get_current_user

router = APIRouter()

#----MANAGER----
@router.post(
    "/ingest",
    dependencies=[Depends(require_role(["MANAGER"]))]
)
def ingest_reading(
    reading: SensorReading,
    user=Depends(get_current_user)
):
    """
    Sensor ingestion endpoint (SYSTEM only)
    """

    # Validate batch
    batch = batches_collection.find_one(
        {"batch_id": reading.batch_id, "status": "ACTIVE"},
        {"_id": 0}
    )

    if not batch:
        raise HTTPException(
            status_code=400,
            detail="Invalid or inactive batch"
        )

    # Warehouse derived from batch (authoritative)
    reading_dict = reading.dict()
    reading_dict["warehouse_id"] = batch["warehouse_id"]
    reading_dict["ingested_at"] = datetime.utcnow()

    sensor_readings_collection.insert_one(reading_dict)

    return {
        "status": "INGESTED",
        "batch_id": reading.batch_id,
        "warehouse_id": batch["warehouse_id"]
    }
