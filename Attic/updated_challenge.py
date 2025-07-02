#!/usr/bin/env python3
"""
Updated Liquidation Preference Waterfall Calculator

Solves the updated coding challenge for calculating liquidation preferences
based on the new README requirements.
"""

from waterfall import WaterfallCalculator, ShareClass, PreferenceType, AntiDilutionType
from csv_waterfall import print_waterfall_analysis


def create_updated_challenge_cap_table():
    """
    Creates the cap table from the updated challenge:
    Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
    """
    calculator = WaterfallCalculator()
    
    # Define the updated cap table from README
    cap_table_data = [
        ("Series E", 7, 1500000, 9.00, 1, False, True, 0, "WA"),
        ("Series D", 6, 870000, 35.00, 1, False, True, 0, "None"),
        ("Series C", 5, 600000, 31.00, 1, False, True, 0, "None"),
        ("Series B2", 4, 67000, 25.00, 1, False, True, 0, "None"),
        ("Series B1", 4, 165000, 22.00, 1, False, True, 0, "None"),
        ("Series A2", 3, 108000, 18.00, 1, False, True, 0, "None"),
        ("Series A1", 2, 185000, 17.00, 1, False, True, 0, "None"),
        ("Seed", 1, 79000, 14.50, 1, False, True, 0, "None"),
        ("Common", 0, 650000, 1.00, 0, True, False, 0, "None"),
        ("ESOP/Options", 0, 500000, 0.00, 0, True, False, 0, "None"),
    ]
    
    for name, stack_order, shares, price, lp_multiple, participating, convertible, part_cap, ad_type in cap_table_data:
        # Calculate invested amount
        invested = shares * price if price > 0 else 0
        
        # Determine preference type
        if name in ['Common', 'ESOP/Options']:
            preference_type = PreferenceType.COMMON
        elif participating:
            preference_type = PreferenceType.PARTICIPATING
        else:
            preference_type = PreferenceType.NON_PARTICIPATING
        
        # Parse anti-dilution type
        try:
            anti_dilution_type = AntiDilutionType(ad_type)
        except ValueError:
            anti_dilution_type = AntiDilutionType.NONE
        
        # Participation cap (0 means no cap, None means uncapped)
        participation_cap = None if part_cap == 0 else part_cap
        
        share_class = ShareClass(
            name=name,
            shares=shares,
            invested=invested,
            preference_type=preference_type,
            preference_multiple=lp_multiple,
            participation_cap=participation_cap,
            priority=stack_order,
            stack_order=stack_order,
            convertible=convertible,
            anti_dilution_type=anti_dilution_type
        )
        
        calculator.add_share_class(share_class)
    
    return calculator


def calculate_updated_exit_scenarios():
    """Calculate distributions for the updated challenge exit values"""
    calculator = create_updated_challenge_cap_table()
    exit_values = [15000000, 50000000, 75000000, 150000000, 250000000]
    
    print("UPDATED LIQUIDATION PREFERENCE WATERFALL ANALYSIS")
    print("=" * 60)
    print()
    
    # Display ownership percentages
    total_shares = sum(sc.shares for sc in calculator.share_classes)
    print("Ownership Structure:")
    for sc in sorted(calculator.share_classes, key=lambda x: x.stack_order, reverse=True):
        ownership_pct = sc.shares / total_shares * 100
        print(f"• {sc.name}: {ownership_pct:.1f}%")
    print()
    
    print_waterfall_analysis(calculator, exit_values)


def compare_with_readme_examples():
    """Compare results with examples from README"""
    calculator = create_updated_challenge_cap_table()
    
    print("VALIDATION AGAINST README EXAMPLES")
    print("=" * 60)
    
    # Test $180M scenario (all convert to common)
    print("At $180M exit (all should convert to common):")
    distribution = calculator.calculate_distribution(180000000)
    
    expected_180m = {
        "Series E": 57.2,
        "Series D": 33.1, 
        "Series C": 22.9,
        "Series B2": 2.6,
        "Series B1": 6.3,
        "Series A2": 4.1,
        "Series A1": 7.0,
        "Seed": 3.0,
        "Common": 24.8,
        "ESOP/Options": 19.1
    }
    
    print("Expected vs Actual (in $M):")
    for name, expected in expected_180m.items():
        actual = distribution.get(name, 0) / 1000000
        status = "✓" if abs(actual - expected) < 1.0 else "✗"
        print(f"  {status} {name:<15}: Expected ${expected:>6.1f}M, Actual ${actual:>6.1f}M")
    print()
    
    # Test $18M scenario  
    print("At $18M exit (Series E gets $13.5M, Series D gets $4.5M):")
    distribution = calculator.calculate_distribution(18000000)
    
    for name in ["Series E", "Series D", "Series C", "Common", "ESOP/Options"]:
        actual = distribution.get(name, 0) / 1000000
        print(f"  {name:<15}: ${actual:>6.2f}M")
    print()


if __name__ == "__main__":
    calculate_updated_exit_scenarios()
    print()
    compare_with_readme_examples()