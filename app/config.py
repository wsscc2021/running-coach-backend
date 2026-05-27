import os


class Config:
    AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
    DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT")  # local override (e.g. DynamoDB Local)
    BIO_EVENTS_TABLE = os.getenv("BIO_EVENTS_TABLE", "bio_events")
    HEART_RATE_TABLE = os.getenv("HEART_RATE_TABLE", "heart_rate")
    BLOOD_PRESSURE_TABLE = os.getenv("BLOOD_PRESSURE_TABLE", "blood_pressure")


class DevelopmentConfig(Config):
    DEBUG = True
    # DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")


class ProductionConfig(Config):
    DEBUG = False


configs = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
