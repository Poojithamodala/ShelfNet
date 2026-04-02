#!/usr/bin/env python
"""Test warehouse endpoint and debug the mismatch."""

import requests
import sys
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['shelfnet']

# Get warehouse data
warehouses = list(db['warehouses'].find({}, {'warehouse_id': 1, 'name': 1, '_id': 0}))
users = list(db['users'].find({'role': 'MANAGER'}, {'email': 1, 'warehouse_id': 1, '_id': 0}))

print("=" * 60)
print("DATABASE STATE")
print("=" * 60)

print("\nWarehouses in DB:")
for w in warehouses:
    print(f"  warehouse_id: {w.get('warehouse_id')}")
    print(f"  name: {w.get('name')}")

print("\nManager Users in DB:")
for u in users:
    print(f"  email: {u.get('email')}")
    print(f"  warehouse_id: {u.get('warehouse_id')}")

if not warehouses:
    print("\n⚠️  NO WAREHOUSES FOUND IN DB")
    sys.exit(1)

if not users:
    print("\n⚠️  NO MANAGER USERS FOUND IN DB")
    sys.exit(1)

# Test endpoint
print("\n" + "=" * 60)
print("TESTING BACKEND ENDPOINT")
print("=" * 60)

warehouse_id = warehouses[0]['warehouse_id']
test_url = f"http://127.0.0.1:8000/warehouses/{warehouse_id}"

print(f"\nTesting: GET {test_url}")

try:
    response = requests.get(test_url)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    
    if response.status_code == 200:
        print("\n✅ Endpoint working!")
    else:
        print(f"\n❌ Endpoint returned {response.status_code}")
except Exception as e:
    print(f"\n❌ Cannot reach backend: {str(e)}")
    print("\nBACKEND IS NOT RUNNING!")
    print("\nTo start backend, run:")
    print("  cd C:\\Major Project\\ShelfNet\\backend")
    print("  python -m uvicorn main:app --host 0.0.0.0 --port 8000")
