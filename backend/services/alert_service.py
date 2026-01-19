from datetime import datetime
from pymongo import MongoClient
from services.alert_rules import ALERT_RULES

# FRUIT PROFILES
FRUIT_PROFILES = {
    "Apple": {"temperature": (3.0, 6.0), "humidity": (85, 95)},
    "Banana": {"temperature": (13.0, 18.0), "humidity": (85, 95)},
    "Strawberry": {"temperature": (0.0, 4.0), "humidity": (90, 95)},
    "Pear": {"temperature": (0.0, 4.0), "humidity": (85, 95)},
    "Grapes": {"temperature": (0.0, 2.0), "humidity": (90, 95)},
    "Cherry": {"temperature": (0.0, 2.0), "humidity": (90, 95)},
    "Tomato": {"temperature": (12.0, 18.0), "humidity": (85, 95)}
}

client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]

alerts_col = db["alerts"]
sensor_col = db["sensor_readings"]
batches_col = db["batches"]

def create_alert(batch_id, warehouse_id, alert_type, message):
    existing = alerts_col.find_one({
        "batch_id": batch_id,
        "alert_type": alert_type,
        "resolved": False
    })

    if existing:
        alerts_col.update_one(
            {"_id": existing["_id"]},
            {
                "$inc": {"occurrences": 1},
                "$set": {"last_seen_at": datetime.utcnow()}
            }
        )
        return

    alerts_col.insert_one({
        "batch_id": batch_id,
        "warehouse_id": warehouse_id,
        "alert_type": alert_type,
        "message": message,
        "created_at": datetime.utcnow(),
        "last_seen_at": datetime.utcnow(),
        "occurrences": 1,
        "resolved": False
    })


def auto_resolve_alert(batch_id, alert_type, message="Condition normalized"):
    alerts_col.update_one(
        {
            "batch_id": batch_id,
            "alert_type": alert_type,
            "resolved": False
        },
        {
            "$set": {
                "resolved": True,
                "resolved_at": datetime.utcnow(),
                "resolution_type": "AUTO_RESOLVED",
                "resolution_message": message
            }
        }
    )

def evaluate_alerts(batch_id, warehouse_id, fruit, prediction, latest, history):

    profile = FRUIT_PROFILES.get(fruit)

    if prediction <= 0:
        create_alert(batch_id, warehouse_id, "SPOILED", "Batch likely spoiled")
    elif prediction <= ALERT_RULES["SHELF_CRITICAL"]:
        create_alert(batch_id, warehouse_id, "CRITICAL", f"Shelf life {prediction} days")
    elif prediction <= ALERT_RULES["SHELF_WARNING"]:
        create_alert(batch_id, warehouse_id, "WARNING", f"Shelf life {prediction} days")
    elif prediction <= ALERT_RULES["SHELF_INFO"]:
        create_alert(batch_id, warehouse_id, "INFO", f"Shelf life {prediction} days")

    # TEMPERATURE (SAFE) 
    if profile:
        temp_min, temp_max = profile["temperature"]

        if latest["temperature"] > temp_max:
            create_alert(batch_id, warehouse_id, "TEMP_HIGH", "Temperature too high")
        else:
            auto_resolve_alert(batch_id, "TEMP_HIGH")

        if latest["temperature"] < temp_min:
            create_alert(batch_id, warehouse_id, "TEMP_LOW", "Temperature too low")
        else:
            auto_resolve_alert(batch_id, "TEMP_LOW")
    else:
        auto_resolve_alert(batch_id, "TEMP_HIGH")
        auto_resolve_alert(batch_id, "TEMP_LOW")

    # HUMIDITY 
    if profile:
        hum_min, hum_max = profile["humidity"]

        if latest["humidity"] < hum_min:
            create_alert(batch_id, warehouse_id, "HUMIDITY_LOW", "Humidity too low")
        else:
            auto_resolve_alert(batch_id, "HUMIDITY_LOW")

        if latest["humidity"] > hum_max:
            create_alert(batch_id, warehouse_id, "HUMIDITY_HIGH", "Humidity too high")
        else:
            auto_resolve_alert(batch_id, "HUMIDITY_HIGH")
    else:
        auto_resolve_alert(batch_id, "HUMIDITY_LOW")
        auto_resolve_alert(batch_id, "HUMIDITY_HIGH")

    # GASES
    if latest["ethylene"] > ALERT_RULES["ETHYLENE_MAX"]:
        create_alert(batch_id, warehouse_id, "ETHYLENE_HIGH", "High ethylene level")
    else:
        auto_resolve_alert(batch_id, "ETHYLENE_HIGH")

    if latest["co2"] > ALERT_RULES["CO2_MAX"]:
        create_alert(batch_id, warehouse_id, "CO2_HIGH", "High CO₂ level")
    else:
        auto_resolve_alert(batch_id, "CO2_HIGH")

    if latest["o2"] < ALERT_RULES["O2_MIN"]:
        create_alert(batch_id, warehouse_id, "O2_LOW", "Low O₂ level")
    else:
        auto_resolve_alert(batch_id, "O2_LOW")

    # SENSOR HEALTH 
    if latest["power_status"] != "ON":
        create_alert(batch_id, warehouse_id, "POWER_FAILURE", "Sensor power off")
    else:
        auto_resolve_alert(batch_id, "POWER_FAILURE")

    # TREND
    if len(history) >= ALERT_RULES["TREND_WINDOW"]:
        eth_vals = [r["ethylene"] for r in history]
        if eth_vals[-1] - eth_vals[0] > 0.8:
            create_alert(batch_id, warehouse_id, "ETHYLENE_RISING_FAST", "Ethylene rising rapidly")
        else:
            auto_resolve_alert(batch_id, "ETHYLENE_RISING_FAST")
    else:
        auto_resolve_alert(batch_id, "ETHYLENE_RISING_FAST")
