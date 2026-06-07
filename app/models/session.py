from dataclasses import dataclass


@dataclass
class Session:
    sessionId: str
    userId: str
    deviceId: str
    startTime: str
    endTime: str
    sessionType: str = "running"   # "running" | "foot_pressure"

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            sessionId=data["sessionId"],
            userId=data["userId"],
            deviceId=data["deviceId"],
            startTime=data["startTime"],
            endTime=data["endTime"],
            sessionType=data.get("sessionType", "running"),
        )

    def to_dynamodb_item(self) -> dict:
        return {
            "sessionId": self.sessionId,
            "userId": self.userId,
            "deviceId": self.deviceId,
            "startTime": self.startTime,
            "endTime": self.endTime,
            "sessionType": self.sessionType,
        }
