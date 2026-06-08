from flask import Blueprint, jsonify, request
from botocore.exceptions import ClientError
from anthropic import APIStatusError
from ..services.session_service import get_session_events
from ..services.analysis_service import analyze_heart_rate, analyze_foot_pressure, detect_risks
from ..services.claude_service import generate_feedback, _friendly_api_error

analysis_bp = Blueprint("analysis", __name__)


def _build_and_respond(hr_data: list, fp_data: dict, meta: dict) -> tuple:
    hr_analysis = analyze_heart_rate(hr_data)
    fp_analysis = analyze_foot_pressure(fp_data)
    risks = detect_risks(hr_analysis, fp_analysis)

    session_analysis = {
        **meta,
        "heartRate": hr_analysis,
        "footPressure": fp_analysis,
        "risks": risks,
    }

    feedback = None
    feedback_error = None
    try:
        feedback = generate_feedback(session_analysis)
    except APIStatusError as e:
        feedback_error = _friendly_api_error(e)
    except Exception as e:
        feedback_error = str(e)

    response = {**session_analysis, "feedback": feedback}
    if feedback_error:
        response["feedbackError"] = feedback_error

    return jsonify(response), 200


@analysis_bp.get("/sessions/<session_id>/analysis")
def get_analysis(session_id: str):
    try:
        events = get_session_events(session_id)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        return jsonify({"error": f"DynamoDB error [{code}]: {msg}"}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {type(e).__name__}: {e}"}), 500

    return _build_and_respond(
        hr_data=events.get("heartRate", []),
        fp_data=events.get("footPressure", {}),
        meta={"sessionId": session_id},
    )


@analysis_bp.get("/analysis")
def get_combined_analysis():
    """
    러닝 세션(심박수)과 발 압력 세션을 각각 지정해 통합 분석.
    runningSessionId, fpSessionId 중 하나 이상 필요.
    """
    running_id = request.args.get("runningSessionId")
    fp_id = request.args.get("fpSessionId")

    if not running_id and not fp_id:
        return jsonify({"error": "runningSessionId or fpSessionId is required"}), 400

    hr_data: list = []
    fp_data: dict = {}

    try:
        if running_id:
            running_events = get_session_events(running_id)
            hr_data = running_events.get("heartRate", [])
        if fp_id:
            fp_events = get_session_events(fp_id)
            fp_data = fp_events.get("footPressure", {})
            if not hr_data:
                hr_data = fp_events.get("heartRate", [])
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        return jsonify({"error": f"DynamoDB error [{code}]: {msg}"}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {type(e).__name__}: {e}"}), 500

    return _build_and_respond(
        hr_data=hr_data,
        fp_data=fp_data,
        meta={"runningSessionId": running_id, "fpSessionId": fp_id},
    )
