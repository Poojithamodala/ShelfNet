from fastapi import APIRouter, Depends
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
 
    active_query = restrict_to_warehouse(user, {
        "status": "ACTIVE",
        "predicted_remaining_shelf_life_days": {"$exists": True}
    })
 
    sold_query = restrict_to_warehouse(user, {
        "status": "INACTIVE"
    })
 
    total_query = restrict_to_warehouse(user, {})
 
    all_active_query = restrict_to_warehouse(user, {
        "status": "ACTIVE"
    })
 
    return {
        "sellable_batches": batches_col.count_documents({
            **active_query,
            "predicted_remaining_shelf_life_days": {"$gt": 5}
        }),
        "sell_soon_batches": batches_col.count_documents({
            **active_query,
            "predicted_remaining_shelf_life_days": {"$gt": 2, "$lte": 5}
        }),
        "not_sellable_batches": batches_col.count_documents({
            **active_query,
            "predicted_remaining_shelf_life_days": {"$lte": 2}
        }),
        "sold_batches": batches_col.count_documents(sold_query),
        "total_batches": batches_col.count_documents(total_query),
        "active_batches": batches_col.count_documents(all_active_query)
    }
 
 
# -----------------------------------------------------------------------
# GRAPH ANALYTICS ENDPOINTS
# -----------------------------------------------------------------------
 
@router.get("/analytics/sellability")
def sales_sellability_distribution(user=Depends(get_current_user)):
    """
    Returns sellability category counts for pie/bar chart.
    Categories: SELL_NOW, SELL_SOON, DO_NOT_SELL, SOLD
    """
    base_query = restrict_to_warehouse(user, {
        "status": "ACTIVE",
        "predicted_remaining_shelf_life_days": {"$exists": True}
    })
 
    sell_now = batches_col.count_documents({
        **base_query,
        "predicted_remaining_shelf_life_days": {"$gt": 5}
    })
    sell_soon = batches_col.count_documents({
        **base_query,
        "predicted_remaining_shelf_life_days": {"$gt": 2, "$lte": 5}
    })
    do_not_sell = batches_col.count_documents({
        **base_query,
        "predicted_remaining_shelf_life_days": {"$lte": 2}
    })
    sold = batches_col.count_documents(
        restrict_to_warehouse(user, {"status": "INACTIVE"})
    )
 
    return [
        {"category": "Sell Now",    "count": sell_now},
        {"category": "Sell Soon",   "count": sell_soon},
        {"category": "Do Not Sell", "count": do_not_sell},
        {"category": "Sold",        "count": sold},
    ]
 
 
@router.get("/analytics/fruit-shelf-life")
def sales_fruit_shelf_life(user=Depends(get_current_user)):
    """
    Returns average remaining shelf life grouped by fruit type.
    Used for bar chart.
    """
    query = restrict_to_warehouse(user, {
        "status": "ACTIVE",
        "predicted_remaining_shelf_life_days": {"$exists": True}
    })
 
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": "$fruit",
                "avg_remaining_shelf_life": {
                    "$avg": "$predicted_remaining_shelf_life_days"
                },
                "total_batches": {"$sum": 1}
            }
        },
        {"$sort": {"avg_remaining_shelf_life": -1}}
    ]
 
    data = list(batches_col.aggregate(pipeline))
 
    return [
        {
            "fruit": d["_id"],
            "avg_remaining_shelf_life": (
                round(d["avg_remaining_shelf_life"], 2)
                if d.get("avg_remaining_shelf_life") is not None
                else None
            ),
            "total_batches": d["total_batches"]
        }
        for d in data
    ]
 
 
@router.get("/analytics/batch-status")
def sales_batch_status(user=Depends(get_current_user)):
    """
    Returns batch counts grouped by status.
    Used for bar chart: Active vs Sold vs Total.
    """
    active = batches_col.count_documents(
        restrict_to_warehouse(user, {"status": "ACTIVE"})
    )
    sold = batches_col.count_documents(
        restrict_to_warehouse(user, {"status": "INACTIVE"})
    )
    total = batches_col.count_documents(
        restrict_to_warehouse(user, {})
    )
 
    return [
        {"label": "Active", "count": active},
        {"label": "Sold",   "count": sold},
        {"label": "Total",  "count": total},
    ]
 
 
@router.get("/analytics/expiry-distribution")
def sales_expiry_distribution(user=Depends(get_current_user)):
    """
    Returns count of active batches bucketed by days remaining.
    Used for bar chart showing urgency distribution.
    Buckets: 0-2d, 3-5d, 6-10d, 11-20d, 20d+
    """
    base_query = restrict_to_warehouse(user, {
        "status": "ACTIVE",
        "predicted_remaining_shelf_life_days": {"$exists": True}
    })
 
    buckets = [
        {"label": "0–2 days",  "min": 0,   "max": 2},
        {"label": "3–5 days",  "min": 3,   "max": 5},
        {"label": "6–10 days", "min": 6,   "max": 10},
        {"label": "11–20 days","min": 11,  "max": 20},
        {"label": "20+ days",  "min": 21,  "max": 99999},
    ]
 
    result = []
    for bucket in buckets:
        count = batches_col.count_documents({
            **base_query,
            "predicted_remaining_shelf_life_days": {
                "$gte": bucket["min"],
                "$lte": bucket["max"]
            }
        })
        result.append({"label": bucket["label"], "count": count})
 
    return result
 
 
# -----------------------------------------------------------------------
# EXISTING ENDPOINTS (unchanged)
# -----------------------------------------------------------------------
 
@router.get("/batches")
def sales_batches(user=Depends(get_current_user)):
 
    query = restrict_to_warehouse(user, {})
 
    batches = list(
        batches_col.find(query, {"_id": 0})
        .sort("predicted_remaining_shelf_life_days", 1)
    )
 
    result = []
 
    for b in batches:
        remaining = b.get("predicted_remaining_shelf_life_days")
        status = b.get("status", "ACTIVE")
        is_sold = status == "INACTIVE"
 
        if is_sold:
            category = "SELLED"
            remaining_value = None
        elif remaining is None:
            category = "SELL_NOW" if status == "ACTIVE" else "UNKNOWN"
            remaining_value = None
        else:
            category = (
                "DO_NOT_SELL" if remaining <= 2 else
                "SELL_SOON" if remaining <= 5 else
                "SELL_NOW"
            )
            remaining_value = round(remaining, 2)
 
        result.append({
            "batch_id": b.get("batch_id"),
            "fruit": b.get("fruit"),
            "quantity_kg": b.get("quantity_kg"),
            "warehouse_id": b.get("warehouse_id"),
            "remaining_shelf_life_days": remaining_value,
            "sales_category": category,
            "status": status
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
        "status": "ACTIVE"
    })
 
    batches = list(batches_col.find(query, {"_id": 0}))
 
    report = []
 
    for b in batches:
        remaining = b.get("predicted_remaining_shelf_life_days")
        if remaining is None:
            continue
 
        expiry_date = today + timedelta(days=remaining)
 
        report.append({
            "batch_id": b.get("batch_id"),
            "fruit": b.get("fruit"),
            "warehouse_id": b.get("warehouse_id"),
            "expected_expiry_date": expiry_date.date().isoformat(),
            "remaining_shelf_life_days": round(remaining, 2)
        })
 
    return report