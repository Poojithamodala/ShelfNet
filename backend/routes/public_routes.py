from fastapi import APIRouter
from pymongo import MongoClient
 
router = APIRouter(
    prefix="/public",
    tags=["Public"]
    # ✅ No auth dependency — accessible without login
)
 
client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]
warehouses_col = db["warehouses"]
 
@router.get("/warehouses")
def get_public_warehouses():
    """
    Returns basic warehouse info for the registration page.
    No authentication required.
    """
    warehouses = list(warehouses_col.find({}, {"_id": 0}))
    return [
        {
            "warehouse_id": wh["warehouse_id"],
            "name": wh["name"],
            "location": wh["location"]
        }
        for wh in warehouses
    ]