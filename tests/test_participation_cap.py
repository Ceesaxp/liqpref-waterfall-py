#!/usr/bin/env python3
"""Test participation cap logic"""

from liquidation_waterfall import parse_cap_table_csv

# Parse the updated cap table
calc = parse_cap_table_csv('captable-3.csv')

# Check Series E
series_e = next(sc for sc in calc.share_classes if sc.name == "Series E")
print("Series E details:")
print(f"  Preference Type: {series_e.preference_type}")
print(f"  Invested: ${series_e.invested/1000000:.2f}M")
print(f"  Participation Cap: {series_e.participation_cap if series_e.participation_cap is not None else 'None'}")
print(f"  Max payout with cap: ${series_e.invested * (series_e.participation_cap or 0) / 1000000:.2f}M")

# Test $170M distribution
print("\nDistribution at $170M:")
dist = calc.calculate_distribution(170000000)

for sc in sorted(calc.share_classes, key=lambda x: x.priority, reverse=True):
    amount = dist.get(sc.name, 0)
    print(f"  {sc.name:<15}: ${amount/1000000:>6.2f}M")

    # Check if Series E is properly capped
    if sc.name == "Series E":
        if sc.participation_cap is not None and sc.participation_cap > 0:
            max_allowed = sc.invested * sc.participation_cap
            if amount > max_allowed:
                print(f"  >>> ERROR: Series E got ${amount/1000000:.2f}M but should be capped at ${max_allowed/1000000:.2f}M")

print(f"\nTotal: ${sum(dist.values())/1000000:.2f}M")
