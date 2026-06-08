"""
Input validation for order parameters.

Each validator raises a descriptive ValueError on bad input so the CLI
can surface a friendly message before any network call is made.
"""

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Optional

logger = logging.getLogger(__name__)

# ── Allowed values ────────────────────────────────────────────────────────────

VALID_SIDES = {"BUY", "SELL"}

VALID_ORDER_TYPES = {
    "MARKET",
    "LIMIT",
    "STOP",           # bonus: stop-limit
    "STOP_MARKET",    # bonus: stop-market
    "TAKE_PROFIT",
    "TAKE_PROFIT_MARKET",
}

# Order types that need a limit price
PRICE_REQUIRED = {"LIMIT", "STOP", "TAKE_PROFIT"}

# Order types that need a stop/trigger price
STOP_PRICE_REQUIRED = {"STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"}

# Order types that need timeInForce
TIME_IN_FORCE_REQUIRED = {"LIMIT", "STOP", "TAKE_PROFIT"}


# ── Field validators ──────────────────────────────────────────────────────────

def validate_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if not re.fullmatch(r"[A-Z0-9]{2,20}", symbol):
        raise ValueError(
            f"Invalid symbol '{symbol}'. Use alphanumeric characters only (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Supported types: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str) -> str:
    try:
        qty = Decimal(str(quantity).strip())
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than 0 (got {qty}).")
    # Return as a plain string to avoid scientific notation
    return f"{qty:f}"


def validate_price(price: str, label: str = "Price") -> str:
    try:
        p = Decimal(str(price).strip())
    except InvalidOperation:
        raise ValueError(f"Invalid {label.lower()} '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValueError(f"{label} must be greater than 0 (got {p}).")
    return f"{p:f}"


# ── Composite validator ───────────────────────────────────────────────────────

def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
) -> dict:
    """
    Validate all order parameters and return a clean dict ready to pass
    to the Binance API.

    Raises ValueError with a human-readable message on any violation.
    """
    params: dict = {}

    params["symbol"] = validate_symbol(symbol)
    params["side"] = validate_side(side)
    params["type"] = validate_order_type(order_type)
    params["quantity"] = validate_quantity(quantity)

    ot = params["type"]

    # Price (limit price)
    if ot in PRICE_REQUIRED:
        if not price:
            raise ValueError(
                f"--price is required for {ot} orders."
            )
        params["price"] = validate_price(price, "Price")
    elif price:
        logger.warning(
            "Price supplied for a %s order — it will be ignored by the API.", ot
        )

    # Stop price
    if ot in STOP_PRICE_REQUIRED:
        if not stop_price:
            raise ValueError(
                f"--stop-price is required for {ot} orders."
            )
        params["stopPrice"] = validate_price(stop_price, "Stop price")
    elif stop_price:
        logger.warning(
            "Stop price supplied for a %s order — it will be ignored by the API.", ot
        )

    # Time-in-force (always GTC for types that need it)
    if ot in TIME_IN_FORCE_REQUIRED:
        params["timeInForce"] = "GTC"

    logger.debug("Validated params: %s", params)
    return params
