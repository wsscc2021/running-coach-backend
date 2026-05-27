from flask import current_app
from ..models.bio_event import BioEventRequest
from ..db.dynamodb import batch_write_items

_HEART_RATE = "heart_rate"
_BLOOD_PRESSURE = "blood_pressure"


def save_bio_events(request: BioEventRequest) -> dict[str, int]:
    """
    sensorType별 라우팅:
      heart_rate     → heart_rate table
      blood_pressure → blood_pressure table
      그 외           → bio_events table
    """
    if not request.events:
        return {"heart_rate": 0, "blood_pressure": 0, "bio_events": 0}

    hr_items, bp_items, bio_items = [], [], []

    for event in request.events:
        if event.sensorType == _HEART_RATE:
            hr_items.append(
                event.to_heart_rate_item(request.userId, request.deviceId, request.sessionId)
            )
        elif event.sensorType == _BLOOD_PRESSURE:
            bp_items.append(
                event.to_blood_pressure_item(request.userId, request.deviceId, request.sessionId)
            )
        else:
            bio_items.append(
                event.to_dynamodb_item(request.userId, request.deviceId, request.sessionId)
            )

    if hr_items:
        batch_write_items(current_app.config["HEART_RATE_TABLE"], hr_items)
    if bp_items:
        batch_write_items(current_app.config["BLOOD_PRESSURE_TABLE"], bp_items)
    if bio_items:
        batch_write_items(current_app.config["BIO_EVENTS_TABLE"], bio_items)

    return {"heart_rate": len(hr_items), "blood_pressure": len(bp_items), "bio_events": len(bio_items)}
