"""
Output formatting utilities for liquidation preference analysis.

This module provides functions to format cap table summaries and waterfall
analysis results in various human-readable formats.
"""

from typing import List, Dict
from .core import WaterfallCalculator, PreferenceType


def format_cap_table_summary(calculator: WaterfallCalculator) -> str:
    """
    Format a summary of the cap table.

    Args:
        calculator: WaterfallCalculator instance with loaded share classes

    Returns:
        Formatted string showing cap table summary
    """
    lines = []
    lines.append("Cap Table Summary")
    lines.append("=" * 80)

    total_shares = sum(sc.shares for sc in calculator.share_classes)
    total_invested = sum(sc.invested for sc in calculator.share_classes)

    # Sort by priority for display
    sorted_classes = sorted(calculator.share_classes, key=lambda x: x.priority, reverse=True)

    lines.append(f"{'Series':<12} {'Stack':<5} {'Shares':<12} {'Price':<10} {'Invested':<18} {'Type':<17} {'Cap':<8} {'Ownership':<7}")
    lines.append("-" * 100)

    for sc in sorted_classes:
        ownership_pct = sc.shares / total_shares * 100
        pref_type = sc.preference_type.value.replace('_', ' ').title()
        price = sc.invested / sc.shares if sc.shares > 0 and sc.invested > 0 else 0
        cap_str = f"{sc.participation_cap:.1f}x" if sc.participation_cap else "None"

        lines.append(f"{sc.name:<12} {sc.stack_order:<5} {sc.shares:>12,} ${price:>9.4f} ${sc.invested:>17,.2f} {pref_type:<17} {cap_str:<8} {ownership_pct:>3.1f}%")

    lines.append("-" * 100)
    lines.append(f"{'Total':<12} {'':>5} {total_shares:<12,} {'':>10} ${total_invested:<14,.2f}")
    lines.append("")

    return "\n".join(lines)


def format_waterfall_analysis(calculator: WaterfallCalculator, exit_values: List[float]) -> str:
    """
    Format waterfall analysis for given exit values.

    Args:
        calculator: WaterfallCalculator instance with loaded share classes
        exit_values: List of exit values to analyze

    Returns:
        Formatted string showing waterfall analysis across all exit values
    """
    lines = []
    lines.append("Waterfall Analysis")
    lines.append("=" * 120)

    # Header with exit values
    header = f"{'Series':<18} {'Type':<17} {'Invested':<12}"
    for exit_value in exit_values:
        header += f"${exit_value/1000000:>10.0f}M"
    lines.append(header)
    lines.append("-" * 120)

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
        lines.append(row)

    # Print totals
    lines.append("-" * 120)
    total_invested = sum(sc.invested for sc in calculator.share_classes)
    row = f"{'Total':<18} {'':>17} ${total_invested/1000000:<11.2f}M"
    for distribution in all_distributions:
        total = sum(distribution.values())
        row += f"${total/1000000:>10.2f}M"
    lines.append(row)
    lines.append("")

    return "\n".join(lines)


def format_conversion_analysis(calculator: WaterfallCalculator, exit_values: List[float]) -> str:
    """
    Format conversion analysis showing which share classes convert at each exit value.

    Args:
        calculator: WaterfallCalculator instance with loaded share classes
        exit_values: List of exit values to analyze

    Returns:
        Formatted string showing conversion decisions and rationale
    """
    lines = []
    lines.append("Conversion Analysis")
    lines.append("-" * 60)

    # Calculate distributions for each exit value
    all_distributions = []
    for exit_value in exit_values:
        distribution = calculator.calculate_distribution(exit_value)
        all_distributions.append(distribution)

    for i, exit_value in enumerate(exit_values):
        lines.append(f"At ${exit_value/1000000:.0f}M exit:")
        distribution = all_distributions[i]

        # Check which classes actually converted based on distribution
        # total_shares = sum(sc.shares for sc in calculator.share_classes)
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
            lines.append(f"  Converted to common: {', '.join(converted)}")
        else:
            lines.append("  No conversions")
        lines.append("")

    return "\n".join(lines)


def format_detailed_analysis(calculator: WaterfallCalculator, exit_value: float) -> str:
    """
    Format a detailed step-by-step analysis of the waterfall calculation.

    Args:
        calculator: WaterfallCalculator instance with loaded share classes
        exit_value: Single exit value to analyze in detail

    Returns:
        Formatted string showing step-by-step waterfall calculation
    """
    lines = []
    lines.append(f"Detailed Waterfall Analysis: ${exit_value/1000000:.1f}M Exit")
    lines.append("=" * 80)

    distribution = calculator.calculate_distribution(exit_value)

    # Show the priority structure
    lines.append("Priority Structure:")
    lines.append("-" * 40)

    preferred_classes = [sc for sc in calculator.share_classes
                        if sc.preference_type != PreferenceType.COMMON]

    if preferred_classes:
        priority_groups = {}
        for sc in preferred_classes:
            if sc.priority not in priority_groups:
                priority_groups[sc.priority] = []
            priority_groups[sc.priority].append(sc)

        for priority in sorted(priority_groups.keys(), reverse=True):
            group = priority_groups[priority]
            total_lp = sum(sc.invested * sc.preference_multiple for sc in group)
            lines.append(f"Priority {priority}: ${total_lp/1000000:.2f}M total liquidation preference")
            for sc in group:
                lp_amount = sc.invested * sc.preference_multiple
                lines.append(f"  - {sc.name}: ${lp_amount/1000000:.2f}M ({sc.preference_multiple}x)")
        lines.append("")

    # Show final distribution
    lines.append("Final Distribution:")
    lines.append("-" * 40)

    sorted_classes = sorted(calculator.share_classes, key=lambda x: x.priority, reverse=True)

    for sc in sorted_classes:
        amount = distribution.get(sc.name, 0)
        pref_type = sc.preference_type.value.replace('_', ' ').title()
        lines.append(f"{sc.name:<15} ({pref_type:<17}): ${amount/1000000:>8.2f}M")

    lines.append("-" * 40)
    total = sum(distribution.values())
    lines.append(f"{'Total':<35}: ${total/1000000:>8.2f}M")

    return "\n".join(lines)
