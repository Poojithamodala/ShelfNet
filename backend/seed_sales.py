#!/usr/bin/env python
"""Seed a sales user with proper password."""

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

# Check if sales user exists
sales_user = users_col.find_one({'email': 'sales@shelfnet.com'})

if sales_user:
    print(f"✅ Sales user {sales_user['email']} exists")

    # Update with password
    users_col.update_one(
        {'email': 'sales@shelfnet.com'},
        {
            '$set': {
                'password_hash': hash_password('Sales@123'),
                'password_set': True,
                'updated_at': datetime.utcnow()
            }
        }
    )
    print("✅ Password updated to 'Sales@123'")
else:
    print("❌ Sales user not found, creating new one...")

    user_id = f"U-{str(uuid.uuid4())[:4].upper()}"

    sales_doc = {
        'user_id': user_id,
        'email': 'sales@shelfnet.com',
        'name': 'Sales User',
        'role': 'SALES',
        'status': 'ACTIVE',
        'warehouse_id': 'WH-6A42',
        'password_hash': hash_password('Sales@123'),
        'password_set': True,
        'created_at': datetime.utcnow()
    }

    users_col.insert_one(sales_doc)
    print(f"✅ Created sales user: {user_id}")

print("\n" + "=" * 60)
print("✅ SALES USER READY!")
print("=" * 60)
print("\nTo login:")
print("  Email: sales@shelfnet.com")
print("  Password: Sales@123")
print("\nAfter login, sales pages should load warehouse: Apple (WH-6A42)")