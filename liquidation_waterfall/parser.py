"""
Cap table parsing utilities for liquidation preference calculations.

This module provides functions to parse cap tables from CSV files and convert
them into WaterfallCalculator instances ready for analysis.
"""

import csv
from typing import List, Dict
from .core import WaterfallCalculator, ShareClass, PreferenceType, AntiDilutionType


def parse_cap_table_csv(csv_file_path: str) -> WaterfallCalculator:
    """
    Parse cap table CSV and create WaterfallCalculator.

    Supports multiple CSV formats for backward compatibility:
    - New format: Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
    - Old format: Series,Order,Shares,Price,LiqPrefMultiple,Participating,Convertible

    Args:
        csv_file_path: Path to the CSV file containing cap table data

    Returns:
        WaterfallCalculator instance populated with share classes from the CSV

    Raises:
        FileNotFoundError: If the CSV file cannot be found
        ValueError: If the CSV contains invalid data
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
            shares_raw = row.get('# Shares', row.get('Shares', 0))
            shares = int(shares_raw) if shares_raw is not None and shares_raw != '' else 0
            price_raw = row.get('Price', 0)
            price = float(price_raw) if price_raw is not None and price_raw != '' else 0.0
            liq_pref_raw = row.get('LPMultiple', row.get('LiqPrefMultiple', 1))
            liq_pref_multiple = float(liq_pref_raw) if liq_pref_raw is not None and liq_pref_raw != '' else 1.0
            participating = row.get('Participation', row.get('Participating', 'FALSE')).upper() == 'TRUE'
            convertible = row.get('Convertible', 'TRUE').upper() == 'TRUE'
            order_raw = row.get('Stack Order', row.get('Order', 0))
            stack_order = int(order_raw) if order_raw is not None and order_raw != '' else 0
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


def parse_cap_table_dict(cap_table_data: List[Dict]) -> WaterfallCalculator:
    """
    Parse cap table from a list of dictionaries and create WaterfallCalculator.

    Args:
        cap_table_data: List of dictionaries representing share classes

    Returns:
        WaterfallCalculator instance populated with share classes

    Example:
        >>> data = [
        ...     {
        ...         "Share Class": "Series A",
        ...         "Stack Order": 1,
        ...         "# Shares": 100000,
        ...         "Price": 10.0,
        ...         "LPMultiple": 1.0,
        ...         "Participation": "FALSE",
        ...         "Convertible": "TRUE"
        ...     },
        ...     {
        ...         "Share Class": "Common",
        ...         "Stack Order": 0,
        ...         "# Shares": 500000,
        ...         "Price": 1.0,
        ...         "LPMultiple": 1.0,
        ...         "Participation": "TRUE",
        ...         "Convertible": "FALSE"
        ...     }
        ... ]
        >>> calc = parse_cap_table_dict(data)
    """
    calculator = WaterfallCalculator()

    for row in cap_table_data:
        # Skip empty rows
        if not row.get('Share Class') and not row.get('Series'):
            continue

        # Handle both old and new formats
        series = row.get('Share Class', row.get('Series', ''))
        shares = int(row.get('# Shares', row.get('Shares', 0)))
        price = float(row.get('Price', 0))
        liq_pref_multiple = float(row.get('LPMultiple', row.get('LiqPrefMultiple', 1)))
        participating = row.get('Participation', row.get('Participating', 'FALSE')).upper() == 'TRUE'
        convertible = row.get('Convertible', 'TRUE').upper() == 'TRUE'
        stack_order = int(row.get('Stack Order', row.get('Order', 0)))
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

        # Priority is based on stack order
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