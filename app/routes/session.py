from flask import Blueprint, request, jsonify
from botocore.exceptions import ClientError
from ..models.session import Session
from ..services.session_service import save_session

session_bp = Blueprint("session", __name__)


@session_bp.post("/sessions")
def post_session():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON"}), 400

    required = {"sessionId", "userId", "deviceId", "startTime", "endTime"}
    missing = required - body.keys()
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    session = Session.from_dict(body)
    try:
        save_session(session)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        return jsonify({"error": f"DynamoDB error [{code}]: {msg}"}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {type(e).__name__}: {e}"}), 500

    return jsonify({"sessionId": session.sessionId}), 201
