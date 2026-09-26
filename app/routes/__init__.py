"""StockSense Flask API route blueprints."""

from .auth_routes import auth_bp
from .user_routes import user_bp
from .warehouse_routes import warehouse_bp
from .location_routes import location_bp
from .category_routes import category_bp
from .product_routes import product_bp
from .stock_routes import stock_bp
from .receipt_routes import receipt_bp
from .delivery_routes import delivery_bp
from .transfer_routes import transfer_bp
from .adjustment_routes import adjustment_bp
from .ledger_routes import ledger_bp
from .dashboard_routes import dashboard_bp
