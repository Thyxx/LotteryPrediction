from flask import Flask

from .database import init_db


def create_app() -> Flask:
    """Application factory for the Lottery Prediction app."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-me-in-production"

    init_db()

    from .routes import bp as main_bp

    app.register_blueprint(main_bp)

    return app


app = create_app()
