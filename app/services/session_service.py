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

    # ── 발 압력 집계 (핀별 평균, 0-4095) ──────────────────────────────
    fp_table = get_table(current_app.config["FOOT_PRESSURE_TABLE"])
    fp_items = fp_table.query(
        KeyConditionExpression=Key("sessionId").eq(session_id)
    ).get("Items", [])

    fp_sums: dict[str, list] = {"left": [0] * 6, "right": [0] * 6}
    fp_counts: dict[str, int] = {"left": 0, "right": 0}
    for item in fp_items:
        side = item.get("footSide")
        vals = item.get("values", [])
        if side in fp_sums and len(vals) == 6:
            for i, v in enumerate(vals):
                fp_sums[side][i] += int(v)
            fp_counts[side] += 1

    foot_pressure = {}
    for side in ("left", "right"):
        n = fp_counts[side]
        if n:
            foot_pressure[side] = [round(fp_sums[side][i] / n) for i in range(6)]

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
        "footPressure": foot_pressure,
    }
