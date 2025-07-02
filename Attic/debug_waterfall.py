#!/usr/bin/env python3
"""Debug waterfall calculation for $50M scenario"""

from csv_waterfall import parse_cap_table

# Parse the cap table
calc = parse_cap_table('captable-3.csv')

# Test the internal calculation methods
print("=== Testing $50M Distribution ===\n")

# First, show what happens with all liquidation preferences
print("Scenario 1: All take liquidation preferences")
dist_all_lp = calc._calculate_with_all_liquidation_preferences(50000000)

remaining = 50000000
for sc in sorted(calc.share_classes, key=lambda x: x.priority, reverse=True):
    if sc.preference_type.value != 'common':
        amount = dist_all_lp.get(sc.name, 0)
        lp = sc.invested * sc.preference_multiple
        print(f'{sc.name:<15}: LP=${lp/1000000:.2f}M, Gets=${amount/1000000:.2f}M')
        remaining -= amount

print(f'Remaining after all LPs: ${remaining/1000000:.2f}M')
print(f'Common gets: ${dist_all_lp.get("Common", 0)/1000000:.2f}M')
print(f'ESOP/Opts gets: ${dist_all_lp.get("ESOP/Opts", 0)/1000000:.2f}M')

print("\n" + "="*50 + "\n")

# Now show the actual distribution
print("Actual distribution (with conversion logic):")
dist = calc.calculate_distribution(50000000)

for sc in sorted(calc.share_classes, key=lambda x: x.priority, reverse=True):
    amount = dist.get(sc.name, 0)
    ownership = sc.shares / sum(s.shares for s in calc.share_classes) * 100
    pro_rata_50m = 50000000 * sc.shares / sum(s.shares for s in calc.share_classes)
    
    print(f'{sc.name:<15}: ${amount/1000000:>6.2f}M (Own: {ownership:>5.1f}%, Pro-rata: ${pro_rata_50m/1000000:.2f}M)')

print(f'\nTotal distributed: ${sum(dist.values())/1000000:.2f}M')

# Check conversion logic for Series E
print("\n" + "="*50 + "\n")
print("Series E conversion analysis:")
series_e = next(sc for sc in calc.share_classes if sc.name == "Series E")
print(f"- Liquidation preference: ${series_e.invested/1000000:.2f}M")
print(f"- What they get with LP: ${dist_all_lp.get('Series E', 0)/1000000:.2f}M")
print(f"- Pro-rata if all convert: ${50*series_e.shares/sum(s.shares for s in calc.share_classes):.2f}M")
print(f"- Decision: {'Convert' if dist.get('Series E', 0) > series_e.invested else 'Take LP'}")