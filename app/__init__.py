import os
from flask import Flask
from .config import configs


def create_app(env: str | None = None) -> Flask:
    env = env or os.getenv("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(configs[env])

    from .routes import register_routes
    register_routes(app)

    return app
