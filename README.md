# Binance Futures Testnet Trading Bot

A clean, production-structured Python application that places orders on the **Binance USDT-M Futures Testnet** through a fully interactive CLI — the bot prompts you for each field one by one, validates your input inline, and shows a confirmation summary before placing any order.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py           # package metadata
│   ├── client.py             # Binance REST API client (HMAC signing, HTTP, exceptions)
│   ├── orders.py             # order placement logic and display helpers
│   ├── validators.py         # input validation — raises ValueError on bad input
│   └── logging_config.py    # structured logging → timestamped file + console
├── logs/                     # auto-created on first run; one log file per session
│   ├── trading_bot_market_order_sample.log
│   └── trading_bot_limit_order_sample.log
├── cli.py                    # interactive prompt-based entry point
├── .env.example              # copy to .env and fill in your Testnet credentials
├── requirements.txt
└── README.md
```

---

## Setup

### Step 1 — Register on Binance Futures Testnet

1. Go to **[https://testnet.binancefuture.com](https://testnet.binancefuture.com)**
2. Sign in with your GitHub account (no KYC or ID required).
3. Navigate to **API Management** and click **Generate Key**.
4. Copy both the **API Key** and **Secret Key** — the secret is only shown once.

> ⚠️ These are Testnet credentials. Do **not** use real Binance API keys here.

---

### Step 2 — Unzip and install dependencies

```bash
cd trading_bot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Dependencies installed:**

| Package | Purpose |
|---|---|
| `requests` | HTTP client for Binance REST API calls |
| `python-dotenv` | Loads credentials from `.env` file |
| `rich` | Coloured tables, panels, and prompts in the terminal |
| `typer` | CLI framework (used for `rich` prompt integration) |

---

### Step 3 — Configure your credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```dotenv
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

---

## Running the Bot

Start the bot with a single command:

```bash
python cli.py
```

You will see a welcome banner and a main menu:

```
  Main Menu

  [1]  Place Order
  [2]  View Open Orders
  [3]  Test Connection
  [4]  Exit
```

Select an option by typing its number and pressing Enter. The bot will guide you through each step interactively.

---

## How to Run — Session Examples

### Test your connection first

Select option `3` from the menu:

```
  Select option: 3
  ⏳ Pinging Binance Futures Testnet…
  ╭── ✅ Connected ───────────────────────────────────╮
  │  Testnet is reachable. Credentials loaded         │
  │  correctly.                                       │
  ╰───────────────────────────────────────────────────╯
```

---

### Example 1 — Place a MARKET order

Select `1` from the menu. The bot asks each field in sequence:

```
  Select option: 1

  ─────────────── Place New Order ─────────────────

  Symbol [e.g. BTCUSDT]: BTCUSDT
  Side [BUY / SELL]: BUY
  Order Type [LIMIT / MARKET / STOP / ...]: MARKET
  Quantity [in base asset units, e.g. 0.001]: 0.001
  Reduce Only? [y/N]: n

  ┌── Order Summary ──────────────────────┐
  │ Symbol      │ BTCUSDT                 │
  │ Side        │ BUY                     │
  │ Order Type  │ MARKET                  │
  │ Quantity    │ 0.001                   │
  └─────────────────────────────────────  ┘

  Confirm and place this order? [y/N]: y
  ⏳ Placing order…

  ┌── ✅ Order Response ──────────────────┐
  │ Order ID    │ 3281940123              │
  │ Status      │ FILLED                  │
  │ Symbol      │ BTCUSDT                 │
  │ Side        │ BUY                     │
  │ Type        │ MARKET                  │
  │ Orig Qty    │ 0.001                   │
  │ Exec Qty    │ 0.001                   │
  │ Avg Price   │ 101583.20               │
  └─────────────────────────────────────  ┘
```

> **Note:** For MARKET orders the bot does **not** ask for a price — the prompt is skipped automatically.

---

### Example 2 — Place a LIMIT order

```
  Select option: 1

  Symbol [e.g. BTCUSDT]: BTCUSDT
  Side [BUY / SELL]: SELL
  Order Type [LIMIT / MARKET / STOP / ...]: LIMIT
  Quantity [in base asset units, e.g. 0.001]: 0.001
  Limit Price [required for LIMIT]: 105000
  Reduce Only? [y/N]: n

  ┌── Order Summary ──────────────────────┐
  │ Symbol        │ BTCUSDT               │
  │ Side          │ SELL                  │
  │ Order Type    │ LIMIT                 │
  │ Quantity      │ 0.001                 │
  │ Limit Price   │ 105000                │
  │ Time-in-Force │ GTC                   │
  └─────────────────────────────────────  ┘

  Confirm and place this order? [y/N]: y
  ⏳ Placing order…

  ┌── ✅ Order Response ──────────────────┐
  │ Order ID    │ 3281940456              │
  │ Status      │ NEW                     │
  │ Symbol      │ BTCUSDT                 │
  │ Side        │ SELL                    │
  │ Type        │ LIMIT                   │
  │ Orig Qty    │ 0.001                   │
  │ Exec Qty    │ 0                       │
  │ Avg Price   │ 0                       │
  │ Price       │ 105000                  │
  └─────────────────────────────────────  ┘
```

> **Note:** A LIMIT order with status `NEW` means it is resting on the order book waiting to be filled.

---

### Example 3 — Place a STOP-LIMIT order *(bonus)*

A Stop-Limit order waits until price hits the **stop price**, then places a limit order at the **limit price**.

```
  Select option: 1

  Symbol [e.g. BTCUSDT]: BTCUSDT
  Side [BUY / SELL]: BUY
  Order Type [LIMIT / MARKET / STOP / ...]: STOP
  Quantity [in base asset units, e.g. 0.001]: 0.001
  Limit Price [required for STOP]: 50000
  Stop / Trigger Price [required for STOP]: 49500
  Reduce Only? [y/N]: n

  Confirm and place this order? [y/N]: y
```

---

### Example 4 — Place a STOP-MARKET order *(bonus)*

Triggers a market fill when the stop price is reached. No limit price needed.

```
  Select option: 1

  Symbol [e.g. BTCUSDT]: BTCUSDT
  Side [BUY / SELL]: SELL
  Order Type [LIMIT / MARKET / STOP / ...]: STOP_MARKET
  Quantity [in base asset units, e.g. 0.001]: 0.001
  Stop / Trigger Price [required for STOP_MARKET]: 48000
  Reduce Only? [y/N]: n

  Confirm and place this order? [y/N]: y
```

---

### Example 5 — View open orders

Select `2` from the menu. You can filter by symbol or press Enter to list all:

```
  Select option: 2

  Filter by symbol? (press Enter to list all): BTCUSDT
  ⏳ Fetching open orders…

  ╭── Open Orders — BTCUSDT ───────────────────────────────────────────╮
  │ orderId    │ symbol  │ side │ type  │ origQty │ price  │ status │
  │ 3281940456 │ BTCUSDT │ SELL │ LIMIT │ 0.001   │ 105000 │ NEW    │
  ╰────────────────────────────────────────────────────────────────────╯
```

---

## Prompt Fields Reference

| Prompt | Always shown | Shown only when |
|---|---|---|
| Symbol | ✅ | — |
| Side | ✅ | — |
| Order Type | ✅ | — |
| Quantity | ✅ | — |
| Limit Price | ❌ | Order type is `LIMIT`, `STOP`, or `TAKE_PROFIT` |
| Stop / Trigger Price | ❌ | Order type is `STOP`, `STOP_MARKET`, `TAKE_PROFIT`, or `TAKE_PROFIT_MARKET` |
| Reduce Only | ✅ | — |

---

## Supported Order Types

| Type | Description |
|---|---|
| `MARKET` | Fills immediately at the best available market price |
| `LIMIT` | Places an order at a specific price or better (requires limit price) |
| `STOP` | Stop-Limit: triggers at stop price, then executes a limit order at limit price |
| `STOP_MARKET` | Stop-Market: triggers at stop price, then fills at market price |
| `TAKE_PROFIT` | Take-Profit-Limit: triggers at stop price, executes limit order |
| `TAKE_PROFIT_MARKET` | Take-Profit-Market: triggers at stop price, fills at market |

---

## Input Validation

Every field is validated before any network call is made. If you enter an invalid value the bot shows an inline error and re-prompts the **same field** — you never have to restart from the beginning:

```
  Symbol [e.g. BTCUSDT]: !!!BAD
    ⚠  Invalid symbol '!!!BAD'. Use alphanumeric characters only (e.g. BTCUSDT).
  Symbol [e.g. BTCUSDT]: BTCUSDT   ← re-prompted, continues normally

  Side [BUY / SELL]: LONG
    ⚠  Invalid side 'LONG'. Must be one of: BUY, SELL.
  Side [BUY / SELL]: BUY

  Quantity [in base asset units, e.g. 0.001]: -5
    ⚠  Quantity must be greater than 0 (got -5).
  Quantity [in base asset units, e.g. 0.001]: 0.001
```

---

## Logging

Each run creates a new timestamped log file under `logs/`:

```
logs/trading_bot_YYYYMMDD_HHMMSS.log
```

The path is printed in the banner at startup. Sample log files for a MARKET order and a LIMIT order are included in the `logs/` folder.

**What gets logged:**

| Level | Where | Content |
|---|---|---|
| `DEBUG` | File only | Raw API request params, full JSON responses |
| `INFO` | File only | Order attempts, success details, ping results |
| `WARNING` | File + console | Unused parameter warnings (e.g. price given for MARKET) |
| `ERROR` | File + console | API errors, network failures, unexpected exceptions |

**Sample log entry (MARKET order):**
```
2024-12-14 10:23:54 | INFO     | bot.orders  | Attempting MARKET BUY BTCUSDT qty=0.001
2024-12-14 10:23:54 | DEBUG    | bot.client  | → POST /fapi/v1/order | params={...}
2024-12-14 10:23:54 | DEBUG    | bot.client  | ← 200 /fapi/v1/order  | response={...}
2024-12-14 10:23:54 | INFO     | bot.orders  | Order success — orderId=3281940123 status=FILLED execQty=0.001 avgPrice=101583.20
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing `.env` credentials | Error panel shown, process exits cleanly |
| Invalid input (bad symbol, wrong side, etc.) | Inline `⚠` message, same field re-prompted immediately |
| LIMIT order without a price | Validation error before any network call |
| Binance API error (e.g. invalid symbol, insufficient balance) | Error code + message shown in red panel; full detail in log |
| Network / timeout failure | User-friendly message shown; full traceback in log |
| User declines confirmation | Order is not placed; returns to menu |
| `Ctrl+C` during prompts | Cancels current action, returns to menu |

---

## Assumptions

- **One-way position mode** is assumed, which is the default on new Testnet accounts. Hedge Mode (where `positionSide` must be `LONG` or `SHORT`) is not supported without code changes.
- **Quantity precision** is validated for type and sign but not against each symbol's exchange-defined lot size. The Binance API will return a clear error (code `-1111`) if the precision is too granular for the chosen symbol.
- `timeInForce` is always set to **GTC** (Good Till Cancel) for order types that require it (`LIMIT`, `STOP`, `TAKE_PROFIT`). This is the most widely applicable default.
- The bot targets **USDT-M Futures Testnet** only (`https://testnet.binancefuture.com`). It is not configured for COIN-M Futures or the Spot exchange.
- All prices and quantities are handled as strings internally to preserve decimal precision and avoid float rounding errors.
- A `recvWindow` of 5000 ms is used for signed requests. If you experience frequent timestamp errors, your system clock may need syncing.

---

## Architecture Overview

```
python cli.py
     │
     ▼
 cli.py  (interactive prompts, menu loop, rich display)
     │
     ├── bot/validators.py  ──  validates input, raises ValueError
     │         │ clean params dict
     │         ▼
     ├── bot/orders.py  ──  place_order(), logs attempt + outcome
     │         │
     │         ▼
     ├── bot/client.py  ──  HMAC signing, HTTP via requests,
     │         │             raises BinanceAPIError / NetworkError
     │         ▼
     │   Binance Futures Testnet API
     │   https://testnet.binancefuture.com
     │
     └── bot/logging_config.py  →  logs/trading_bot_YYYYMMDD_HHMMSS.log
```

**Layer responsibilities:**

| File | Responsibility |
|---|---|
| `cli.py` | All user interaction — prompts, menus, display. Zero business logic. |
| `validators.py` | Pure input validation. Never touches the network. Only raises `ValueError`. |
| `orders.py` | Orchestrates the order call. Logs outcomes. Re-raises exceptions for CLI to display. |
| `client.py` | Pure HTTP layer. Handles signing, headers, request/response. Raises typed exceptions only. |
| `logging_config.py` | Configures structured logging to file (DEBUG) and console (WARNING+). |

---

*Built for the Primetrade.ai Python Developer Intern application task.*