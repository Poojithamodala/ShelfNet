from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: str
    role: str
    warehouse_id: Optional[str] = None
    password: Optional[str] = None
