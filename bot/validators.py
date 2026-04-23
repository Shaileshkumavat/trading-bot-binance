"""
Input validation for trading bot CLI arguments.

Normalisation rules applied to every field:
  - symbol    : strip whitespace, uppercase
  - side      : strip whitespace, uppercase
  - order_type: strip whitespace, uppercase
  - quantity  : parsed to float
  - price     : parsed to float (LIMIT only); None for MARKET

All validators raise ValueError with a descriptive, user-facing message.
"""

import math
import re
from typing import Optional

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_SIDES       = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

# Binance symbol: 2-20 uppercase letters or digits (e.g. BTCUSDT, ETHUSDT)
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,20}$")


# ── Individual validators ─────────────────────────────────────────────────────

def validate_symbol(symbol: str) -> str:
    """Normalise and validate a trading-pair symbol."""
    symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValueError(
            f"Invalid symbol '{symbol}'. "
            "Expected 2-20 uppercase letters/digits (e.g. BTCUSDT, ETHUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    """Normalise and validate the order side."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. "
            f"Accepted values: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Normalise and validate the order type."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Accepted values: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str) -> float:
    """Parse and validate the order quantity (must be a positive finite number)."""
    try:
        value = float(str(quantity).strip())
    except (ValueError, TypeError):
        raise ValueError(
            f"Invalid quantity '{quantity}'. Must be a positive number (e.g. 0.01)."
        )
    if not math.isfinite(value):
        raise ValueError(f"Quantity must be a finite number, got '{quantity}'.")
    if value <= 0:
        raise ValueError(
            f"Quantity must be greater than 0, got {value}. "
            "Please enter a positive amount."
        )
    return value


def validate_price(price: Optional[str], order_type: str) -> Optional[float]:
    """
    Validate the price argument against the order type.

    LIMIT  → price is required; must be a positive finite number.
    MARKET → price must be absent (None); if provided it will be ignored
             (caller is responsible for warning the user).

    Returns the parsed float for LIMIT, or None for MARKET.
    """
    if order_type == "LIMIT":
        if price is None:
            raise ValueError(
                "Price is required for LIMIT orders. "
                "Please add --price <value> (e.g. --price 60000)."
            )
        try:
            value = float(str(price).strip())
        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid price '{price}'. Must be a positive number (e.g. 60000)."
            )
        if not math.isfinite(value):
            raise ValueError(f"Price must be a finite number, got '{price}'.")
        if value <= 0:
            raise ValueError(
                f"Price must be greater than 0, got {value}. "
                "Please enter a positive price."
            )
        return value

    # MARKET order — price is irrelevant; return None and let CLI warn the user
    return None


# ── Composite validator (main entry point) ────────────────────────────────────

def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str],
) -> dict:
    """
    Run all validations in a single call.

    Returns a dict of clean, typed values:
        {symbol: str, side: str, order_type: str, quantity: float, price: float | None}

    Raises ValueError (with a human-readable message) on the first failure.
    """
    clean_symbol    = validate_symbol(symbol)
    clean_side      = validate_side(side)
    clean_type      = validate_order_type(order_type)
    clean_qty       = validate_quantity(quantity)
    clean_price     = validate_price(price, clean_type)

    return {
        "symbol":     clean_symbol,
        "side":       clean_side,
        "order_type": clean_type,
        "quantity":   clean_qty,
        "price":      clean_price,
    }