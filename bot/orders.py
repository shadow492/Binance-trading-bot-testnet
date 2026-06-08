"""
Order placement logic.

This module sits between the CLI layer and the API client.
It owns the business logic around placing an order and exposes
helpers for formatting the request summary and API response.
"""

import logging
from typing import Any

from bot.client import BinanceAPIError, BinanceClient, NetworkError

logger = logging.getLogger(__name__)


# ── Order placement ───────────────────────────────────────────────────────────

def place_order(client: BinanceClient, params: dict) -> dict:
    """
    Place an order using a validated params dict and return the API response.

    Logs the attempt and its outcome at the appropriate level.
    Re-raises BinanceAPIError / NetworkError so the CLI can handle them.
    """
    symbol = params.get("symbol", "?")
    side = params.get("side", "?")
    otype = params.get("type", "?")
    qty = params.get("quantity", "?")
    price_info = f" @ {params['price']}" if "price" in params else ""
    stop_info = f" (stop {params['stopPrice']})" if "stopPrice" in params else ""

    logger.info(
        "Attempting %s %s %s qty=%s%s%s",
        otype, side, symbol, qty, price_info, stop_info,
    )

    try:
        response = client.place_order(**params)
        logger.info(
            "Order success — orderId=%s status=%s execQty=%s avgPrice=%s",
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
            response.get("avgPrice"),
        )
        return response

    except BinanceAPIError:
        logger.error("Order failed (BinanceAPIError) for params: %s", params)
        raise
    except NetworkError:
        logger.error("Order failed (NetworkError) for params: %s", params)
        raise
    except Exception as exc:
        logger.exception("Unexpected error while placing order: %s", exc)
        raise


# ── Display helpers (fallback plain-text, used when rich is unavailable) ─────

def _row(label: str, value: Any, width: int = 48) -> str:
    val = str(value) if value not in (None, "", "N/A") else "N/A"
    return f"│  {label:<14}: {val}"


def format_order_summary(params: dict) -> str:
    """Return a plain-text box summarising the order request."""
    lines = ["┌── Order Request " + "─" * 31 + "┐"]
    for key, val in params.items():
        lines.append(_row(key.capitalize(), val))
    lines.append("└" + "─" * 49 + "┘")
    return "\n".join(lines)


def format_order_response(response: dict) -> str:
    """Return a plain-text box summarising the order API response."""
    fields = [
        ("Order ID",  response.get("orderId")),
        ("Status",    response.get("status")),
        ("Symbol",    response.get("symbol")),
        ("Side",      response.get("side")),
        ("Type",      response.get("type")),
        ("Orig Qty",  response.get("origQty")),
        ("Exec Qty",  response.get("executedQty")),
        ("Avg Price", response.get("avgPrice")),
        ("Client ID", response.get("clientOrderId")),
    ]
    lines = ["┌── Order Response " + "─" * 30 + "┐"]
    for label, val in fields:
        lines.append(_row(label, val))
    lines.append("└" + "─" * 49 + "┘")
    return "\n".join(lines)
