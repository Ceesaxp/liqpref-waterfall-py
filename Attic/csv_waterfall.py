#!/usr/bin/env python3
"""
CSV-based Liquidation Preference Waterfall Calculator

Reads a cap table from CSV and calculates waterfall distributions
for specified exit values.
"""

import csv
import argparse
from typing import List, Dict
from waterfall import WaterfallCalculator, ShareClass, PreferenceType, AntiDilutionType


def parse_cap_table(csv_file_path: str) -> WaterfallCalculator:
    """
    Parse cap table CSV and create WaterfallCalculator.

    Expected CSV format:
    Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
    """
    calculator = WaterfallCalculator()

    with open(csv_file_path, 'r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            # Skip empty rows
            if not row.get('Share Class') and not row.get('Series'):
                continue

            # Handle both old and new CSV formats
            series = row.get('Share Class', row.get('Series', ''))
            shares = int(row.get('# Shares', row.get('Shares', 0)))
            price = float(row.get('Price', 0))
            liq_pref_multiple = float(row.get('LPMultiple', row.get('LiqPrefMultiple', 1)))
            participating = row.get('Participation', row.get('Participating', 'FALSE')).upper() == 'TRUE'
            convertible = row.get('Convertible', 'TRUE').upper() == 'TRUE'
            stack_order = int(row.get('Stack Order', row.get('Order', 0)))
            # Parse participation cap - it's a multiplier (e.g., 2 means 2x cap)
            cap_value = row.get('Participation Cap', '0')
            participation_cap = float(cap_value) if cap_value and cap_value != '0' else None
            ad_type_str = row.get('AD Type', 'None')

            # Calculate invested amount
            invested = shares * price if price > 0 else 0

            # Determine preference type
            if series in ['Common', 'ESOP', 'ESOP/Options', 'ESOP/Opts']:
                preference_type = PreferenceType.COMMON
            elif participating:
                preference_type = PreferenceType.PARTICIPATING
            else:
                preference_type = PreferenceType.NON_PARTICIPATING

            # Parse anti-dilution type
            try:
                ad_type = AntiDilutionType(ad_type_str)
            except ValueError:
                ad_type = AntiDilutionType.NONE

            # Priority is based on stack order (higher stack order = higher priority)
            priority = stack_order

            share_class = ShareClass(
                name=series,
                shares=shares,
                invested=invested,
                preference_type=preference_type,
                preference_multiple=liq_pref_multiple,
                participation_cap=participation_cap,
                priority=priority,
                stack_order=stack_order,
                convertible=convertible,
                anti_dilution_type=ad_type
            )

            calculator.add_share_class(share_class)

    return calculator


def print_cap_table_summary(calculator: WaterfallCalculator):
    """Print summary of the cap table"""
    print("Cap Table Summary")
    print("=" * 80)

    total_shares = sum(sc.shares for sc in calculator.share_classes)
    total_invested = sum(sc.invested for sc in calculator.share_classes)

    # Sort by priority for display
    sorted_classes = sorted(calculator.share_classes, key=lambda x: x.priority, reverse=True)

    print(f"{'Series':<12} {'Stack':<5} {'Shares':<12} {'Price':<10} {'Invested':<18} {'Type':<17} {'Cap':<8} {'Ownership':<7}")
    print("-" * 100)

    for sc in sorted_classes:
        ownership_pct = sc.shares / total_shares * 100
        pref_type = sc.preference_type.value.replace('_', ' ').title()
        price = sc.invested / sc.shares if sc.shares > 0 and sc.invested > 0 else 0
        cap_str = f"{sc.participation_cap:.1f}x" if sc.participation_cap else "None"

        print(f"{sc.name:<12} {sc.stack_order:<5} {sc.shares:>12,} ${price:>9.4f} ${sc.invested:>17,.2f} {pref_type:<17} {cap_str:<8} {ownership_pct:>3.1f}%")

    print("-" * 100)
    print(f"{'Total':<12} {'':>5} {total_shares:<12,} {'':>10} ${total_invested:<14,.2f}")
    print()


def print_waterfall_analysis(calculator: WaterfallCalculator, exit_values: List[float]):
    """Print waterfall analysis for given exit values"""
    print("Waterfall Analysis")
    print("=" * 120)

    # Header with exit values
    header = f"{'Series':<18} {'Type':<17} {'Invested':<12}"
    for exit_value in exit_values:
        header += f"${exit_value/1000000:>10.0f}M"
    print(header)
    print("-" * 120)

    # Calculate distributions for each exit value
    all_distributions = []
    for exit_value in exit_values:
        distribution = calculator.calculate_distribution(exit_value)
        all_distributions.append(distribution)

    # Print results for each share class
    sorted_classes = sorted(calculator.share_classes, key=lambda x: x.priority, reverse=True)

    for sc in sorted_classes:
        pref_type = sc.preference_type.value.replace('_', ' ').title()
        row = f"{sc.name:<18} {pref_type:<17} ${sc.invested/1000000:<11.2f}M"

        for distribution in all_distributions:
            amount = distribution.get(sc.name, 0)
            row += f"${amount/1000000:>10.2f}M"
        print(row)

    # Print totals
    print("-" * 120)
    total_invested = sum(sc.invested for sc in calculator.share_classes)
    row = f"{'Total':<18} {'':>17} ${total_invested/1000000:<11.2f}M"
    for distribution in all_distributions:
        total = sum(distribution.values())
        row += f"${total/1000000:>10.2f}M"
    print(row)
    print()

    # Print conversion summary
    print("Conversion Analysis")
    print("-" * 60)
    for i, exit_value in enumerate(exit_values):
        print(f"At ${exit_value/1000000:.0f}M exit:")
        distribution = all_distributions[i]

        # Check which classes actually converted based on distribution
        total_shares = sum(sc.shares for sc in calculator.share_classes)
        converted = []

        for sc in calculator.share_classes:
            if sc.preference_type != PreferenceType.COMMON and sc.convertible:
                liquidation_amount = sc.invested * sc.preference_multiple
                actual_amount = distribution.get(sc.name, 0)

                # For non-participating: check if they got more than liquidation preference
                # For participating: they don't convert, but may hit their cap
                if sc.preference_type == PreferenceType.NON_PARTICIPATING:
                    if actual_amount > liquidation_amount * 1.01:  # 1% tolerance
                        converted.append(f"{sc.name} (${liquidation_amount/1000000:.2f}M → ${actual_amount/1000000:.2f}M)")
                elif sc.preference_type == PreferenceType.PARTICIPATING:
                    # Check if they hit their cap
                    if sc.participation_cap and actual_amount >= sc.invested * sc.participation_cap * 0.99:
                        converted.append(f"{sc.name} (capped at ${actual_amount/1000000:.2f}M)")

        if converted:
            print(f"  Converted to common: {', '.join(converted)}")
        else:
            print("  No conversions")
        print()
    print()


def main():
    parser = argparse.ArgumentParser(description='Calculate liquidation preference waterfall from CSV')
    parser.add_argument('csv_file', help='Path to cap table CSV file')
    parser.add_argument('--exit-values', nargs='+', type=float,
                        default=[15000000, 25000000, 50000000, 100000000],
                        help='Exit values to analyze (default: 15M 25M 50M 100M)')
    parser.add_argument('--summary', action='store_true',
                        help='Show cap table summary')

    args = parser.parse_args()

    try:
        # Parse cap table
        calculator = parse_cap_table(args.csv_file)

        if args.summary:
            print_cap_table_summary(calculator)

        # Run waterfall analysis
        print_waterfall_analysis(calculator, args.exit_values)

    except FileNotFoundError:
        print(f"Error: Could not find file '{args.csv_file}'")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
