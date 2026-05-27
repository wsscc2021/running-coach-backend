from boto3.dynamodb.conditions import Attr, Key
from flask import current_app
from ..models.session import Session
from ..db.dynamodb import get_table


def save_session(session: Session) -> None:
    table = get_table(current_app.config["SESSIONS_TABLE"])
    table.put_item(Item=session.to_dynamodb_item())


def get_sessions_by_user(user_id: str) -> list[dict]:
    table = get_table(current_app.config["SESSIONS_TABLE"])
    # Production에서는 userId GSI 권장 — 현재는 Scan + FilterExpression 사용
    response = table.scan(FilterExpression=Attr("userId").eq(user_id))
    items = response.get("Items", [])
    items.sort(key=lambda x: x.get("startTime", ""), reverse=True)
    return items


def get_session_events(session_id: str) -> dict:
    def query_sensor(table_key: str, fields: list[str]) -> list[dict]:
        table = get_table(current_app.config[table_key])
        response = table.query(
            KeyConditionExpression=Key("sessionId").eq(session_id)
        )
        rows = sorted(response.get("Items", []), key=lambda x: x["measuredAt"])
        return [{f: row[f] for f in fields if f in row} for row in rows]

    heart_rate = query_sensor("HEART_RATE_TABLE", ["measuredAt", "bpm"])
    cadence    = query_sensor("CADENCE_TABLE",    ["measuredAt", "stepsPerMinute"])
    speed      = query_sensor("SPEED_TABLE",      ["measuredAt", "metersPerSecond"])
    spo2       = query_sensor("OXYGEN_SATURATION_TABLE", ["measuredAt", "percentage"])

    return {
        "sessionId": session_id,
        "heartRate": [
            {"measuredAt": r["measuredAt"], "bpm": int(r["bpm"])} for r in heart_rate
        ],
        "cadence": [
            {"measuredAt": r["measuredAt"], "stepsPerMinute": float(r["stepsPerMinute"])} for r in cadence
        ],
        "speed": [
            {"measuredAt": r["measuredAt"], "metersPerSecond": float(r["metersPerSecond"])} for r in speed
        ],
        "oxygenSaturation": [
            {"measuredAt": r["measuredAt"], "percentage": float(r["percentage"])} for r in spo2
        ],
    }
