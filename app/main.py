from flask import Flask

from app.routes.products import product_bp


def create_app():
    app = Flask(__name__)

    app.register_blueprint(product_bp)

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