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
    try:
        saved = save_bio_events(bio_request)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        return jsonify({"error": f"DynamoDB error [{code}]: {msg}"}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {type(e).__name__}: {e}"}), 500

    return jsonify({"saved": saved}), 201
