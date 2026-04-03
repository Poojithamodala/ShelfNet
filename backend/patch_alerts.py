from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]
alerts_col = db["alerts"]

SEVERITY_MAP = {
    "SPOILED":              "CRITICAL",
    "CRITICAL":             "CRITICAL",
    "WARNING":              "HIGH",
    "TEMP_HIGH":            "HIGH",
    "TEMP_LOW":             "HIGH",
    "HUMIDITY_LOW":         "HIGH",
    "HUMIDITY_HIGH":        "HIGH",
    "ETHYLENE_HIGH":        "HIGH",
    "ETHYLENE_RISING_FAST": "HIGH",
    "CO2_HIGH":             "HIGH",
    "O2_LOW":               "HIGH",
    "INFO":                 "LOW",
    "POWER_FAILURE":        "LOW",
}

updated = 0
for alert_type, severity in SEVERITY_MAP.items():
    result = alerts_col.update_many(
        {"alert_type": alert_type, "severity": {"$exists": False}},
        {"$set": {"severity": severity}}
    )
    updated += result.modified_count

print(f"✅ Patched {updated} alerts with severity field")