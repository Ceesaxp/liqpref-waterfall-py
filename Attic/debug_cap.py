#!/usr/bin/env python3
"""Debug participation cap calculation"""

from csv_waterfall import parse_cap_table

calc = parse_cap_table('captable-3.csv')

# Check what the _calculate_with_all_liquidation_preferences method returns
print("Testing $170M with all liquidation preferences:")
dist_all_lp = calc._calculate_with_all_liquidation_preferences(170000000)

series_e = next(sc for sc in calc.share_classes if sc.name == "Series E")
print(f"\nSeries E:")
print(f"  Type: {series_e.preference_type}")
print(f"  Invested: ${series_e.invested/1000000:.2f}M")
print(f"  Cap: {series_e.participation_cap}x = ${series_e.invested * series_e.participation_cap / 1000000:.2f}M")
print(f"  Got in all-LP scenario: ${dist_all_lp.get('Series E', 0)/1000000:.2f}M")

# Check if Series E is choosing to convert
print("\nChecking conversion logic...")
lp_amount = dist_all_lp.get('Series E', 0)
test_dist = calc._calculate_with_conversions(170000000, ['Series E'])
convert_amount = test_dist.get('Series E', 0)

print(f"  With LP: ${lp_amount/1000000:.2f}M")
print(f"  If convert: ${convert_amount/1000000:.2f}M")
print(f"  Decision: {'Convert' if convert_amount > lp_amount else 'Take LP'}")

# Check which shares are converting
print("\nChecking all conversion decisions:")
all_lp_dist = calc._calculate_with_all_liquidation_preferences(170000000)
converting = []

for sc in calc.share_classes:
    if sc.preference_type.value == 'non_participating' and sc.convertible:
        lp_amt = all_lp_dist.get(sc.name, 0)
        test_dist = calc._calculate_with_conversions(170000000, [sc.name])
        convert_amt = test_dist.get(sc.name, 0)
        
        if convert_amt > lp_amt:
            converting.append(sc.name)
            print(f"  {sc.name}: LP=${lp_amt/1000000:.2f}M < Convert=${convert_amt/1000000:.2f}M -> CONVERT")
        else:
            print(f"  {sc.name}: LP=${lp_amt/1000000:.2f}M >= Convert=${convert_amt/1000000:.2f}M -> KEEP LP")

print(f"\nConverting shares: {converting}")

# Final distribution
print("\nFinal distribution:")
final_dist = calc.calculate_distribution(170000000)
print(f"  Series E gets: ${final_dist.get('Series E', 0)/1000000:.2f}M")

# Check if this matches a conversion scenario
if converting:
    print("\nDistribution with conversions:")
    conv_dist = calc._calculate_with_conversions(170000000, converting)
    print(f"  Series E gets: ${conv_dist.get('Series E', 0)/1000000:.2f}M")