from fastapi import APIRouter, Depends, HTTPException
from pymongo import MongoClient
from datetime import datetime, timedelta

from utils.auth_dependency import require_role, get_current_user

router = APIRouter(
    prefix="/sales",
    tags=["Sales Dashboard"],
    dependencies=[Depends(require_role(["SALES", "ADMIN"]))]
)

client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]

batches_col = db["batches"]
alerts_col = db["alerts"]

def restrict_to_warehouse(user, query: dict):
    if user["role"] == "SALES":
        query["warehouse_id"] = user["warehouse_id"]
    return query


@router.get("/kpis")
def sales_kpis(user=Depends(get_current_user)):

    base_query = restrict_to_warehouse(user, {
        "status": "ACTIVE",
        "predicted_remaining_shelf_life_days": {"$exists": True}
    })

    return {
        "sellable_batches": batches_col.count_documents({
            **base_query,
            "predicted_remaining_shelf_life_days": {"$gt": 5}
        }),
        "sell_soon_batches": batches_col.count_documents({
            **base_query,
            "predicted_remaining_shelf_life_days": {"$gt": 2, "$lte": 5}
        }),
        "not_sellable_batches": batches_col.count_documents({
            **base_query,
            "predicted_remaining_shelf_life_days": {"$lte": 2}
        })
    }


@router.get("/batches")
def sales_batches(user=Depends(get_current_user)):

    query = restrict_to_warehouse(user, {
        "status": "ACTIVE",
        "predicted_remaining_shelf_life_days": {"$exists": True}
    })

    batches = list(
        batches_col.find(query, {"_id": 0})
        .sort("predicted_remaining_shelf_life_days", 1)
    )

    result = []

    for b in batches:
        remaining = b["predicted_remaining_shelf_life_days"]

        category = (
            "DO_NOT_SELL" if remaining <= 2 else
            "SELL_SOON" if remaining <= 5 else
            "SELL_NOW"
        )

        result.append({
            "batch_id": b["batch_id"],
            "fruit": b["fruit"],
            "quantity_kg": b["quantity_kg"],
            "warehouse_id": b["warehouse_id"],
            "remaining_shelf_life_days": round(remaining, 2),
            "sales_category": category
        })

    return result

@router.get("/recommendations")
def sales_recommendations(user=Depends(get_current_user)):

    query = restrict_to_warehouse(user, {
        "status": "ACTIVE",
        "predicted_remaining_shelf_life_days": {"$gt": 0}
    })

    batches = list(
        batches_col.find(query, {"_id": 0})
        .sort("predicted_remaining_shelf_life_days", 1)
    )

    recommendations = []

    for b in batches:
        remaining = b["predicted_remaining_shelf_life_days"]

        priority = (
            "HIGH" if remaining <= 5 else
            "MEDIUM" if remaining <= 10 else
            "LOW"
        )

        recommendations.append({
            "batch_id": b["batch_id"],
            "fruit": b["fruit"],
            "quantity_kg": b["quantity_kg"],
            "remaining_shelf_life_days": round(remaining, 2),
            "priority": priority
        })

    return recommendations


@router.get("/reports/expiry")
def expiry_forecast(user=Depends(get_current_user)):

    today = datetime.utcnow()

    query = restrict_to_warehouse(user, {
        "status": "ACTIVE",
        "predicted_remaining_shelf_life_days": {"$exists": True}
    })

    batches = list(batches_col.find(query, {"_id": 0}))

    report = []

    for b in batches:
        remaining = b["predicted_remaining_shelf_life_days"]
        expiry_date = today + timedelta(days=remaining)

        report.append({
            "batch_id": b["batch_id"],
            "fruit": b["fruit"],
            "warehouse_id": b["warehouse_id"],
            "expected_expiry_date": expiry_date.date().isoformat(),
            "remaining_shelf_life_days": round(remaining, 2)
        })

    return report
