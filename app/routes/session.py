from flask import Blueprint, request, jsonify
from botocore.exceptions import ClientError
from ..models.session import Session
from ..services.session_service import save_session, get_sessions_by_user, get_session_events

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


@session_bp.get("/sessions")
def list_sessions():
    user_id = request.args.get("userId")
    if not user_id:
        return jsonify({"error": "userId query parameter is required"}), 400

    try:
        sessions = get_sessions_by_user(user_id)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        return jsonify({"error": f"DynamoDB error [{code}]: {msg}"}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {type(e).__name__}: {e}"}), 500

    return jsonify({"sessions": sessions}), 200


@session_bp.get("/sessions/<session_id>/events")
def get_events(session_id: str):
    try:
        events = get_session_events(session_id)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        return jsonify({"error": f"DynamoDB error [{code}]: {msg}"}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {type(e).__name__}: {e}"}), 500

    return jsonify(events), 200
