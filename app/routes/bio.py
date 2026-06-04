from flask import Blueprint, request, jsonify
from botocore.exceptions import ClientError
from ..models.bio_event import BioEventRequest
from ..services.bio_service import save_bio_events
from ..services.collection_state import is_collecting

bio_bp = Blueprint("bio", __name__)


@bio_bp.post("/bio/events")
def post_bio_events():
    if not is_collecting():
        return jsonify({"error": "Data collection is currently inactive"}), 423

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON"}), 400

    required = {"userId", "deviceId", "sessionId", "events"}
    missing = required - body.keys()
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    bio_request = BioEventRequest.from_dict(body)

    for e in bio_request.events:
        if e.sensorType == "foot_pressure":
            if e.footSide not in ("left", "right"):
                return jsonify({"error": f"foot_pressure event {e.eventId}: footSide must be 'left' or 'right'"}), 400
            if len(e.values) != 6:
                return jsonify({"error": f"foot_pressure event {e.eventId}: values must have exactly 6 elements"}), 400
            if not all(0 <= v <= 4095 for v in e.values):
                return jsonify({"error": f"foot_pressure event {e.eventId}: all sensor values must be in range 0-4095"}), 400

    try:
        saved = save_bio_events(bio_request)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        return jsonify({"error": f"DynamoDB error [{code}]: {msg}"}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {type(e).__name__}: {e}"}), 500

    return jsonify({"saved": saved}), 201
