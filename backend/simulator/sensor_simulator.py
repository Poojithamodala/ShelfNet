import random
from datetime import datetime, timedelta
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]

batches_col = db["batches"]
sensors_col = db["sensors"]
readings_col = db["sensor_readings"]

FRUIT_PROFILES = {
    "Apple": {"temperature": (3.0, 6.0), "humidity": (85, 95), "ethylene": (1.5, 3.0)},
    "Banana": {"temperature": (13.0, 18.0), "humidity": (85, 95), "ethylene": (2.5, 6.0)},
    "Strawberry": {"temperature": (0.0, 4.0), "humidity": (90, 95), "ethylene": (0.1, 0.5)},
    "Pear": {"temperature": (0.0, 4.0), "humidity": (85, 95), "ethylene": (1.0, 3.5)},
    "Grapes": {"temperature": (0.0, 2.0), "humidity": (90, 95), "ethylene": (0.1, 0.4)},
    "Cherry": {"temperature": (0.0, 2.0), "humidity": (90, 95), "ethylene": (0.2, 0.6)},
    "Tomato": {"temperature": (12.0, 18.0), "humidity": (85, 95), "ethylene": (2.0, 5.0)}
}

def generate_reading(fruit, day_index):
    profile = FRUIT_PROFILES.get(fruit, FRUIT_PROFILES["Apple"])

    # Drift factors (simulate spoilage)
    ethylene_drift = day_index * 0.05
    co2_drift = day_index * 0.03
    o2_drift = day_index * 0.04

    return {
        "temperature": round(random.uniform(*profile["temperature"]), 2),
        "humidity": round(random.uniform(*profile["humidity"]), 2),
        "ethylene": round(min(profile["ethylene"][1], random.uniform(*profile["ethylene"]) + ethylene_drift), 2),
        "co2": round(min(2.5, random.uniform(0.6, 1.4) + co2_drift), 2),
        "o2": round(max(16.0, random.uniform(18.0, 20.5) - o2_drift), 2),
        "light": random.choice([0, 10, 50, 120]),
        "vibration": round(random.uniform(0.0, 0.05), 3),
        "power_status": "ON"
    }

def generate_future_readings(days=7, interval_minutes=30):
    print(" Generating future sensor readings...\n")

    start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    interval = timedelta(minutes=interval_minutes)

    active_batches = list(batches_col.find({"status": "ACTIVE"}, {"_id": 0}))

    total_inserted = 0

    for batch in active_batches:
        batch_id = batch["batch_id"]
        warehouse_id = batch["warehouse_id"]
        fruit = batch["fruit"]

        sensor = sensors_col.find_one(
            {"current_batch_id": batch_id},
            {"_id": 0}
        )

        if not sensor:
            print(f"⚠ No sensor for batch {batch_id}")
            continue

        for day in range(days):
            current_time = start_time + timedelta(days=day)

            for _ in range(int(24 * 60 / interval_minutes)):
                reading = generate_reading(fruit, day)

                doc = {
                    "batch_id": batch_id,
                    "sensor_id": sensor["sensor_id"],
                    "warehouse_id": warehouse_id,
                    "timestamp": current_time,
                    **reading
                }

                readings_col.insert_one(doc)
                total_inserted += 1

                current_time += interval

    print(f"\n Done! Inserted {total_inserted} readings.")
    print(" Data now spans multiple days and is ML-ready.")

if __name__ == "__main__":
    generate_future_readings(days=7, interval_minutes=30)
