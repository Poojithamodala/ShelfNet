import random
import uuid
from datetime import datetime, timedelta
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]

batches_col  = db["batches"]
sensors_col  = db["sensors"]
readings_col = db["sensor_readings"]

FRUIT_PROFILES = {
    "Apple":      {"temperature": (3.0,  6.0),  "humidity": (85, 95), "ethylene": (1.5, 3.0)},
    "Apples":     {"temperature": (3.0,  6.0),  "humidity": (85, 95), "ethylene": (1.5, 3.0)},
    "Banana":     {"temperature": (13.0, 18.0), "humidity": (85, 95), "ethylene": (2.5, 6.0)},
    "Strawberry": {"temperature": (0.0,  4.0),  "humidity": (90, 95), "ethylene": (0.1, 0.5)},
    "Pear":       {"temperature": (0.0,  4.0),  "humidity": (85, 95), "ethylene": (1.0, 3.5)},
    "Grapes":     {"temperature": (0.0,  2.0),  "humidity": (90, 95), "ethylene": (0.1, 0.4)},
    "Cherry":     {"temperature": (0.0,  2.0),  "humidity": (90, 95), "ethylene": (0.2, 0.6)},
    "Tomato":     {"temperature": (12.0, 18.0), "humidity": (85, 95), "ethylene": (2.0, 5.0)},
    "Oranges":    {"temperature": (5.0,  8.0),  "humidity": (88, 93), "ethylene": (0.1, 1.0)},
    "Mango":      {"temperature": (10.0, 13.0), "humidity": (85, 92), "ethylene": (0.3, 3.0)},
}

DEFAULT_PROFILE = {"temperature": (5.0, 10.0), "humidity": (85, 92), "ethylene": (0.2, 2.0)}


def get_profile(fruit: str) -> dict:
    return FRUIT_PROFILES.get(fruit, DEFAULT_PROFILE)


def get_or_create_sensor(batch: dict) -> dict:
    """
    Returns an existing sensor assigned to this batch,
    or creates and assigns a new one automatically.
    """
    batch_id     = batch["batch_id"]
    warehouse_id = batch["warehouse_id"]

    # Check if sensor already assigned
    sensor = sensors_col.find_one({"current_batch_id": batch_id}, {"_id": 0})
    if sensor:
        return sensor

    # Create a new sensor for this batch
    sensor_id = f"SNS-{uuid.uuid4().hex[:4].upper()}"
    sensor_doc = {
        "sensor_id":        sensor_id,
        "warehouse_id":     warehouse_id,
        "location":         "Cold Storage Unit A",
        "current_batch_id": batch_id,
        "status":           "ACTIVE",
        "installed_at":     datetime.utcnow(),
        "registered_by":    "SYSTEM"
    }
    sensors_col.insert_one(sensor_doc)
    print(f"  🔧 Auto-created sensor {sensor_id} for batch {batch_id}")

    return sensor_doc


def generate_reading(fruit: str, day_index: int) -> dict:
    profile = get_profile(fruit)

    ethylene_drift = day_index * 0.05
    co2_drift      = day_index * 0.03
    o2_drift       = day_index * 0.04

    return {
        "temperature": round(random.uniform(*profile["temperature"]), 2),
        "humidity":    round(random.uniform(*profile["humidity"]), 2),
        "ethylene":    round(min(profile["ethylene"][1], random.uniform(*profile["ethylene"]) + ethylene_drift), 2),
        "co2":         round(min(2.5, random.uniform(0.6, 1.4) + co2_drift), 2),
        "o2":          round(max(16.0, random.uniform(18.0, 20.5) - o2_drift), 2),
        "light":       random.choice([0, 10, 50, 120]),
        "vibration":   round(random.uniform(0.0, 0.05), 3),
        "power_status": "ON"
    }


def generate_future_readings(days: int = 7, interval_minutes: int = 30):
    print("=" * 50)
    print("  ShelfNet — Sensor Reading Generator")
    print("=" * 50)

    # Fetch ALL active batches across ALL warehouses dynamically
    active_batches = list(batches_col.find({"status": "ACTIVE"}, {"_id": 0}))

    if not active_batches:
        print("\n❌ No active batches found. Add batches first.")
        return

    print(f"\nFound {len(active_batches)} active batch(es) across all warehouses:\n")

    start_time = (
        datetime.utcnow()
        .replace(hour=0, minute=0, second=0, microsecond=0)
        + timedelta(days=1)
    )
    interval = timedelta(minutes=interval_minutes)

    total_inserted = 0

    for batch in active_batches:
        batch_id     = batch["batch_id"]
        warehouse_id = batch["warehouse_id"]
        fruit        = batch.get("fruit", "Unknown")

        print(f"📦 {batch_id} | {fruit} | Warehouse: {warehouse_id}")

        # ✅ Auto-create sensor if missing — no manual setup needed
        sensor = get_or_create_sensor(batch)
        sensor_id = sensor["sensor_id"]

        batch_inserted = 0

        for day in range(days):
            current_time = start_time + timedelta(days=day)

            readings_per_day = int(24 * 60 / interval_minutes)
            for _ in range(readings_per_day):
                reading = generate_reading(fruit, day)

                doc = {
                    "batch_id":     batch_id,
                    "sensor_id":    sensor_id,
                    "warehouse_id": warehouse_id,
                    "timestamp":    current_time,
                    **reading
                }

                readings_col.insert_one(doc)
                batch_inserted += 1
                current_time += interval

        total_inserted += batch_inserted
        print(f"  ✅ {batch_inserted} readings inserted "
              f"({days} days × {int(24 * 60 / interval_minutes)} readings/day)\n")

    print("=" * 50)
    print(f"✅ Done! Total readings inserted: {total_inserted}")
    print(f"   Warehouses covered: {len(set(b['warehouse_id'] for b in active_batches))}")
    print(f"   Batches covered   : {len(active_batches)}")
    print("\n▶  You can now run:")
    print("     cd ml")
    print("     python train_lstm.py")
    print("=" * 50)


if __name__ == "__main__":
    generate_future_readings(days=7, interval_minutes=30)