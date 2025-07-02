# Liquidation Preference Waterfall Calculator

A comprehensive Python library for modeling startup liquidation preferences, including stacked liquidation preferences, participation rights, caps, and conversion scenarios.

## Features

- **Stacked Liquidation Preferences**: Model multiple financing rounds with priority-based payouts
- **Participation Rights**: Support for participating vs non-participating preferred shares
- **Participation Caps**: Handle caps on participating preferences (e.g., 2x cap)
- **Conversion Analysis**: Automatically determine optimal conversion to common shares
- **Priority Groups**: Pro-rata distribution within same priority levels when multiple shareholders have different terms
- **CSV Integration**: Parse cap tables from CSV files with flexible formatting
- **Multiple Output Formats**: Generate summaries, detailed analyses, and conversion reports

## Installation

### As a Library

```bash
# Clone the repository
git clone <repository-url>
cd liquidation-preference-waterfall

# Install in development mode
pip install -e .
```

### As a Standalone Application

```bash
# Use the command-line interface directly
python cli.py captable.csv --exit-values 15M 25M 50M 100M
```

## Quick Start

### Library Usage

```python
from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType

# Create calculator
calc = WaterfallCalculator()

# Add share classes
common = ShareClass("Common", 1000000, 0, PreferenceType.COMMON)
series_a = ShareClass("Series A", 200000, 900000, PreferenceType.PARTICIPATING, 1.0, 2.0, 1)

calc.add_share_class(common)
calc.add_share_class(series_a)

# Calculate distribution for $5M exit
distribution = calc.calculate_distribution(5000000)
print(distribution)
```

### CSV Usage

```python
from liquidation_waterfall import parse_cap_table_csv, format_waterfall_analysis

# Load cap table from CSV
calculator = parse_cap_table_csv("captable.csv")

# Analyze multiple exit scenarios
exit_values = [15_000_000, 25_000_000, 50_000_000, 100_000_000]
print(format_waterfall_analysis(calculator, exit_values))
```

### Command Line Interface

```bash
# Basic analysis
python cli.py captable.csv

# Custom exit values with summary
python cli.py captable.csv --exit-values 15M 25M 50M 100M --summary

# Detailed step-by-step analysis
python cli.py captable.csv --detailed

# Show only conversion decisions
python cli.py captable.csv --conversion-only
```

## CSV Format

The library supports flexible CSV formats for cap tables:

```csv
Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Series E,7,1500000,9.00,1,FALSE,TRUE,0,None
Series D,6,870000,35.00,1,FALSE,TRUE,0,None
Series C,5,600000,31.00,1,FALSE,TRUE,0,None
Common,0,650000,1,0,TRUE,FALSE,0,None
```

**Required Fields:**
- `Share Class`: Name of the share class
- `Stack Order`: Priority order (higher = paid first)
- `# Shares`: Number of shares outstanding
- `Price`: Price per share at issuance
- `LPMultiple`: Liquidation preference multiple (e.g., 1.0 for 1x)
- `Participation`: TRUE for participating, FALSE for non-participating
- `Convertible`: TRUE if shares can convert to common
- `Participation Cap`: Cap multiple for participating shares (0 = no cap)
- `AD Type`: Anti-dilution type (None, FR, WA)

## Core Concepts

### Liquidation Preferences

When a startup is sold, proceeds are distributed according to liquidation preferences:

1. **Non-participating**: Investor gets either liquidation preference OR pro-rata share (whichever is higher)
2. **Participating**: Investor gets liquidation preference AND pro-rata share of remaining proceeds
3. **Participating with Cap**: Participating preference with maximum total payout limit

### Waterfall Algorithm

1. **Pay liquidation preferences** in priority order (highest stack order first)
2. **Handle insufficient funds** by pro-rating within priority groups
3. **Distribute remaining proceeds** to participating preferred and common shares
4. **Apply participation caps** iteratively to prevent over-allocation
5. **Evaluate conversion decisions** for non-participating preferred shares

### Priority Groups

When multiple shareholders exist at the same priority level with different terms:

```csv
B: Investor 1,2,1000000,10,1.25,TRUE,FALSE,0
B: Investor 2,2,500000,10,1.5,TRUE,FALSE,0
```

At insufficient funding, distribution is pro-rated based on liquidation preference amounts within the priority group.

## Advanced Features

### Conversion Analysis

The library automatically determines optimal conversion decisions:

```python
# Check conversion decisions for each exit value
conversion_analysis = format_conversion_analysis(calculator, [50_000_000])
print(conversion_analysis)
```

### Detailed Step-by-Step Analysis

```python
# Get detailed waterfall breakdown
detailed = format_detailed_analysis(calculator, 50_000_000)
print(detailed)
```

## Examples

### Example 1: Basic Waterfall

```python
from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType

calc = WaterfallCalculator()

# Add Series A: $1M invested, 1x non-participating
series_a = ShareClass("Series A", 100000, 1000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)

# Add Common: 900,000 shares
common = ShareClass("Common", 900000, 0, PreferenceType.COMMON)

calc.add_share_class(series_a)
calc.add_share_class(common)

# $5M exit
distribution = calc.calculate_distribution(5000000)
# Series A: $4,500,000 (converts to common for better return)
# Common: $500,000
```

### Example 2: Participating with Cap

```python
# Series B: $2M invested, 1x participating with 2x cap
series_b = ShareClass("Series B", 200000, 2000000, PreferenceType.PARTICIPATING, 1.0, 2.0, 2)

calc.add_share_class(series_b)

# At high exit values, Series B is capped at $4M total
distribution = calc.calculate_distribution(20000000)
```

## Documentation

See the `doc/` directory for detailed documentation:

- `PRIORITY_GROUPS.md`: How pro-rata distribution works within priority levels
- `PARTICIPATION_CAP_LOGIC.md`: Detailed explanation of participation caps
- `WATERFALL_LOGIC.md`: Step-by-step waterfall algorithm
- `LPW.md`: Additional implementation notes

## Testing

```bash
# Run tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_waterfall.py
```

## CLI Reference

```bash
# Show help
python cli.py --help

# Exit value formats supported:
python cli.py captable.csv --exit-values 15M 1.5B 500K 25000000

# Analysis options:
python cli.py captable.csv --summary           # Show cap table summary
python cli.py captable.csv --detailed          # Detailed step-by-step analysis
python cli.py captable.csv --conversion-only   # Show only conversion decisions
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.