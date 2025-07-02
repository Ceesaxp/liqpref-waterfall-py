#!/usr/bin/env python3
"""Test stacking groups with different multiples within same priority"""

from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType

# Create the example scenario from the description
calc = WaterfallCalculator()

# Series B shareholders (all at stack order 2)
shareholder1 = ShareClass(
    name="Shareholder 1",
    shares=1000000,
    invested=10000000,  # 1M shares * $10
    preference_type=PreferenceType.NON_PARTICIPATING,
    preference_multiple=2.0,
    priority=2
)

shareholder2 = ShareClass(
    name="Shareholder 2",
    shares=500000,
    invested=5000000,   # 500K shares * $10
    preference_type=PreferenceType.NON_PARTICIPATING,
    preference_multiple=1.5,
    priority=2
)

shareholder3 = ShareClass(
    name="Shareholder 3",
    shares=500000,
    invested=5000000,   # 500K shares * $10
    preference_type=PreferenceType.NON_PARTICIPATING,
    preference_multiple=1.25,
    priority=2
)

calc.add_share_class(shareholder1)
calc.add_share_class(shareholder2)
calc.add_share_class(shareholder3)

print("=== Pro-rata within Priority Level Test ===")
print("$20M exit scenario:")
print()

# Calculate liquidation preferences
sh1_lp = shareholder1.invested * shareholder1.preference_multiple  # 10M * 2.0 = 20M
sh2_lp = shareholder2.invested * shareholder2.preference_multiple  # 5M * 1.5 = 7.5M
sh3_lp = shareholder3.invested * shareholder3.preference_multiple  # 5M * 1.25 = 6.25M
total_lp = sh1_lp + sh2_lp + sh3_lp  # 33.75M

print("Liquidation Preferences:")
print(f"  Shareholder 1: ${sh1_lp/1000000:.1f}M")
print(f"  Shareholder 2: ${sh2_lp/1000000:.1f}M")
print(f"  Shareholder 3: ${sh3_lp/1000000:.1f}M")
print(f"  Total LP: ${total_lp/1000000:.2f}M")
print()

# Expected pro-rata payouts at $20M
exit_value = 20000000
expected_sh1 = exit_value * (sh1_lp / total_lp)  # 20 * 20 / 33.75 = 11.85M
expected_sh2 = exit_value * (sh2_lp / total_lp)  # 20 * 7.5 / 33.75 = 4.44M
expected_sh3 = exit_value * (sh3_lp / total_lp)  # 20 * 6.25 / 33.75 = 3.70M

print("Expected Pro-rata Payouts:")
print(f"  Shareholder 1: ${expected_sh1/1000000:.2f}M")
print(f"  Shareholder 2: ${expected_sh2/1000000:.2f}M")
print(f"  Shareholder 3: ${expected_sh3/1000000:.2f}M")
print(f"  Total: ${(expected_sh1 + expected_sh2 + expected_sh3)/1000000:.2f}M")
print()

# Actual calculation
distribution = calc.calculate_distribution(exit_value)

print("Actual Distribution:")
print(f"  Shareholder 1: ${distribution.get('Shareholder 1', 0)/1000000:.2f}M")
print(f"  Shareholder 2: ${distribution.get('Shareholder 2', 0)/1000000:.2f}M")
print(f"  Shareholder 3: ${distribution.get('Shareholder 3', 0)/1000000:.2f}M")
print(f"  Total: ${sum(distribution.values())/1000000:.2f}M")
print()

# Check if results match
tolerance = 10000  # $10K tolerance
sh1_actual = distribution.get('Shareholder 1', 0)
sh2_actual = distribution.get('Shareholder 2', 0)
sh3_actual = distribution.get('Shareholder 3', 0)

print("Validation:")
print(f"  Shareholder 1: {'✓' if abs(sh1_actual - expected_sh1) < tolerance else '✗'}")
print(f"  Shareholder 2: {'✓' if abs(sh2_actual - expected_sh2) < tolerance else '✗'}")
print(f"  Shareholder 3: {'✓' if abs(sh3_actual - expected_sh3) < tolerance else '✗'}")
