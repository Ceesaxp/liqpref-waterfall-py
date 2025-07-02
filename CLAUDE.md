# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**liq-pref** is a liquidation preference calculator that models how proceeds from a company sale are distributed among different classes of shareholders based on their liquidation preferences, participation rights, and conversion options.

## Commands

### Running the Calculator
```bash
python lp.py --cap_table captable.csv --prev_price <price> --new_price <price> --sale_prices <price1> <price2> ... --output <output_file> --format <csv|excel|html|md|txt>
```

Example:
```bash
python lp.py --cap_table captable.csv --prev_price 36.62 --new_price 9.41 --sale_prices 15000000 25000000 50000000 100000000 --output results.txt --format txt
```

### Missing Dependencies
The project uses pandas and numpy but they're not in pyproject.toml. Install with:
```bash
pip install pandas numpy openpyxl
```

## Code Architecture

The main logic is in `lp.py` with the following key components:

1. **Data Loading**: `load_cap_table()` reads CSV with columns:
   - Series, Order, Shares, Price, LiqPrefMultiple, Participating, Convertible

2. **Anti-dilution**: `apply_anti_dilution()` adjusts share counts when new financing price is lower than previous

3. **Liquidation Waterfall**: `run_liquidation_waterfall()` implements the distribution algorithm:
   - First: Pay liquidation preferences by order
   - Second: Distribute to participating preferred
   - Third: Handle conversion decisions
   - Fourth: Distribute remaining to common/converted shares

4. **Export**: Supports CSV, Excel, HTML, Markdown, and text output formats

## Development Notes

- Python 3.13 project
- No test suite or linting configuration currently exists
- All files are currently untracked in git
- The capitalization table CSV drives the share class definitions and liquidation order