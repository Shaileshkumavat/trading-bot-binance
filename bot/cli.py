"""
CLI entry point for the Binance Futures Testnet trading bot.

Usage
-----
python -m bot.cli --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.01
python -m bot.cli --symbol BTCUSDT --side BUY  --type LIMIT  --quantity 0.01 --price 60000
python -m bot.cli --symbol ETHUSDT --side SELL --type MARKET --quantity 0.1
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from dotenv import load_dotenv

# ── Bootstrap: load .env and configure logging BEFORE any bot imports ─────────
load_dotenv()

from bot.logging_config import setup_logging, get_logger  # noqa: E402
setup_logging()
logger = get_logger(__name__)

from bot.validators import validate_all          # noqa: E402
from bot.orders import OrderService, OrderResult  # noqa: E402


# ── ANSI colour helpers ───────────────────────────────────────────────────────

def _c(code: str, text: str) -> str:
    """Apply an ANSI colour code when stdout is a real TTY."""
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text

def green(t: str)  -> str: return _c("32", t)
def red(t: str)    -> str: return _c("31", t)
def cyan(t: str)   -> str: return _c("36", t)
def yellow(t: str) -> str: return _c("33", t)
def bold(t: str)   -> str: return _c("1",  t)
def dim(t: str)    -> str: return _c("2",  t)


# ── Output helpers ────────────────────────────────────────────────────────────

_DIV = dim("─" * 54)


def print_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
) -> None:
    side_str = green(side) if side == "BUY" else red(side)
    print()
    print(bold("  📋  Order Request Summary"))
    print(_DIV)
    print(f"  Symbol     : {cyan(symbol)}")
    print(f"  Side       : {side_str}")
    print(f"  Type       : {yellow(order_type)}")
    print(f"  Quantity   : {quantity}")
    if price is not None:
        print(f"  Price      : {price:,.2f} USDT")
    else:
        print(f"  Price      : {dim('(market price)')}")
    print(_DIV)


def print_order_result(result: OrderResult) -> None:
    if result.success:
        print()
        print(bold("  ✅  Order Placed Successfully"))
        print(_DIV)
        print(f"  Order ID       : {cyan(str(result.order_id))}")
        print(f"  Symbol         : {result.symbol}")
        print(f"  Side           : {result.side}")
        print(f"  Type           : {result.order_type}")
        print(f"  Status         : {green(result.status or 'N/A')}")
        print(f"  Original Qty   : {result.orig_qty}")
        print(f"  Executed Qty   : {result.executed_qty}")

        avg = result.avg_price
        if avg and float(avg) > 0:
            print(f"  Avg Fill Price : {float(avg):,.2f} USDT")
        else:
            print(f"  Avg Fill Price : {dim('N/A (order not yet filled)')}")

        if result.client_order_id:
            print(f"  Client OID     : {dim(result.client_order_id)}")
        print(_DIV)
        print(f"\n  {green('SUCCESS')} — Order submitted to Binance Futures Testnet.\n")

    else:
        print()
        print(bold("  ❌  Order Failed"))
        print(_DIV)

        # Always show the human-readable reason from Binance (the `msg` field)
        print(f"  {red('Reason')}  : {result.error}")

        # If we have the Binance numeric code, show it too — helps with debugging
        if result.binance_code is not None:
            print(f"  {red('Code')}    : {result.binance_code}")
            print(
                f"  {dim('Hint')}    : "
                f"Search https://binance-docs.github.io/apidocs for error {result.binance_code}"
            )
        print(_DIV)
        print(f"\n  {red('FAILURE')} — The order could not be placed.\n")


# ── Argument parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m bot.cli",
        description="Binance Futures Testnet CLI Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python -m bot.cli --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.01
  python -m bot.cli --symbol BTCUSDT --side BUY  --type LIMIT  --quantity 0.01 --price 60000
  python -m bot.cli --symbol ETHUSDT --side SELL --type MARKET --quantity 0.1
        """,
    )
    parser.add_argument(
        "--symbol", required=True, metavar="SYMBOL",
        help="Trading pair (e.g. BTCUSDT). Case-insensitive.",
    )
    parser.add_argument(
        "--side", required=True, metavar="SIDE",
        help="BUY or SELL. Case-insensitive.",
    )
    parser.add_argument(
        "--type", dest="order_type", required=True, metavar="TYPE",
        help="MARKET or LIMIT. Case-insensitive.",
    )
    parser.add_argument(
        "--quantity", required=True, metavar="QTY",
        help="Order quantity, e.g. 0.01",
    )
    parser.add_argument(
        "--price", required=False, default=None, metavar="PRICE",
        help="Limit price in USDT. Required for LIMIT orders.",
    )
    return parser


# ── Main ──────────────────────────────────────────────────────────────────────

def main(argv: Optional[list] = None) -> int:
    """
    Parse → validate → place order → display result.
    Returns exit code 0 on success, 1 on any failure.
    """
    parser = build_parser()
    args   = parser.parse_args(argv)

    logger.info(
        "CLI START | symbol=%s side=%s type=%s qty=%s price=%s",
        args.symbol, args.side, args.order_type, args.quantity, args.price,
    )

    # ── 1. Validate + normalise all inputs ───────────────────────────────────
    try:
        clean = validate_all(
            symbol     = args.symbol,
            side       = args.side,
            order_type = args.order_type,
            quantity   = args.quantity,
            price      = args.price,
        )
    except ValueError as exc:
        print(f"\n  {red('Validation Error')}: {exc}\n")
        logger.error("VALIDATION FAILED | %s", exc)
        return 1

    # ── 2. Warn about ignored price on MARKET orders ─────────────────────────
    if clean["order_type"] == "MARKET" and args.price is not None:
        print(f"\n  {yellow('⚠  Warning')}: --price is not used for MARKET orders and will be ignored.\n")
        logger.warning("--price supplied for MARKET order | value=%s | ignoring", args.price)

    # ── 3. Print request summary ─────────────────────────────────────────────
    print_order_summary(
        symbol     = clean["symbol"],
        side       = clean["side"],
        order_type = clean["order_type"],
        quantity   = clean["quantity"],
        price      = clean["price"],
    )

    # ── 4. Initialise service (validates env keys) ────────────────────────────
    try:
        service = OrderService()
    except EnvironmentError as exc:
        print(f"\n  {red('Configuration Error')}: {exc}\n")
        logger.error("ENV CONFIG FAILED | %s", exc)
        return 1

    # ── 5. Place order ────────────────────────────────────────────────────────
    if clean["order_type"] == "MARKET":
        result = service.place_market_order(
            symbol   = clean["symbol"],
            side     = clean["side"],
            quantity = clean["quantity"],
        )
    else:  # LIMIT
        result = service.place_limit_order(
            symbol   = clean["symbol"],
            side     = clean["side"],
            quantity = clean["quantity"],
            price    = clean["price"],   # type: ignore[arg-type]
        )

    # ── 6. Print result ───────────────────────────────────────────────────────
    print_order_result(result)

    exit_code = 0 if result.success else 1
    logger.info("CLI END | success=%s", result.success)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())