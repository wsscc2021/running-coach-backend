from flask import current_app
from ..db.dynamodb import get_table

_PK_VALUE = "collecting"


def _table():
    return get_table(current_app.config["COLLECTION_STATE_TABLE"])


def is_collecting() -> bool:
    try:
        resp = _table().get_item(Key={"configKey": _PK_VALUE})
        item = resp.get("Item")
        return bool(item.get("value", False)) if item else False
    except Exception:
        return False


def set_collecting(value: bool) -> None:
    _table().put_item(Item={"configKey": _PK_VALUE, "value": value})
