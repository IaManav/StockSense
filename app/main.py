import os

from flask import Flask, jsonify

from app.database import engine, Base

from app.models import (
    User,
    Warehouse,
    Location,
    Product,
    Stock,
    Receipt,
    ReceiptItem,
    Delivery,
    DeliveryItem,
    StockMove,
    StockTransfer,
    TransferItem,
)
from app.routes import api_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "development-secret-change-me")
    Base.metadata.create_all(bind=engine)

    @app.get("/")
    def root():
        return jsonify(message="StockSense API is running")

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    app.register_blueprint(api_bp, url_prefix="/api")
    return app


app = create_app()
