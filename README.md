# Stock Portfolio Performance Tracker (Python)

A console program to track a stock portfolio. Enter your stocks, see the current value and gain or loss for each stock and for the whole portfolio, and save each run to a CSV file.

## Features

- Add stocks by ticker, number of shares and buy price
- Buying the same stock again averages the buy price
- Shows invested amount, current value, gain/loss in $ and %, with totals
- Reads current prices from a CSV file you provide
- Appends each saved run to `portfolio_summary.csv`, with a timestamp
- Uses only the standard library (no installs needed)

## Requirements

- Python 3.8 or newer

## Price file

The program needs a CSV file of prices, `prices.csv` by default:

- It must have a `Symbol` column, plus one price column: `Price`, `Close` or `Adj Close`.
- If it has a `Date` column too, the last row for each symbol is used, so keep rows in date order.

`sample_prices.csv` is included to try the program. Its prices are sample values, not live market data.

To use the S&P 500 dataset, download it as a CSV, save it in this folder as `prices.csv` (or give its path with `--prices`).

## How to run

```bash
python3 portfolio.py
```

Use a different price file or summary file:

```bash
python3 portfolio.py --prices sample_prices.csv --summary my_summary.csv
```

On Windows, use `python` instead of `python3`.

## Menu

1. **Add stock**: enter the ticker, shares and buy price.
2. **View portfolio**: show the table with current values and gain/loss.
3. **Save summary to CSV**: append this run's rows to `portfolio_summary.csv`.
4. **Quit**

## Summary CSV columns

`run_time, ticker, shares, buy_price, current_price, invested, current_value, gain_loss, gain_loss_pct`

## Formulas

- Invested = shares × buy price
- Current value = shares × current price
- Gain/loss = current value − invested
- Gain/loss % = gain/loss ÷ invested × 100

## Tests

The tests use fixed prices, so results are the same every time:

```bash
python3 test_portfolio.py
```

## Files

| File | Purpose |
|---|---|
| `portfolio.py` | The program |
| `test_portfolio.py` | Unit tests |
| `sample_prices.csv` | Sample prices to try the program |
| `README.md` | This file |

## Notes

- Positions are kept only while the program runs. Save to CSV before you quit to keep a record.
- Current prices come from your price file, so they are only as current as that file.
