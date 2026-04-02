#!/usr/bin/env python
"""Seed a manager user with proper password."""

from pymongo import MongoClient
from datetime import datetime
import uuid
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

client = MongoClient('mongodb://localhost:27017')
db = client['shelfnet']
users_col = db['users']

# Find warehouse
warehouse = db['warehouses'].find_one({'warehouse_id': 'WH-6A42'})
if not warehouse:
    print("❌ Warehouse WH-6A42 not found")
    exit(1)

print(f"✅ Found warehouse: {warehouse['name']}")

# Check if manager exists
manager = users_col.find_one({'email': 'vellanki@gmail.com'})

if manager:
    print(f"✅ Manager {manager['email']} exists")
    
    # Update with password
    users_col.update_one(
        {'email': 'vellanki@gmail.com'},
        {
            '$set': {
                'password_hash': hash_password('Manager@123'),
                'password_set': True,
                'updated_at': datetime.utcnow()
            }
        }
    )
    print("✅ Password updated to 'Manager@123'")
else:
    print("❌ Manager user not found, creating new one...")
    
    user_id = f"U-{str(uuid.uuid4())[:4].upper()}"
    
    manager_doc = {
        'user_id': user_id,
        'email': 'vellanki@gmail.com',
        'name': 'Manager User',
        'role': 'MANAGER',
        'status': 'ACTIVE',
        'warehouse_id': 'WH-6A42',
        'password_hash': hash_password('Manager@123'),
        'password_set': True,
        'created_at': datetime.utcnow()
    }
    
    users_col.insert_one(manager_doc)
    print(f"✅ Created manager user: {user_id}")

print("\n" + "=" * 60)
print("✅ MANAGER USER READY!")
print("=" * 60)
print("\nTo login:")
print("  Email: vellanki@gmail.com")
print("  Password: Manager@123")
print("\nAfter login, manager pages should load warehouse: Apple (WH-6A42)")
