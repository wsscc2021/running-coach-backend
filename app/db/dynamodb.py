import boto3
from decimal import Decimal
from flask import current_app
from typing import Any

_dynamodb = None


def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        kwargs: dict[str, Any] = {"region_name": current_app.config["AWS_REGION"]}
        endpoint = current_app.config.get("DYNAMODB_ENDPOINT")
        if endpoint:
            kwargs["endpoint_url"] = endpoint
        _dynamodb = boto3.resource("dynamodb", **kwargs)
    return _dynamodb


def get_table(table_name: str):
    return get_dynamodb().Table(table_name)


def _to_decimal(item: dict) -> dict:
    """Convert float values to Decimal for DynamoDB compatibility."""
    result = {}
    for k, v in item.items():
        if isinstance(v, float):
            result[k] = Decimal(str(v))
        else:
            result[k] = v
    return result


def batch_write_items(table_name: str, items: list[dict]) -> None:
    """Write items in batches of 25 (DynamoDB BatchWriteItem limit)."""
    table = get_table(table_name)
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=_to_decimal(item))
