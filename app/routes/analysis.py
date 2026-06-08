from flask import Blueprint, jsonify, request
from botocore.exceptions import ClientError
from anthropic import APIStatusError
from ..services.session_service import get_session_events
from ..services.analysis_service import analyze_heart_rate, analyze_foot_pressure, detect_risks
from ..services.claude_service import generate_feedback, _friendly_api_error

analysis_bp = Blueprint("analysis", __name__)


def _fetch_events(running_id: str | None, fp_id: str | None) -> tuple[list, dict]:
    """두 세션에서 심박수·발 압력 데이터를 수집해 반환."""
    hr_data: list = []
    fp_data: dict = {}

    if running_id:
        running_events = get_session_events(running_id)
        hr_data = running_events.get("heartRate", [])
    if fp_id:
        fp_events = get_session_events(fp_id)
        fp_data = fp_events.get("footPressure", {})
        if not hr_data:
            hr_data = fp_events.get("heartRate", [])

    return hr_data, fp_data


def _db_error_response(e: ClientError):
    code = e.response["Error"]["Code"]
    msg  = e.response["Error"]["Message"]
    return jsonify({"error": f"DynamoDB error [{code}]: {msg}"}), 503


# ── GET /v1/analysis ────────────────────────────────────────────────
# 분석 데이터만 반환 (Claude 미호출)

@analysis_bp.get("/analysis")
def get_combined_analysis():
    running_id = request.args.get("runningSessionId")
    fp_id      = request.args.get("fpSessionId")

    if not running_id and not fp_id:
        return jsonify({"error": "runningSessionId or fpSessionId is required"}), 400

    try:
        hr_data, fp_data = _fetch_events(running_id, fp_id)
    except ClientError as e:
        return _db_error_response(e)
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {type(e).__name__}: {e}"}), 500

    hr_analysis = analyze_heart_rate(hr_data)
    fp_analysis = analyze_foot_pressure(fp_data)
    risks       = detect_risks(hr_analysis, fp_analysis)

    return jsonify({
        "runningSessionId": running_id,
        "fpSessionId":      fp_id,
        "heartRate":        hr_analysis,
        "footPressure":     fp_analysis,
        "risks":            risks,
    }), 200


# ── GET /v1/analysis/feedback ───────────────────────────────────────
# 버튼 클릭 시 호출 — Claude AI 피드백만 반환

@analysis_bp.get("/analysis/feedback")
def get_analysis_feedback():
    running_id = request.args.get("runningSessionId")
    fp_id      = request.args.get("fpSessionId")

    if not running_id and not fp_id:
        return jsonify({"error": "runningSessionId or fpSessionId is required"}), 400

    try:
        hr_data, fp_data = _fetch_events(running_id, fp_id)
    except ClientError as e:
        return _db_error_response(e)
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {type(e).__name__}: {e}"}), 500

    hr_analysis = analyze_heart_rate(hr_data)
    fp_analysis = analyze_foot_pressure(fp_data)
    risks       = detect_risks(hr_analysis, fp_analysis)

    session_analysis = {
        "runningSessionId": running_id,
        "fpSessionId":      fp_id,
        "heartRate":        hr_analysis,
        "footPressure":     fp_analysis,
        "risks":            risks,
    }

    try:
        feedback = generate_feedback(session_analysis)
        return jsonify({"feedback": feedback}), 200
    except APIStatusError as e:
        return jsonify({"error": _friendly_api_error(e)}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GET /v1/sessions/<id>/analysis ─────────────────────────────────
# 단일 세션 분석 (기존 호환)

@analysis_bp.get("/sessions/<session_id>/analysis")
def get_analysis(session_id: str):
    try:
        events = get_session_events(session_id)
    except ClientError as e:
        return _db_error_response(e)
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {type(e).__name__}: {e}"}), 500

    hr_analysis = analyze_heart_rate(events.get("heartRate", []))
    fp_analysis = analyze_foot_pressure(events.get("footPressure", {}))
    risks       = detect_risks(hr_analysis, fp_analysis)

    return jsonify({
        "sessionId":    session_id,
        "heartRate":    hr_analysis,
        "footPressure": fp_analysis,
        "risks":        risks,
    }), 200
