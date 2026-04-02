#!/usr/bin/env python3
import bcrypt
from pymongo import MongoClient

print("Fixing admin password hash...")

# Generate bcrypt hash directly
password = b'Admin@123'
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password, salt)
hashed_str = hashed.decode('utf-8')

print(f"New bcrypt hash: {hashed_str}")

# Update the database
client = MongoClient('mongodb://localhost:27017')
db = client['shelfnet']
users_collection = db['users']

result = users_collection.update_one(
    {'email': 'dedeepyavellanki@gmail.com'},
    {'$set': {'password_hash': hashed_str}}
)

if result.modified_count > 0:
    print("✅ Database updated with new password hash!")
    print("\nYou can now login with:")
    print("📧 Email: dedeepyavellanki@gmail.com")
    print("🔑 Password: Admin@123")
else:
    print("❌ Failed to update database")

# Verify
test_result = bcrypt.checkpw(password, hashed)
print(f"\nPassword verification test: {test_result}")
