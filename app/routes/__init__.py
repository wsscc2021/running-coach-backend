from flask import Flask
from .bio import bio_bp
from .session import session_bp
from .collection import collection_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(bio_bp, url_prefix="/v1")
    app.register_blueprint(session_bp, url_prefix="/v1")
    app.register_blueprint(collection_bp, url_prefix="/v1")
