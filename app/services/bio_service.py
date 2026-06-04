from flask import current_app
from ..models.bio_event import BioEventRequest
from ..db.dynamodb import batch_write_items

_HEART_RATE = "heart_rate"
_CADENCE = "cadence"
_SPEED = "speed"
_OXYGEN_SATURATION = "oxygen_saturation"
_FOOT_PRESSURE = "foot_pressure"

_ROUTER = {
    _HEART_RATE:        ("HEART_RATE_TABLE",        "to_heart_rate_item"),
    _CADENCE:           ("CADENCE_TABLE",            "to_cadence_item"),
    _SPEED:             ("SPEED_TABLE",              "to_speed_item"),
    _OXYGEN_SATURATION: ("OXYGEN_SATURATION_TABLE",  "to_oxygen_saturation_item"),
    _FOOT_PRESSURE:     ("FOOT_PRESSURE_TABLE",      "to_foot_pressure_item"),
}


def save_bio_events(request: BioEventRequest) -> dict[str, int]:
    """
    sensorType별 DynamoDB 테이블 라우팅.
    _ROUTER에 없는 sensorType은 bio_events 테이블로 폴백.
    """
    if not request.events:
        return {k: 0 for k in list(_ROUTER.keys()) + ["bio_events"]}

    buckets: dict[str, list] = {k: [] for k in list(_ROUTER.keys()) + ["bio_events"]}

    for event in request.events:
        if event.sensorType in _ROUTER:
            _, method_name = _ROUTER[event.sensorType]
            item = getattr(event, method_name)(request.userId, request.deviceId, request.sessionId)
            buckets[event.sensorType].append(item)
        else:
            buckets["bio_events"].append(
                event.to_dynamodb_item(request.userId, request.deviceId, request.sessionId)
            )

    for sensor_type, items in buckets.items():
        if not items:
            continue
        if sensor_type == "bio_events":
            batch_write_items(current_app.config["BIO_EVENTS_TABLE"], items)
        else:
            table_key, _ = _ROUTER[sensor_type]
            batch_write_items(current_app.config[table_key], items)

    return {k: len(v) for k, v in buckets.items()}
