from flask import Flask, jsonify, request, Response, render_template, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from datetime import datetime
from urllib.parse import unquote
from bson.json_util import dumps
from pymongo import MongoClient
from bson import ObjectId
from db import get_database, owner_collection, user_collection, hostel_collection

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

db = get_database()
pg_collections = db["pg_listing"]

client = MongoClient("mongodb://localhost:27017/")
request_db = client["student_accommodation"]
request_collection = request_db["request"]

# ---------------------- HOSTEL ROUTES ----------------------

@app.route('/api/hostels', methods=['GET'])
def get_hostels():
    hostels_data = list(pg_collections.find({}))
    return Response(dumps(hostels_data), mimetype='application/json')

@app.route('/api/hostels/by-name/<path:hostel_name>')
def get_hostel_by_name(hostel_name):
    hostel = pg_collections.find_one({"Name": hostel_name})
    if hostel:
        hostel['_id'] = str(hostel['_id'])
        return jsonify(hostel)
    else:
        return jsonify({"error": "Hostel not found"}), 404

# ---------------------- AUTH ROUTES ----------------------

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")
    hostel_name = data.get("hostel_name")

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"})

    if role == "owner":
        if not hostel_name:
            return jsonify({"success": False, "message": "Hostel Name is required for owner signup"})
        if owner_collection.find_one({"username": hostel_name}):
            return jsonify({"success": False, "message": "Hostel already registered"})
        hashed_password = generate_password_hash(password)
        owner_collection.insert_one({
            "username": hostel_name,
            "password": hashed_password,
            "role": "owner",
            "name": data.get("name")
        })
    else:
        if user_collection.find_one({"username": username}):
            return jsonify({"success": False, "message": "User already exists"})
        hashed_password = generate_password_hash(password)
        user_collection.insert_one({
            "username": username,
            "password": hashed_password,
            "role": "user"
        })

    return jsonify({"success": True, "message": "Signup successful"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username").strip()
    password = data.get("password")
    role = data.get("role")

    if role == 'owner':
        hostel_from_pg = pg_collections.find_one({"Name": username})
        owner = owner_collection.find_one({"username": username})
        hostel = hostel_collection.find_one({"hostel_name": username}) # Fetch from hostel_collection

        if hostel_from_pg and username == password.strip():
            session['username'] = username
            # Include hostel details in the response
            hostel['_id'] = str(hostel['_id']) if hostel and '_id' in hostel else None
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'redirect': url_for('dashboard_owner'),
                'hostelDetails': hostel  # Add hostel details here
            }), 200
        elif owner and check_password_hash(owner["password"], password):
            session['username'] = username
            # Include hostel details in the response
            hostel['_id'] = str(hostel['_id']) if hostel and '_id' in hostel else None
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'redirect': url_for('dashboard_owner'),
                'hostelDetails': hostel  # Add hostel details here
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    # ... (rest of the login route for 'user')
# ---------------------- DASHBOARD ----------------------

@app.route("/dashboard/<hostel_name>", methods=["GET"])
def get_hostel_for_dashboard(hostel_name):
    decoded_name = unquote(hostel_name)
    hostel = hostel_collection.find_one({"hostel_name": decoded_name}, {"_id": 0})
    if hostel:
        return jsonify({"success": True, "hostel": hostel})
    else:
        return jsonify({"success": False, "message": "Hostel not found"})


# ---------------------- REQUEST HANDLING ----------------------

@app.route('/submit_request', methods=['POST'])
def submit_request():
    data = request.get_json()
    if not data or 'hostelId' not in data:
        return jsonify({"message": "Invalid data"}), 400

    request_doc = {
        "student_name": data.get("firstName") + " " + data.get("lastName"),
        "student_email": data.get("email"),
        "message": f"Mobile: {data.get('mobile')}",
        "hostel_id": data.get("hostelId")
    }

    request_collection.insert_one(request_doc)
    return jsonify({"message": "Request submitted successfully", "success": True})

@app.route("/api/requests/<hostel_id>")
def get_requests(hostel_id):
    requests = list(request_collection.find({"hostel_id": hostel_id}))
    for r in requests:
        r["_id"] = str(r["_id"])
    return jsonify(requests)

@app.route("/api/requests/<request_id>/update_status", methods=["POST"])
def update_request_status(request_id):
    data = request.get_json()
    new_status = data.get("status")

    request_data = request_collection.find_one({"_id": ObjectId(request_id)})
    if not request_data:
        return jsonify({"message": "Request not found"}), 404

    result = request_collection.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": new_status}}
    )

    if result.modified_count:
        return jsonify({"message": "Status updated successfully"})
    return jsonify({"message": "No changes made"}), 400



# ---------------------- SESSION & HTML ROUTES ----------------------

@app.route("/check_session")
def check_session():
    return jsonify({"username": session.get("username")})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return jsonify({"success": True, "message": "Logged out successfully"})


@app.route('/send_request', methods=['POST'])
def send_request():
    data = request.get_json()
    # Process the request data (store it in the database, send emails, etc.)
    # If the data is valid and processed successfully:
    return jsonify({'success': True})



if __name__ == "__main__":
    app.run(debug=True, port=5001)
