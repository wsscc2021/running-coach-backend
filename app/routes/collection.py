from flask import Blueprint, request, jsonify
from ..services.collection_state import is_collecting, set_collecting

collection_bp = Blueprint("collection", __name__)


@collection_bp.get("/collection")
def get_collection_state():
    return jsonify({"collecting": is_collecting()}), 200


@collection_bp.put("/collection")
def set_collection_state():
    body = request.get_json(silent=True)
    if not body or "collecting" not in body:
        return jsonify({"error": "Missing field: collecting"}), 400
    if not isinstance(body["collecting"], bool):
        return jsonify({"error": "collecting must be a boolean"}), 400

    set_collecting(body["collecting"])
    return jsonify({"collecting": is_collecting()}), 200
