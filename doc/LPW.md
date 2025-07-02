# Liquidation Preference Waterfall Calculator

This script performs a liquidation preference calculation and provides both point calculations and iterative analysis of liquidation scenarios.

## Overview

The **liq-pref** tool calculates how proceeds from a company sale are distributed among different classes of shareholders based on their liquidation preferences, participation rights, and conversion options.

## CSV File Format

The tool requires CSV files with the following format for `lpw.py`:

### Required Columns (in order):

1. **Seniority** (int): Liquidation order where 1 = highest priority
2. **Round_Amount** (float): Total value invested for that share class
3. **Investor_Amount** (float): Specific investor's investment share in that round
4. **Round_Shares** (float): Total shares assigned to the category
5. **Investor_Shares** (float): Specific investor's shares in that round
6. **Preferred** (int): 1 = Preferred stock, 0 = Common stock
7. **Participating** (int): 1 = Participating preferred, 0 = Non-participating
8. **CAP** (float): Maximum participation cap (e.g., 3.0 for 3x), 0 if no cap
9. **MP** (float): Liquidation preference multiplier (typically 1.0)
10. **Common_Pool** (int): 1 = participates in final common distribution, 0 = excluded

### File Requirements:

- **Format**: UTF-8 encoded CSV
- **Delimiter**: Semicolon (;)
- **Numbers**: Use format like 1,000,000.00 or 1000000.00
- **No formulas**: Clean Excel formulas and empty cells before export

### Example CSV Structure:

```
Seniority;Round_Amount;Investor_Amount;Round_Shares;Investor_Shares;Preferred;Participating;CAP;MP;Common_Pool
1;15000000.00;5000000.00;1593863;531287;1;0;0;1.0;1
2;31800000.00;10600000.00;870334;290111;1;0;0;1.0;1
3;18600000.00;6200000.00;599451;199817;1;0;0;1.0;1
9;650000.00;0.00;650238;0;0;1;0;1.0;1
```

### Field Descriptions:

- **Seniority**: Determines payout order (1 gets paid first)
- **Round_Amount**: Total investment in this funding round
- **Investor_Amount**: How much the specific investor put into this round
- **Round_Shares**: Total shares issued in this round
- **Investor_Shares**: Shares owned by the specific investor from this round
- **Preferred**: Whether this is preferred (1) or common (0) stock
- **Participating**: Whether preferred shares participate in upside (1) or not (0)
- **CAP**: Maximum return multiple (0 = uncapped)
- **MP**: Liquidation preference multiple (usually 1x)
- **Common_Pool**: Whether these shares participate in final common distribution

### Common Pool Note:

The Common_Pool field handles special cases where preferred shares, after receiving their liquidation preference, also participate in the final distribution with common shares. This is used for complex participation structures with caps.

