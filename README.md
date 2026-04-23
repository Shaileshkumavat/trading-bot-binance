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
| Logs | `logs/app.log` with execution metrics |

---

## 🏗️ Architecture

The application follows a **layered architecture** with clear separation of concerns:

- **CLI Layer (`cli.py`)**  
  Handles argument parsing, user input processing, and command execution flow.

- **Validation Layer (`validators.py`)**  
  Validates and normalizes user inputs before they reach the business logic, ensuring data integrity.

- **Business Logic Layer (`orders.py`)**  
  Encapsulates order creation, response parsing, and result formatting using structured data classes.

- **API Client Layer (`client.py`)**  
  Manages HMAC-SHA256 signed HTTP requests to Binance API with automatic timestamp generation and signature calculation.

- **Logging Layer (`logging_config.py`)**  
  Provides structured logging for debugging, monitoring, and performance analysis across all layers.

**Design Principle:** Each layer has a single responsibility and can be tested or modified independently.

---

## 🔐 Security

Security is a core consideration in this implementation:

- **Environment-based Secrets**  
  API keys are stored securely using environment variables (`.env`) and never hardcoded in source files.

- **Signature-based Authentication**  
  All API requests use HMAC-SHA256 signing to ensure request integrity and prevent tampering.

- **Log Sanitization**  
  Sensitive data (e.g., API secrets, request signatures) are masked or excluded from logs to prevent accidental exposure.

- **Version Control Protection**  
  `.env` is explicitly excluded via `.gitignore` to prevent accidental commits of credentials.

- **Configuration Template**  
  An example `.env.example` file is included for safe reference without exposing real credentials.

---

## ⚡ Performance

The bot is designed with performance monitoring built-in:

- **Request Latency Tracking**  
  API request execution time is logged for every request, enabling performance analysis and bottleneck identification.

- **Efficient HTTP Client**  
  Uses `requests` library with connection reuse and minimal overhead for low-latency order execution.

- **Lightweight Design**  
  No heavy dependencies or unnecessary abstractions — optimized for fast startup and execution.

**Example log output:**
```
2024-01-15 10:30:45 | INFO | bot.client | RESPONSE | POST /fapi/v1/order | HTTP 200 | elapsed=0.843s
```

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

> ⚠️ **Never commit your `.env` file.** Add it to `.gitignore`.  
> 💡 A template `.env.example` is included for reference.

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
├── .env.example             # Template for environment variables
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

## 🧪 Testing Coverage

This implementation has been validated against the following scenarios:

- ✅ **MARKET BUY order** — Successful execution with quantity validation
- ✅ **LIMIT BUY order** — Order placement with price specification
- ✅ **Input validation** — Invalid side, quantity, missing price, malformed symbols
- ✅ **Error handling** — Binance API failures with proper error code propagation
- ✅ **Logging verification** — Request/response logging with execution time tracking
- ✅ **Edge cases** — MARKET order with `--price` supplied (warning shown, price ignored)

**Testing approach:** Manual integration testing against Binance Futures Testnet API with log verification.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `requests` | Latest | HTTP client for API communication |
| `python-dotenv` | Latest | Environment variable management from `.env` |

Install all dependencies:

```bash
pip install -r requirements.txt
```

**No external trading libraries** — Direct API integration for full control and transparency.

---

## 🚀 Future Enhancements

Potential improvements for production readiness and extended functionality:

### High Priority
- **Additional Order Types**  
  Support for Stop-Loss, Take-Profit, and OCO (One-Cancels-Other) orders

- **Retry Logic**  
  Implement exponential backoff for transient network failures

- **Unit Testing**  
  Add comprehensive test coverage for validation, client, and order logic layers

### Medium Priority
- **Interactive CLI Mode**  
  Add REPL-style interface for rapid order placement without re-running commands

- **Position Management**  
  View open positions, PnL tracking, and automatic position closing

- **Rate Limiting**  
  Built-in rate limit handling to comply with Binance API restrictions

### Nice to Have
- **Configuration Profiles**  
  Support multiple API key profiles for different accounts

- **Order History**  
  Query and display recent order history with filtering options

- **WebSocket Integration**  
  Real-time price feeds and order status updates

---

## 📚 Documentation

- [Binance Futures API Documentation](https://binance-docs.github.io/apidocs/futures/en/)
- [Binance Futures Testnet](https://testnet.binancefuture.com)
- [HMAC-SHA256 Authentication](https://en.wikipedia.org/wiki/HMAC)

---

## 📄 License

This project is for educational purposes. Use at your own risk.

---

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows existing architecture patterns
- New features include appropriate logging
- Input validation is maintained for all user inputs
- Security best practices are preserved

---

**Built with Python 🐍 | Designed for clarity and maintainability**
