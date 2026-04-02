#!/usr/bin/env python3
"""
Seed script to create initial admin user for ShelfNet
Run this after MongoDB is running and before starting the backend
"""

from pymongo import MongoClient
from datetime import datetime
import uuid

def create_admin_user():
    client = MongoClient("mongodb://localhost:27017")
    db = client["shelfnet"]
    users_collection = db["users"]

    # Check if admin already exists
    existing_admin = users_collection.find_one({"role": "ADMIN"})
    if existing_admin:
        print("Admin user already exists!")
        print(f"Email: {existing_admin['email']}")
        return

    # Create admin user with pre-computed bcrypt hash for "Admin@123"
    admin_data = {
        "user_id": f"ADM-{str(uuid.uuid4())[:4].upper()}",
        "name": "System Administrator",
        "email": "dedeepyavellanki@gmail.com",
        "role": "ADMIN",
        "warehouse_id": None,
        "status": "ACTIVE",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfBPj6fMzt6VzAe",  # bcrypt hash for "Admin@123"
        "password_set": True,
        "created_at": datetime.utcnow()
    }

    users_collection.insert_one(admin_data)
    print("✅ Admin user created successfully!")
    print("📧 Email: dedeepyavellanki@gmail.com")
    print("🔑 Password: Admin@123") 
    print("⚠️  Please change the password after first login!")

if __name__ == "__main__":
    create_admin_user()