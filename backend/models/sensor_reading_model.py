from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SensorReading(BaseModel):
    batch_id: str
    sensor_id: str
    warehouse_id: Optional[str] = None
    timestamp: datetime
    temperature: float
    humidity: float
    ethylene: float
    co2: float
    o2: float
    light: float
    vibration: float
    power_status: str
