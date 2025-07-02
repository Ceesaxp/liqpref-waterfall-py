"""
Liquidation Preference Waterfall Calculator

A comprehensive library for modeling startup liquidation preferences,
including stacked liquidation preferences, participation rights, caps,
and conversion scenarios.

Example usage:
    >>> from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType
    >>> calc = WaterfallCalculator()
    >>> 
    >>> # Add share classes
    >>> common = ShareClass("Common", 1000000, 0, PreferenceType.COMMON)
    >>> preferred = ShareClass("Series A", 200000, 900000, PreferenceType.PARTICIPATING, 1.0, 2.0, 1)
    >>> 
    >>> calc.add_share_class(common)
    >>> calc.add_share_class(preferred)
    >>> 
    >>> # Calculate distribution
    >>> distribution = calc.calculate_distribution(5000000)  # $5M exit
    >>> print(distribution)
"""

from .core import (
    WaterfallCalculator,
    ShareClass,
    PreferenceType,
    AntiDilutionType
)

from .parser import (
    parse_cap_table_csv,
    parse_cap_table_dict
)

from .formatters import (
    format_cap_table_summary,
    format_waterfall_analysis,
    format_conversion_analysis,
    format_detailed_analysis
)

__version__ = "1.0.0"
__author__ = "Liquidation Waterfall Calculator"

__all__ = [
    "WaterfallCalculator",
    "ShareClass", 
    "PreferenceType",
    "AntiDilutionType",
    "parse_cap_table_csv",
    "parse_cap_table_dict",
    "format_cap_table_summary",
    "format_waterfall_analysis", 
    "format_conversion_analysis",
    "format_detailed_analysis"
]