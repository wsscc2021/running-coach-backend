from flask import Flask
from .bio import bio_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(bio_bp, url_prefix="/v1")
