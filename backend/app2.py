from flask import Flask, jsonify
from flask_pymongo import PyMongo

app = Flask(__name__)

# Configuring MongoDB URI for Flask-PyMongo
app.config["MONGO_URI"] = "mongodb://localhost:27017/student_accommodation"  # This is the URI for your MongoDB

# Initialize PyMongo with the Flask app
mongo = PyMongo(app)

@app.route("/api/requests", methods=["GET"])
def get_requests():
    # Access the 'request' collection from the 'student_accomodation' database
    requests_collection = mongo.db.request  # 'request' is the collection name
    requests = list(requests_collection.find())  # Fetch all the documents from the collection
    
    return jsonify(requests)  # Return the documents as JSON

if __name__ == "__main__":
    app.run(debug=True, port=5002)
