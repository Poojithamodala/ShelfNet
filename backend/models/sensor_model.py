from pydantic import BaseModel
from typing import Optional

class SensorCreate(BaseModel):
    warehouse_id: str
    location: str
    current_batch_id: Optional[str] = None