"""
Interactive CLI for the Binance Futures Testnet Trading Bot.

Run:
    python cli.py

The bot will guide you through a menu and prompt each field
individually — no flags required.
"""

import os
import sys

from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table

from bot.client import BinanceAPIError, BinanceClient, NetworkError
from bot.logging_config import setup_logging
from bot.orders import place_order
from bot.validators import (
    PRICE_REQUIRED,
    STOP_PRICE_REQUIRED,
    VALID_ORDER_TYPES,
    validate_order_params,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
)

load_dotenv()
console = Console()


# ── Credential helper ─────────────────────────────────────────────────────────

def _get_client() -> BinanceClient:
    api_key    = os.getenv("BINANCE_API_KEY",    "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        console.print(
            Panel(
                "[red]BINANCE_API_KEY or BINANCE_API_SECRET not set.\n"
                "Copy [bold].env.example → .env[/bold] and fill in your "
                "Testnet credentials.[/red]",
                title="[red]❌  Missing Credentials[/red]",
                border_style="red",
            )
        )
        sys.exit(1)

    return BinanceClient(api_key, api_secret)


# ── Generic validated prompt ──────────────────────────────────────────────────

def _ask(prompt_text: str, validator, hint: str = "") -> str:
    """
    Repeatedly prompt until the user enters a value that passes `validator`.
    Shows an inline validation error and re-prompts on failure.
    """
    hint_part = f" [dim]{hint}[/dim]" if hint else ""
    while True:
        raw = Prompt.ask(f"  {prompt_text}{hint_part}")
        try:
            return validator(raw)
        except ValueError as exc:
            console.print(f"  [red]  ⚠  {exc}[/red]")


# ── Table builders ────────────────────────────────────────────────────────────

def _summary_table(params: dict) -> Table:
    labels = {
        "symbol":      "Symbol",
        "side":        "Side",
        "type":        "Order Type",
        "quantity":    "Quantity",
        "price":       "Limit Price",
        "stopPrice":   "Stop Price",
        "timeInForce": "Time-in-Force",
        "reduceOnly":  "Reduce Only",
    }
    t = Table(
        title="Order Summary",
        box=box.ROUNDED,
        border_style="blue",
        show_header=False,
    )
    t.add_column("Field", style="cyan",  no_wrap=True)
    t.add_column("Value", style="white bold")
    for k, v in params.items():
        t.add_row(labels.get(k, k.capitalize()), str(v))
    return t


def _response_table(response: dict) -> Table:
    fields = [
        ("Order ID",      "orderId"),
        ("Client Ord ID", "clientOrderId"),
        ("Status",        "status"),
        ("Symbol",        "symbol"),
        ("Side",          "side"),
        ("Type",          "type"),
        ("Orig Qty",      "origQty"),
        ("Exec Qty",      "executedQty"),
        ("Avg Price",     "avgPrice"),
        ("Price",         "price"),
        ("Stop Price",    "stopPrice"),
        ("Time-in-Force", "timeInForce"),
        ("Update Time",   "updateTime"),
    ]
    t = Table(
        title="✅  Order Response",
        box=box.ROUNDED,
        border_style="green",
        show_header=False,
    )
    t.add_column("Field", style="cyan",        no_wrap=True)
    t.add_column("Value", style="bright_white")
    for label, key in fields:
        val = response.get(key)
        if val not in (None, "", "0", 0):
            t.add_row(label, str(val))
    return t


# ── Menu actions ──────────────────────────────────────────────────────────────

def _action_place_order() -> None:
    """Walk the user through placing an order, field by field."""
    console.print()
    console.print(Rule("[bold blue]Place New Order[/bold blue]", style="blue"))

    # ── Step 1 – Symbol ───────────────────────────────────────────────────────
    console.print()
    symbol = _ask("Symbol", validate_symbol, hint="e.g. BTCUSDT")

    # ── Step 2 – Side ─────────────────────────────────────────────────────────
    side = _ask("Side", validate_side, hint="BUY / SELL")

    # ── Step 3 – Order type ───────────────────────────────────────────────────
    type_hint = " / ".join(sorted(VALID_ORDER_TYPES))
    order_type = _ask("Order Type", validate_order_type, hint=type_hint)

    # ── Step 4 – Quantity ─────────────────────────────────────────────────────
    quantity = _ask("Quantity", validate_quantity, hint="in base asset units, e.g. 0.001")

    # ── Step 5 – Limit price (conditional) ───────────────────────────────────
    price = None
    if order_type in PRICE_REQUIRED:
        price = _ask(f"Limit Price", validate_price, hint=f"required for {order_type}")

    # ── Step 6 – Stop/trigger price (conditional) ─────────────────────────────
    stop_price = None
    if order_type in STOP_PRICE_REQUIRED:
        stop_price = _ask("Stop / Trigger Price", validate_price, hint=f"required for {order_type}")

    # ── Step 7 – Reduce-only flag ─────────────────────────────────────────────
    reduce_only = Confirm.ask("  Reduce Only?", default=False)

    # ── Build validated params ────────────────────────────────────────────────
    params = validate_order_params(symbol, side, order_type, quantity, price, stop_price)
    if reduce_only:
        params["reduceOnly"] = "true"

    # ── Step 8 – Show summary & confirm ──────────────────────────────────────
    console.print()
    console.print(_summary_table(params))
    console.print()

    if not Confirm.ask("  Confirm and place this order?", default=False):
        console.print("  [yellow]Order cancelled.[/yellow]\n")
        return

    # ── Step 9 – Place order ──────────────────────────────────────────────────
    client = _get_client()
    console.print("\n  [yellow]⏳  Placing order…[/yellow]\n")

    try:
        response = place_order(client, params)
    except BinanceAPIError as exc:
        console.print(
            Panel(
                f"[bold]Code [/bold]{exc.code}: {exc.message}",
                title="[red]❌  API Error[/red]",
                border_style="red",
            )
        )
        return
    except NetworkError as exc:
        console.print(
            Panel(str(exc), title="[red]❌  Network Error[/red]", border_style="red")
        )
        return
    except Exception as exc:
        console.print(
            Panel(str(exc), title="[red]❌  Unexpected Error[/red]", border_style="red")
        )
        return

    # ── Step 10 – Display response ────────────────────────────────────────────
    console.print(_response_table(response))
    console.print(
        Panel(
            f"[green]Order [bold]#{response.get('orderId')}[/bold] placed successfully![/green]",
            border_style="green",
            padding=(0, 2),
        )
    )


def _action_open_orders() -> None:
    """Fetch and display open orders, optionally filtered by symbol."""
    console.print()
    raw = Prompt.ask("  Filter by symbol? [dim](press Enter to list all)[/dim]", default="")
    symbol = raw.strip().upper() or None

    client = _get_client()
    console.print("  [yellow]⏳  Fetching open orders…[/yellow]")

    try:
        orders = client.get_open_orders(symbol)
    except (BinanceAPIError, NetworkError) as exc:
        console.print(Panel(str(exc), title="[red]Error[/red]", border_style="red"))
        return

    if not orders:
        console.print(
            Panel("[yellow]No open orders found.[/yellow]", border_style="yellow")
        )
        return

    t = Table(
        title=f"Open Orders{' — ' + symbol if symbol else ''}",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold cyan",
    )
    cols = ["orderId", "symbol", "side", "type", "origQty", "price", "status"]
    for col in cols:
        t.add_column(col, style="white")
    for o in orders:
        t.add_row(*[str(o.get(c, "—")) for c in cols])
    console.print()
    console.print(t)


def _action_ping() -> None:
    """Test connectivity to the Binance Futures Testnet."""
    client = _get_client()
    console.print("  [yellow]⏳  Pinging Binance Futures Testnet…[/yellow]")
    if client.ping():
        console.print(
            Panel(
                "[green]Testnet is reachable. Credentials loaded correctly.[/green]",
                title="[green]✅  Connected[/green]",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[red]Could not reach testnet.binancefuture.com.\n"
                "Check your network connection.[/red]",
                title="[red]❌  Unreachable[/red]",
                border_style="red",
            )
        )


# ── Menu definition ───────────────────────────────────────────────────────────

_MENU = [
    ("1", "Place Order",       _action_place_order),
    ("2", "View Open Orders",  _action_open_orders),
    ("3", "Test Connection",   _action_ping),
    ("4", "Exit",              None),
]


def _show_banner(log_file: str) -> None:
    console.print()
    console.print(
        Panel(
            "[bold green]Binance Futures Testnet Trading Bot[/bold green]\n"
            "[dim]USDT-M Futures  ·  Testnet Only[/dim]",
            border_style="green",
            padding=(1, 4),
        )
    )
    console.print(f"  [dim]Logs → {log_file}[/dim]")


def _show_menu() -> None:
    console.print()
    console.print("  [bold]Main Menu[/bold]")
    console.print()
    for key, label, action in _MENU:
        color = "red" if action is None else "cyan"
        console.print(f"  [{color}][{key}][/{color}]  {label}")
    console.print()


# ── Main loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    log_file = setup_logging()
    _show_banner(log_file)

    valid_keys = [key for key, *_ in _MENU]

    while True:
        _show_menu()

        choice = Prompt.ask(
            "  Select option",
            choices=valid_keys,
            show_choices=False,
        )

        if choice == "4":
            console.print("\n  [dim]Goodbye.[/dim]\n")
            break

        # Find and call the action
        for key, _, action in _MENU:
            if key == choice:
                try:
                    action()
                except KeyboardInterrupt:
                    console.print("\n  [yellow]Interrupted — returning to menu.[/yellow]")
                break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n  [dim]Interrupted. Goodbye.[/dim]\n")