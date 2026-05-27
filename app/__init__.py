import os
from flask import Flask
from flask_cors import CORS
from .config import configs


def create_app(env: str | None = None) -> Flask:
    env = env or os.getenv("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(configs[env])

    CORS(app, resources={r"/v1/*": {"origins": "*"}})

    from .routes import register_routes
    register_routes(app)

    return app
