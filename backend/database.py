from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["shelfnet"]

users_collection = db["users"]
warehouses_collection = db["warehouses"]
batches_collection = db["batches"]
sensors_collection = db["sensors"]
sensor_readings_collection = db["sensor_readings"]
predictions_collection = db["predictions"]
alerts_collection = db["alerts"]
actions_collection = db["actions_log"]
