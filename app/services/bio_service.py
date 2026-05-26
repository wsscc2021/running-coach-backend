from flask import current_app
from ..models.bio_event import BioEventRequest
from ..db.dynamodb import batch_write_items

_HEART_RATE = "heart_rate"


def save_bio_events(request: BioEventRequest) -> dict[str, int]:
    """
    Persist events from a BioEventRequest to DynamoDB.
    heart_rate events → heart_rate_samples table
    other events      → bio_events table
    Returns a dict with saved counts per table.
    """
    if not request.events:
        return {"heart_rate": 0, "bio_events": 0}

    hr_items = []
    bio_items = []

    for event in request.events:
        if event.sensorType == _HEART_RATE:
            hr_items.append(
                event.to_heart_rate_item(request.userId, request.deviceId, request.sessionId)
            )
        else:
            bio_items.append(
                event.to_dynamodb_item(request.userId, request.deviceId, request.sessionId)
            )

    if hr_items:
        batch_write_items(current_app.config["HEART_RATE_TABLE"], hr_items)
    if bio_items:
        batch_write_items(current_app.config["BIO_EVENTS_TABLE"], bio_items)

    return {"heart_rate": len(hr_items), "bio_events": len(bio_items)}
