"""
Order placement business logic.

Wraps BinanceClient with order-specific operations and returns a typed
OrderResult dataclass.  Every success *and* failure path gets a clear,
structured log entry so logs are equally useful for both outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from bot.client import BinanceClient, BinanceAPIError, BinanceNetworkError
from bot.logging_config import get_logger

logger = get_logger(__name__)

_ORDER_ENDPOINT = "/fapi/v1/order"


# ── Result dataclass ──────────────────────────────────────────────────────────


@dataclass
class OrderResult:
    success: bool
    order_id: Optional[int]    = None
    symbol: Optional[str]      = None
    side: Optional[str]        = None
    order_type: Optional[str]  = None
    status: Optional[str]      = None
    executed_qty: Optional[str] = None
    avg_price: Optional[str]   = None
    price: Optional[str]       = None
    orig_qty: Optional[str]    = None
    client_order_id: Optional[str] = None
    raw: Dict[str, Any]        = field(default_factory=dict)
    # Failure path
    error: Optional[str]       = None
    binance_code: Optional[int] = None   # Binance numeric error code, if available

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "OrderResult":
        return cls(
            success         = True,
            order_id        = data.get("orderId"),
            symbol          = data.get("symbol"),
            side            = data.get("side"),
            order_type      = data.get("type"),
            status          = data.get("status"),
            executed_qty    = data.get("executedQty"),
            avg_price       = data.get("avgPrice"),
            price           = data.get("price"),
            orig_qty        = data.get("origQty"),
            client_order_id = data.get("clientOrderId"),
            raw             = data,
        )

    @classmethod
    def from_error(
        cls,
        error: str,
        binance_code: Optional[int] = None,
    ) -> "OrderResult":
        return cls(success=False, error=error, binance_code=binance_code)


# ── Order service ─────────────────────────────────────────────────────────────


class OrderService:
    """
    High-level order operations built on top of BinanceClient.

    Parameters
    ----------
    client : BinanceClient | None
        Pass an instance for testing; otherwise one is created automatically.
    """

    def __init__(self, client: Optional[BinanceClient] = None) -> None:
        self._client = client or BinanceClient()

    # ── Public API ────────────────────────────────────────────────────────────

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
    ) -> OrderResult:
        """Place a MARKET order and return an OrderResult."""
        params = self._build_base_params(symbol, side, "MARKET", quantity)
        logger.info(
            "ORDER    | MARKET | symbol=%s side=%s qty=%s",
            symbol, side, quantity,
        )
        return self._execute(params)

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> OrderResult:
        """Place a GTC LIMIT order and return an OrderResult."""
        params = self._build_base_params(symbol, side, "LIMIT", quantity)
        params["price"]       = self._format_price(price)
        params["timeInForce"] = "GTC"
        logger.info(
            "ORDER    | LIMIT  | symbol=%s side=%s qty=%s price=%s",
            symbol, side, quantity, price,
        )
        return self._execute(params)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _execute(self, params: Dict[str, Any]) -> OrderResult:
        order_type = params.get("type", "?")
        symbol     = params.get("symbol", "?")

        try:
            response = self._client.post(_ORDER_ENDPOINT, params=params, signed=True)

        except BinanceAPIError as exc:
            # ── Structured failure log ────────────────────────────────────────
            logger.error(
                "ORDER FAILED | type=%s symbol=%s | binance_code=%s | reason=%s",
                order_type, symbol, exc.code, exc.message,
            )
            return OrderResult.from_error(
                error        = exc.message,
                binance_code = exc.code,
            )

        except BinanceNetworkError as exc:
            logger.error(
                "ORDER FAILED | type=%s symbol=%s | network_error=%s",
                order_type, symbol, exc,
            )
            return OrderResult.from_error(error=str(exc))

        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "ORDER FAILED | type=%s symbol=%s | unexpected=%s",
                order_type, symbol, exc,
            )
            return OrderResult.from_error(error=f"Unexpected error: {exc}")

        result = OrderResult.from_api_response(response)

        # ── Structured success log (readable at a glance) ─────────────────────
        logger.info(
            "ORDER OK | id=%s status=%s executed=%s avg_price=%s",
            result.order_id,
            result.status,
            result.executed_qty,
            result.avg_price or "N/A",
        )
        logger.debug("RAW      | %s", response)

        return result

    # ── Parameter helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _build_base_params(
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
    ) -> Dict[str, Any]:
        return {
            "symbol":   symbol,
            "side":     side,
            "type":     order_type,
            # Strip trailing zeros so Binance doesn't reject e.g. "0.01000000"
            "quantity": f"{quantity:.8f}".rstrip("0").rstrip("."),
        }

    @staticmethod
    def _format_price(price: float) -> str:
        """Format price as a Binance-friendly string (2 decimal places)."""
        return f"{price:.2f}"