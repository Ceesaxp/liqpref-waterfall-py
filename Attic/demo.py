#!/usr/bin/env python3
"""
Waterfall Calculator Demo

Demonstrates the liquidation preference waterfall calculator
with both the challenge example and CSV-based cap table.
"""

from waterfall import WaterfallCalculator, ShareClass, PreferenceType
from csv_waterfall import parse_cap_table, print_cap_table_summary, print_waterfall_analysis
from updated_challenge import create_updated_challenge_cap_table


def demo_challenge_example():
    """Demonstrate the original coding challenge example"""
    print("🎯 CODING CHALLENGE EXAMPLE")
    print("=" * 60)

    calculator = WaterfallCalculator()

    # Add the challenge cap table
    common = ShareClass("Common", 1000000, 0, PreferenceType.COMMON)
    preferred_a = ShareClass("Preferred A", 200000, 900000, PreferenceType.PARTICIPATING, 1.0, 2.0, 1)
    preferred_b = ShareClass("Preferred B", 300000, 2100000, PreferenceType.PARTICIPATING, 1.0, 2.0, 2)
    preferred_c = ShareClass("Preferred C", 1500000, 15000000, PreferenceType.PARTICIPATING, 1.0, 2.0, 3)

    calculator.add_share_class(common)
    calculator.add_share_class(preferred_a)
    calculator.add_share_class(preferred_b)
    calculator.add_share_class(preferred_c)

    # Challenge exit values
    exit_values = [25000000, 40000000, 50000000, 70000000, 39000000, 47000000]
    print_waterfall_analysis(calculator, exit_values)


def demo_updated_challenge():
    """Demonstrate the updated challenge from README"""
    print("🚀 UPDATED CHALLENGE FROM README")
    print("=" * 60)

    calculator = create_updated_challenge_cap_table()

    # Updated challenge exit values
    exit_values = [15000000, 50000000, 75000000, 150000000, 250000000]
    print_waterfall_analysis(calculator, exit_values)


def demo_csv_example():
    """Demonstrate CSV-based cap table"""
    print("📊 CSV CAP TABLE EXAMPLE")
    print("=" * 60)

    try:
        calculator = parse_cap_table('captable-3.csv')
        print_cap_table_summary(calculator)

        # Interesting exit scenarios
        exit_values = [15000000, 25000000, 50000000, 100000000]
        print_waterfall_analysis(calculator, exit_values)

    except FileNotFoundError:
        print("captable.csv not found - skipping CSV demo")
        print()


def main():
    print("💰 LIQUIDATION PREFERENCE WATERFALL CALCULATOR")
    print("=" * 80)
    print()

    demo_challenge_example()
    demo_updated_challenge()
    demo_csv_example()

    print("✅ Demo completed!")
    print()
    print("Usage examples:")
    print("  python challenge.py                     # Run original challenge")
    print("  python updated_challenge.py             # Run updated challenge from README")
    print("  python csv_waterfall.py captable.csv   # Analyze CSV cap table")
    print("  python simple_waterfall.py captable.csv 20000000 50000000  # Custom exits")
    print("  python test_waterfall.py               # Run original test suite")
    print("  python test_updated_waterfall.py       # Run updated test suite")


if __name__ == "__main__":
    main()
