import os, json, sys
from flask import Flask, request, jsonify
from pymongo import MongoClient
from urllib.parse import quote_plus
app = Flask(__name__)
def get_uri():
    password=""
    with open("/var/openfaas/secrets/mongo-db-password") as f:
        password = f.read()

    return "mongodb://%s:%s@%s" % (
        quote_plus("root"), quote_plus(password), os.getenv("mongo_host"))

def get_followers():
    try:
        uri = get_uri()
        client = MongoClient(uri)
        db = client['openfaas']
        followers = db.followers
        return followers
    except Exception as e:
        sys.stderr.write(f"Error connecting to MongoDB: {e}\n")
        raise

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle(req):
    """Handle incoming HTTP requests."""
    method = request.method
    sys.stderr.write(f"Method: {method}\n")

    try:
        followers = get_followers()
    except Exception:
        return jsonify({"error": "Database connection failed."}), 500

    if method in ["POST", "PUT"]:
        username = request.get_data(as_text=True).strip()
        if not username:
            return jsonify({"error": "Username is required for insertion."}), 400

        follower = {"username": username}
        try:
            res = followers.insert_one(follower)
            return jsonify({"message": f"Record inserted: {res.inserted_id}"}), 201
        except Exception as e:
            sys.stderr.write(f"Insert Error: {e}\n")
            return jsonify({"error": "Failed to insert record."}), 500

    elif method == "GET":
        try:
            ret = [{"username": follower['username']} for follower in followers.find()]
            return jsonify(ret), 200
        except Exception as e:
            sys.stderr.write(f"Get Error: {e}\n")
            return jsonify({"error": "Failed to retrieve records."}), 500

    elif method == "DELETE":
        username = request.get_data(as_text=True).strip()
        if not username:
            return jsonify({"error": "Username is required for deletion."}), 400

        try:
            result = followers.delete_one({"username": username})
            if result.deleted_count == 1:
                return jsonify({"message": f"Record with username '{username}' deleted."}), 200
            else:
                return jsonify({"message": f"No record found with username '{username}'."}), 404
        except Exception as e:
            sys.stderr.write(f"Delete Error: {e}\n")
            return jsonify({"error": "Failed to delete record."}), 500

    else:
        return "Method: {} not supported".format(method)

