from pymongo import MongoClient

def get_database():
    CONNECTION_STRING = "mongodb://localhost:27017"
    client = MongoClient(CONNECTION_STRING)
    return client["student_accommodation"]

try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client.get_database("student_accommodation")

    print("✅ Connected to DB:", db.name)

    pg_collections = db["pg_listing"]  # <- used for hostels
    collection_requests = db["booking_requests"] 
    user_collection = db['students'] 
    owner_collection = db['owners']
    hostel_collection = db['hostels']# <- optional

except Exception as e:
    print("MongoDB Connection Error:", e)
