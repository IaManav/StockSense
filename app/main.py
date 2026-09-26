from flask import Flask

from app.config import secret_key
from app.database import init_app
from app.routes.flask_api import api_bp


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=secret_key(),
    )

    init_app(app)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/")
    def root():
        return {
            "message": "StockSense API is running"
        }

    @app.get("/health")
    def health():
        return {
            "status": "ok"
        }

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
    )
