from pydantic import BaseModel
from datetime import datetime

class BatchCreate(BaseModel):
    fruit: str
    quantity_kg: int
    arrival_date: datetime
    expected_shelf_life_days: int
    warehouse_id: str
