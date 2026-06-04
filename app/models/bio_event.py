from dataclasses import dataclass, field


@dataclass
class BioEvent:
    eventId: str
    sensorType: str
    measuredAt: str
    value: float = 0.0
    unit: str = ""
    footSide: str = ""              # foot pressure: "left" | "right"
    values: list[int] = field(default_factory=list)  # foot pressure: 6 sensors, 0-4095

    @classmethod
    def from_dict(cls, data: dict) -> "BioEvent":
        return cls(
            eventId=data["eventId"],
            sensorType=data["sensorType"],
            measuredAt=data["measuredAt"],
            value=float(data.get("value", 0.0)),
            unit=data.get("unit", ""),
            footSide=data.get("footSide", ""),
            values=[int(v) for v in data.get("values", [])],
        )

    def to_dynamodb_item(self, user_id: str, device_id: str, session_id: str) -> dict:
        return {
            "sessionId": session_id,
            "eventId": self.eventId,
            "userId": user_id,
            "deviceId": device_id,
            "sensorType": self.sensorType,
            "measuredAt": self.measuredAt,
            "value": str(self.value),
            "unit": self.unit,
        }

    def to_heart_rate_item(self, user_id: str, device_id: str, session_id: str) -> dict:
        return {
            "sessionId": session_id,
            "eventId": self.eventId,
            "userId": user_id,
            "deviceId": device_id,
            "measuredAt": self.measuredAt,
            "bpm": int(self.value),
        }

    def to_cadence_item(self, user_id: str, device_id: str, session_id: str) -> dict:
        return {
            "sessionId": session_id,
            "eventId": self.eventId,
            "userId": user_id,
            "deviceId": device_id,
            "measuredAt": self.measuredAt,
            "stepsPerMinute": str(self.value),
        }

    def to_speed_item(self, user_id: str, device_id: str, session_id: str) -> dict:
        return {
            "sessionId": session_id,
            "eventId": self.eventId,
            "userId": user_id,
            "deviceId": device_id,
            "measuredAt": self.measuredAt,
            "metersPerSecond": str(self.value),
        }

    def to_oxygen_saturation_item(self, user_id: str, device_id: str, session_id: str) -> dict:
        return {
            "sessionId": session_id,
            "eventId": self.eventId,
            "userId": user_id,
            "deviceId": device_id,
            "measuredAt": self.measuredAt,
            "percentage": str(self.value),
        }

    def to_foot_pressure_item(self, user_id: str, device_id: str, session_id: str) -> dict:
        return {
            "sessionId": session_id,
            "eventId": self.eventId,
            "userId": user_id,
            "deviceId": device_id,
            "measuredAt": self.measuredAt,
            "footSide": self.footSide,
            "values": self.values,
        }


@dataclass
class BioEventRequest:
    userId: str
    deviceId: str
    sessionId: str
    events: list[BioEvent]

    @classmethod
    def from_dict(cls, data: dict) -> "BioEventRequest":
        return cls(
            userId=data["userId"],
            deviceId=data["deviceId"],
            sessionId=data["sessionId"],
            events=[BioEvent.from_dict(e) for e in data.get("events", [])],
        )
