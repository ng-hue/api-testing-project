"""Tiny REST API for public records requests (capstone-style prototype, in-memory)."""
from flask import Flask, jsonify, request

app = Flask(__name__)
VALID_STATUS = {"submitted", "in_review", "fulfilled", "denied"}
db = {}
next_id = 1

def reset():
    global next_id
    db.clear(); next_id = 1

@app.get("/requests")
def list_requests():
    status = request.args.get("status")
    items = [r for r in db.values() if status is None or r["status"] == status]
    return jsonify(items), 200

@app.post("/requests")
def create_request():
    global next_id
    body = request.get_json(silent=True) or {}
    agency = str(body.get("agency", "")).strip()
    subject = str(body.get("subject", "")).strip()
    if not agency or not subject:
        return jsonify(error="agency and subject are required"), 400
    item = {"id": next_id, "agency": agency, "subject": subject, "status": "submitted"}
    db[next_id] = item; next_id += 1
    return jsonify(item), 201

@app.get("/requests/<int:rid>")
def get_request(rid):
    if rid not in db:
        return jsonify(error="not found"), 404
    return jsonify(db[rid]), 200

@app.patch("/requests/<int:rid>")
def update_status(rid):
    if rid not in db:
        return jsonify(error="not found"), 404
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in VALID_STATUS:
        return jsonify(error=f"status must be one of {sorted(VALID_STATUS)}"), 422
    db[rid]["status"] = status
    return jsonify(db[rid]), 200

@app.delete("/requests/<int:rid>")
def delete_request(rid):
    if db.pop(rid, None) is None:
        return jsonify(error="not found"), 404
    return "", 204

if __name__ == "__main__":
    app.run(port=5000)
