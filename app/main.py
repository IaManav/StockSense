from fastapi import FastAPI

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
)


app = FastAPI(
    title="StockSense API",
    version="1.0.0"
)


# Create database tables
Base.metadata.create_all(bind=engine)


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