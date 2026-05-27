from flask import current_app
from ..models.session import Session
from ..db.dynamodb import get_table


def save_session(session: Session) -> None:
    table_name = current_app.config["SESSIONS_TABLE"]
    table = get_table(table_name)
    table.put_item(Item=session.to_dynamodb_item())
