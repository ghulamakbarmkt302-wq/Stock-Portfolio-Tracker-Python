"""Stock Portfolio Performance Tracker (console).

Enter stock positions (ticker, shares, buy price). The program looks up
current prices in a CSV file, calculates value and gain/loss for each stock
and the whole portfolio, and appends each run to portfolio_summary.csv.

Price file format: a CSV with a 'Symbol' column and a price column named
'Price', 'Close' or 'Adj Close'. If the file has a 'Date' column, the last
row for each symbol is used, so keep rows in date order.
"""
import argparse
import csv
import os
from datetime import datetime

SUMMARY_FILE = "portfolio_summary.csv"
SUMMARY_FIELDS = [
    "run_time", "ticker", "shares", "buy_price", "current_price",
    "invested", "current_value", "gain_loss", "gain_loss_pct",
]
PRICE_COLUMNS = ("Price", "Close", "Adj Close")


# ---------- prices ----------

def load_prices(path):
    """Return {ticker: latest price} read from a price CSV file."""
    prices = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        if "Symbol" not in fields:
            raise ValueError("price file needs a 'Symbol' column")
        price_col = next((c for c in PRICE_COLUMNS if c in fields), None)
        if price_col is None:
            raise ValueError("price file needs one of these columns: " + ", ".join(PRICE_COLUMNS))
        for row in reader:
            symbol = (row.get("Symbol") or "").strip().upper()
            try:
                price = float(row[price_col])
            except (TypeError, ValueError):
                continue
            if symbol and price > 0:
                prices[symbol] = price
    return prices


# ---------- portfolio ----------

def add_position(portfolio, ticker, shares, buy_price):
    """Add shares of a stock. Buying the same stock again averages the buy price."""
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker cannot be empty")
    if shares <= 0:
        raise ValueError("shares must be more than 0")
    if buy_price <= 0:
        raise ValueError("buy price must be more than 0")
    if ticker in portfolio:
        old = portfolio[ticker]
        total = old["shares"] + shares
        avg = (old["shares"] * old["buy_price"] + shares * buy_price) / total
        portfolio[ticker] = {"shares": total, "buy_price": avg}
    else:
        portfolio[ticker] = {"shares": shares, "buy_price": buy_price}
    return portfolio[ticker]


def value_positions(portfolio, prices):
    """Return (rows, missing). Rows hold the numbers for each priced stock."""
    rows, missing = [], []
    for ticker in sorted(portfolio):
        pos = portfolio[ticker]
        price = prices.get(ticker)
        if price is None:
            missing.append(ticker)
            continue
        invested = pos["shares"] * pos["buy_price"]
        current = pos["shares"] * price
        gain = current - invested
        pct = (gain / invested * 100) if invested else 0.0
        rows.append({
            "ticker": ticker,
            "shares": pos["shares"],
            "buy_price": pos["buy_price"],
            "current_price": price,
            "invested": invested,
            "current_value": current,
            "gain_loss": gain,
            "gain_loss_pct": pct,
        })
    return rows, missing


def totals(rows):
    invested = sum(r["invested"] for r in rows)
    value = sum(r["current_value"] for r in rows)
    gain = value - invested
    pct = (gain / invested * 100) if invested else 0.0
    return {"invested": invested, "current_value": value, "gain_loss": gain, "gain_loss_pct": pct}


# ---------- output ----------

def format_table(rows):
    header = f"{'Ticker':<8}{'Shares':>10}{'Buy $':>12}{'Price $':>12}{'Invested $':>14}{'Value $':>14}{'Gain/Loss $':>14}{'%':>9}"
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append(
            f"{r['ticker']:<8}{r['shares']:>10.2f}{r['buy_price']:>12.2f}{r['current_price']:>12.2f}"
            f"{r['invested']:>14.2f}{r['current_value']:>14.2f}{r['gain_loss']:>+14.2f}{r['gain_loss_pct']:>+8.2f}%"
        )
    t = totals(rows)
    lines.append("-" * len(header))
    lines.append(
        f"{'TOTAL':<8}{'':>10}{'':>12}{'':>12}"
        f"{t['invested']:>14.2f}{t['current_value']:>14.2f}{t['gain_loss']:>+14.2f}{t['gain_loss_pct']:>+8.2f}%"
    )
    return "\n".join(lines)


def save_summary(path, rows, run_time=None):
    """Append this run's rows to the summary CSV. The header is written once."""
    run_time = run_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_file = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        if new_file:
            writer.writeheader()
        for r in rows:
            writer.writerow({
                "run_time": run_time,
                "ticker": r["ticker"],
                "shares": round(r["shares"], 4),
                "buy_price": round(r["buy_price"], 4),
                "current_price": round(r["current_price"], 4),
                "invested": round(r["invested"], 2),
                "current_value": round(r["current_value"], 2),
                "gain_loss": round(r["gain_loss"], 2),
                "gain_loss_pct": round(r["gain_loss_pct"], 2),
            })
    return len(rows)


# ---------- console menu ----------

def ask_number(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("Please enter a number.")


def menu_add(portfolio):
    ticker = input("Ticker symbol (e.g. AAPL): ").strip()
    shares = ask_number("Number of shares: ")
    buy_price = ask_number("Buy price per share: ")
    try:
        pos = add_position(portfolio, ticker, shares, buy_price)
    except ValueError as e:
        print("Not added:", e)
        return
    print(f"Saved {ticker.upper()}: {pos['shares']:.2f} shares at average ${pos['buy_price']:.2f}.")


def menu_view(portfolio, prices):
    if not portfolio:
        print("Your portfolio is empty. Add a stock first.")
        return
    rows, missing = value_positions(portfolio, prices)
    if rows:
        print()
        print(format_table(rows))
    if missing:
        print("\nNo price found for:", ", ".join(missing))


def menu_save(portfolio, prices, path):
    rows, missing = value_positions(portfolio, prices)
    if not rows:
        print("Nothing to save. Add stocks that have a price in your price file.")
        return
    count = save_summary(path, rows)
    print(f"Saved {count} rows to {path}.")
    if missing:
        print("Skipped (no price):", ", ".join(missing))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Stock Portfolio Performance Tracker")
    parser.add_argument("--prices", default="prices.csv", help="price CSV file (default: prices.csv)")
    parser.add_argument("--summary", default=SUMMARY_FILE, help="summary CSV file to append to")
    args = parser.parse_args(argv)

    prices = {}
    try:
        prices = load_prices(args.prices)
        print(f"Loaded {len(prices)} prices from {args.prices}.")
    except OSError:
        print(f"Warning: price file '{args.prices}' not found. Values will show as missing.")
    except ValueError as e:
        print(f"Warning: could not read '{args.prices}': {e}")

    portfolio = {}
    print("\n=== Stock Portfolio Performance Tracker ===")
    try:
        while True:
            print("\n1. Add stock\n2. View portfolio\n3. Save summary to CSV\n4. Quit")
            choice = input("Choose an option: ").strip()
            if choice == "1":
                menu_add(portfolio)
            elif choice == "2":
                menu_view(portfolio, prices)
            elif choice == "3":
                menu_save(portfolio, prices, args.summary)
            elif choice == "4":
                break
            else:
                print("Please choose 1, 2, 3 or 4.")
    except (KeyboardInterrupt, EOFError):
        print()
    print("Goodbye!")


if __name__ == "__main__":
    main()
