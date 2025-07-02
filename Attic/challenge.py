#!/usr/bin/env python3
"""
Liquidation Preference Waterfall Calculator

Solves the coding challenge for calculating liquidation preferences
with multiple stacked share classes.
"""

from waterfall import WaterfallCalculator, ShareClass, PreferenceType


def create_challenge_cap_table():
    """
    Creates the cap table from the challenge:
    - Common: 1,000,000 shares, $0 invested
    - Preferred A: 200,000 shares, $900,000 invested, 1x participating with 2x cap
    - Preferred B: 300,000 shares, $2,100,000 invested, 1x participating with 2x cap  
    - Preferred C: 1,500,000 shares, $15,000,000 invested, 1x participating with 2x cap
    """
    calculator = WaterfallCalculator()
    
    # Add share classes in priority order (C=3, B=2, A=1, Common=0)
    common = ShareClass("Common", 1000000, 0, PreferenceType.COMMON, priority=0)
    preferred_a = ShareClass("Preferred A", 200000, 900000, PreferenceType.PARTICIPATING, 1.0, 2.0, 1)
    preferred_b = ShareClass("Preferred B", 300000, 2100000, PreferenceType.PARTICIPATING, 1.0, 2.0, 2)
    preferred_c = ShareClass("Preferred C", 1500000, 15000000, PreferenceType.PARTICIPATING, 1.0, 2.0, 3)
    
    calculator.add_share_class(common)
    calculator.add_share_class(preferred_a)
    calculator.add_share_class(preferred_b)
    calculator.add_share_class(preferred_c)
    
    return calculator


def calculate_exit_scenarios():
    """Calculate distributions for the challenge exit values"""
    calculator = create_challenge_cap_table()
    exit_values = [25000000, 40000000, 50000000, 70000000, 39000000, 47000000]
    
    print("Liquidation Preference Waterfall Analysis")
    print("=" * 50)
    print()
    
    # Display ownership percentages
    total_shares = 1000000 + 200000 + 300000 + 1500000  # 3M shares
    print("Ownership Structure:")
    print(f"• Founders (Common): {1000000/total_shares:.1%}")
    print(f"• Series A Investors: {200000/total_shares:.1%}")
    print(f"• Series B Investors: {300000/total_shares:.1%}")
    print(f"• Series C Investors: {1500000/total_shares:.1%}")
    print()
    
    for exit_value in exit_values:
        print(f"Exit Value: ${exit_value:,}")
        print("-" * 30)
        
        distribution = calculator.calculate_distribution(exit_value)
        
        # Display results
        total_distributed = 0
        for share_class in ["Common", "Preferred A", "Preferred B", "Preferred C"]:
            amount = distribution.get(share_class, 0)
            total_distributed += amount
            print(f"  {share_class:<12}: ${amount:>15,.2f}")
        
        print(f"  {'Total':<12}: ${total_distributed:>15,.2f}")
        print()


if __name__ == "__main__":
    calculate_exit_scenarios()