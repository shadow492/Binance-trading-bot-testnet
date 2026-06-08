"""
Low-level Binance Futures Testnet client.

Handles:
  - HMAC-SHA256 request signing
  - Session / header management
  - HTTP requests with structured logging
  - Typed exceptions for API and network errors
"""

import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000  # milliseconds


# ── Custom exceptions ─────────────────────────────────────────────────────────

class BinanceAPIError(Exception):
    """Raised when the Binance API returns a non-200 status or error body."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class NetworkError(Exception):
    """Raised on connection/timeout failures."""


# ── Client ────────────────────────────────────────────────────────────────────

class BinanceClient:
    """Thin wrapper around the Binance USDT-M Futures Testnet REST API."""

    def __init__(self, api_key: str, api_secret: str) -> None:
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret.encode()

        self._session = requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": api_key})

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: dict) -> str:
        """Return HMAC-SHA256 hex signature of the URL-encoded params dict."""
        query = urlencode(params)
        return hmac.new(self._api_secret, query.encode(), hashlib.sha256).hexdigest()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        signed: bool = False,
    ) -> Any:
        """
        Execute an HTTP request against the Binance Futures Testnet.

        All parameters (including signature for signed endpoints) are sent
        as query-string parameters — this is fully supported by Binance and
        keeps the signing logic straightforward.
        """
        url = f"{BASE_URL}{endpoint}"
        params = dict(params or {})

        if signed:
            params["recvWindow"] = RECV_WINDOW
            params["timestamp"] = self._timestamp()
            params["signature"] = self._sign(params)

        logger.debug("→ %s %s | params=%s", method, endpoint, params)

        try:
            response = self._session.request(method, url, params=params, timeout=10)
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network – connection error: %s", exc)
            raise NetworkError(f"Cannot reach Binance Testnet: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            logger.error("Network – request timed out: %s", exc)
            raise NetworkError(f"Request timed out after 10s: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Network – unexpected requests error: %s", exc)
            raise NetworkError(str(exc)) from exc

        try:
            data = response.json()
        except ValueError:
            logger.error("Response is not valid JSON: %s", response.text[:200])
            raise BinanceAPIError(-1, f"Non-JSON response: {response.text[:200]}")

        if response.status_code != 200:
            code = data.get("code", -1)
            msg = data.get("msg", "Unknown error")
            logger.error("← API error %s: %s", code, msg)
            raise BinanceAPIError(code, msg)

        logger.debug("← %s %s | response=%s", response.status_code, endpoint, data)
        return data

    # ── Public API ────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        """Return True if the testnet is reachable."""
        try:
            self._request("GET", "/fapi/v1/ping")
            logger.info("Ping successful — testnet is reachable.")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Ping failed: %s", exc)
            return False

    def place_order(self, **kwargs: Any) -> dict:
        """
        POST /fapi/v1/order — place a new order.

        Accepts any keyword arguments and passes them directly to the API,
        so callers (orders.py) can forward validated params without mapping.
        """
        logger.info("Placing order with params: %s", kwargs)
        return self._request("POST", "/fapi/v1/order", params=kwargs, signed=True)

    def get_open_orders(self, symbol: str | None = None) -> list[dict]:
        """GET /fapi/v1/openOrders — list open orders (optionally filtered)."""
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        return self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """DELETE /fapi/v1/order — cancel an order by ID."""
        params = {"symbol": symbol.upper(), "orderId": order_id}
        logger.info("Cancelling order %s on %s", order_id, symbol)
        return self._request("DELETE", "/fapi/v1/order", params=params, signed=True)
