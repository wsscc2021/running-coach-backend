from dataclasses import dataclass
from typing import Optional


@dataclass
class BioEvent:
    eventId: str
    sensorType: str
    measuredAt: str
    value: float
    unit: str
    secondaryValue: Optional[float] = None  # blood_pressure: diastolic(mmHg)

    @classmethod
    def from_dict(cls, data: dict) -> "BioEvent":
        raw_secondary = data.get("secondaryValue")
        return cls(
            eventId=data["eventId"],
            sensorType=data["sensorType"],
            measuredAt=data["measuredAt"],
            value=float(data["value"]),
            unit=data["unit"],
            secondaryValue=float(raw_secondary) if raw_secondary is not None else None,
        )

    def to_dynamodb_item(self, user_id: str, device_id: str, session_id: Optional[str]) -> dict:
        item = {
            "userId": user_id,
            "eventId": self.eventId,
            "deviceId": device_id,
            "sensorType": self.sensorType,
            "measuredAt": self.measuredAt,
            "value": str(self.value),
            "unit": self.unit,
        }
        if session_id:
            item["sessionId"] = session_id
        return item

    def to_heart_rate_item(self, user_id: str, device_id: str, session_id: Optional[str]) -> dict:
        item = {
            "userId": user_id,
            "eventId": self.eventId,
            "deviceId": device_id,
            "measuredAt": self.measuredAt,
            "bpm": int(self.value),
        }
        if session_id:
            item["sessionId"] = session_id
        return item

    def to_blood_pressure_item(self, user_id: str, device_id: str, session_id: Optional[str]) -> dict:
        item = {
            "userId": user_id,
            "eventId": self.eventId,
            "deviceId": device_id,
            "measuredAt": self.measuredAt,
            "systolic": str(self.value),
            "diastolic": str(self.secondaryValue) if self.secondaryValue is not None else None,
        }
        if item["diastolic"] is None:
            del item["diastolic"]
        if session_id:
            item["sessionId"] = session_id
        return item


@dataclass
class BioEventRequest:
    userId: str
    deviceId: str
    sessionId: Optional[str]
    events: list[BioEvent]

    @classmethod
    def from_dict(cls, data: dict) -> "BioEventRequest":
        return cls(
            userId=data["userId"],
            deviceId=data["deviceId"],
            sessionId=data.get("sessionId"),
            events=[BioEvent.from_dict(e) for e in data.get("events", [])],
        )
