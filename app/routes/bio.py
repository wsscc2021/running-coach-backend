from flask import Blueprint, request, jsonify
from ..models.bio_event import BioEventRequest
from ..services.bio_service import save_bio_events

bio_bp = Blueprint("bio", __name__)


@bio_bp.post("/bio/events")
def post_bio_events():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON"}), 400

    required = {"userId", "deviceId", "events"}
    missing = required - body.keys()
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    bio_request = BioEventRequest.from_dict(body)
    saved = save_bio_events(bio_request)
    return jsonify({"saved": saved}), 201
