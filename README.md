# Binance Futures Testnet Trading Bot

CLI-based Python bot to place **MARKET** and **LIMIT** orders on the
Binance USDT-M Futures Testnet.

---

## 📌 Overview

| Feature | Detail |
|---|---|
| Exchange | Binance Futures Testnet (USDT-M) |
| Order types | MARKET, LIMIT |
| Sides | BUY, SELL |
| Auth | HMAC-SHA256 signed requests |
| HTTP client | `requests` (no python-binance) |
| Config | `.env` via `python-dotenv` |
| Logs | `logs/app.log` |

---

## ⚙️ Setup

```bash
git clone <your-repo>
cd trading_bot
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### Create `.env`

Get your API keys from [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
→ Account → API Management → Create Key

```
API_KEY=your_testnet_api_key
API_SECRET=your_testnet_api_secret
BASE_URL=https://testnet.binancefuture.com
```

> ⚠️ Never commit your `.env` file. Add it to `.gitignore`.

---

## ▶️ Usage

Run from the **project root** (the `trading_bot/` folder):

### MARKET Order

```bash
python -m bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### LIMIT Order

```bash
python -m bot.cli --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 10000
```

### SELL Order

```bash
python -m bot.cli --symbol ETHUSDT --side SELL --type MARKET --quantity 0.1
```

> Inputs are **case-insensitive** — `buy`, `BUY`, and `Buy` all work.

---

## 🧾 Output

```
  📋  Order Request Summary
──────────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : LIMIT
  Quantity   : 0.01
  Price      : 10,000.00 USDT
──────────────────────────────────────────────────────

  ✅  Order Placed Successfully
──────────────────────────────────────────────────────
  Order ID       : 3279560035
  Symbol         : BTCUSDT
  Side           : BUY
  Type           : LIMIT
  Status         : NEW
  Original Qty   : 0.01
  Executed Qty   : 0
  Avg Fill Price : N/A (order not yet filled)
  Client OID     : web_abc123
──────────────────────────────────────────────────────

  SUCCESS — Order submitted to Binance Futures Testnet.
```

On failure, the exact Binance error reason and code are shown:

```
  ❌  Order Failed
──────────────────────────────────────────────────────
  Reason  : Order's notional must be no smaller than 100 USDT ...
  Code    : -4164
  Hint    : Search https://binance-docs.github.io/apidocs for error -4164
──────────────────────────────────────────────────────

  FAILURE — The order could not be placed.
```

---

## 📂 Logs

All API requests, responses, and errors are saved to:

```
logs/app.log
```

The file is created automatically on first run.

Sample log lines:

```
2024-01-15 10:30:44 | INFO     | bot.orders | ORDER    | LIMIT  | symbol=BTCUSDT side=BUY qty=0.01 price=10000
2024-01-15 10:30:44 | DEBUG    | bot.client | REQUEST  | POST /fapi/v1/order | params={...}
2024-01-15 10:30:45 | INFO     | bot.client | RESPONSE | POST /fapi/v1/order | HTTP 200 | elapsed=0.843s
2024-01-15 10:30:45 | INFO     | bot.orders | ORDER OK | id=3279560035 status=NEW executed=0 avg_price=N/A
```

On failure:

```
2024-01-15 10:31:02 | ERROR    | bot.client | API_ERR  | HTTP 400 | code=-4164 | reason=Order's notional ...
2024-01-15 10:31:02 | ERROR    | bot.orders | ORDER FAILED | type=LIMIT symbol=BTCUSDT | binance_code=-4164 | reason=...
```

---

## 📂 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package metadata
│   ├── client.py            # Signed HTTP client with execution timing
│   ├── orders.py            # Order placement + OrderResult dataclass
│   ├── validators.py        # Input normalisation and validation
│   ├── logging_config.py    # Logging setup (file + console)
│   └── cli.py               # CLI entry point (argparse)
├── logs/
│   └── app.log              # Auto-created on first run
├── .env                     # API credentials (never commit)
├── requirements.txt
└── README.md
```

---

## ✅ Validation Rules

| Field | Rule |
|---|---|
| `--symbol` | 2–20 letters/digits, e.g. `BTCUSDT`. Normalised to uppercase. |
| `--side` | `BUY` or `SELL`. Case-insensitive. |
| `--type` | `MARKET` or `LIMIT`. Case-insensitive. |
| `--quantity` | Positive finite number. |
| `--price` | Required for `LIMIT`; must be a positive finite number. Ignored (with warning) for `MARKET`. |

---

## ⚠️ Assumptions

- Uses Binance **Futures Testnet** — not real money.
- MARKET orders on testnet may show `executedQty=0` and `avgPrice=0` immediately
  after placement; this is normal testnet behaviour.
- LIMIT orders sit as `NEW` until the price is reached.

---

## 🧪 Tested

- ✅ MARKET BUY order
- ✅ LIMIT BUY order
- ✅ Validation errors (missing price, bad symbol, negative quantity)
- ✅ MARKET order with `--price` supplied → warning shown, price ignored

---

## 📦 Requirements

| Package | Purpose |
|---|---|
| `requests` | HTTP client |
| `python-dotenv` | Load `.env` into `os.environ` |

```
pip install -r requirements.txt
```