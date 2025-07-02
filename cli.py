#!/usr/bin/env python3
"""
Liquidation Preference Waterfall (LPW) - Command Line Interface

A standalone application for calculating liquidation preference waterfalls
from CSV cap tables. This tool models how proceeds from a company sale are
distributed among different classes of shareholders based on their liquidation
preferences, participation rights, and conversion options.

Usage:
    cli.py cap_table.csv --exit-values 15M 25M 50M 100M
    cli.py cap_table.csv --summary --detailed
"""

import argparse
import sys
from typing import List
from liquidation_waterfall import (
    parse_cap_table_csv, 
    format_cap_table_summary,
    format_waterfall_analysis,
    format_conversion_analysis,
    format_detailed_analysis
)


def parse_exit_values(exit_values: List[str]) -> List[float]:
    """
    Parse exit values from command line strings.
    
    Supports formats like:
    - "15M" or "15m" -> 15,000,000
    - "1.5B" or "1.5b" -> 1,500,000,000  
    - "25000000" -> 25,000,000
    
    Args:
        exit_values: List of exit value strings
        
    Returns:
        List of float values in dollars
        
    Raises:
        ValueError: If any exit value cannot be parsed
    """
    parsed_values = []
    
    for value_str in exit_values:
        value_str = value_str.strip().upper()
        
        try:
            if value_str.endswith('M'):
                # Million
                base_value = float(value_str[:-1])
                parsed_values.append(base_value * 1_000_000)
            elif value_str.endswith('B'):
                # Billion
                base_value = float(value_str[:-1])
                parsed_values.append(base_value * 1_000_000_000)
            elif value_str.endswith('K'):
                # Thousand
                base_value = float(value_str[:-1])
                parsed_values.append(base_value * 1_000)
            else:
                # Raw number
                parsed_values.append(float(value_str))
        except ValueError:
            raise ValueError(f"Invalid exit value format: {value_str}")
    
    return parsed_values


def main():
    """Main command line interface."""
    parser = argparse.ArgumentParser(
        description='Calculate liquidation preference waterfall from CSV cap table',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s captable.csv
  %(prog)s captable.csv --exit-values 15M 25M 50M 100M
  %(prog)s captable.csv --summary --detailed
  %(prog)s captable.csv --exit-values 1.5B --detailed

Exit value formats:
  15M, 15m      = 15 million
  1.5B, 1.5b    = 1.5 billion  
  500K, 500k    = 500 thousand
  25000000      = 25 million (raw number)
        """
    )
    
    parser.add_argument(
        'csv_file', 
        help='Path to cap table CSV file'
    )
    
    parser.add_argument(
        '--exit-values', 
        nargs='+', 
        default=['15M', '25M', '50M', '100M'],
        help='Exit values to analyze (default: 15M 25M 50M 100M). ' +
             'Supports formats like 15M, 1.5B, 500K, or raw numbers.'
    )
    
    parser.add_argument(
        '--summary', 
        action='store_true',
        help='Show detailed cap table summary'
    )
    
    parser.add_argument(
        '--detailed', 
        action='store_true',
        help='Show detailed step-by-step analysis for each exit value'
    )
    
    parser.add_argument(
        '--conversion-only', 
        action='store_true',
        help='Show only conversion analysis'
    )

    args = parser.parse_args()

    try:
        # Parse exit values
        try:
            exit_values = parse_exit_values(args.exit_values)
        except ValueError as e:
            print(f"Error parsing exit values: {e}", file=sys.stderr)
            return 1

        # Parse cap table
        try:
            calculator = parse_cap_table_csv(args.csv_file)
        except FileNotFoundError:
            print(f"Error: Could not find file '{args.csv_file}'", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error parsing cap table: {e}", file=sys.stderr)
            return 1

        if not calculator.share_classes:
            print("Warning: No share classes found in cap table", file=sys.stderr)
            return 1

        # Show cap table summary if requested
        if args.summary:
            print(format_cap_table_summary(calculator))

        # Show conversion analysis only
        if args.conversion_only:
            print(format_conversion_analysis(calculator, exit_values))
            return 0

        # Show detailed analysis for each exit value
        if args.detailed:
            for exit_value in exit_values:
                print(format_detailed_analysis(calculator, exit_value))
                print()
        else:
            # Show standard waterfall analysis
            print(format_waterfall_analysis(calculator, exit_values))
            print(format_conversion_analysis(calculator, exit_values))

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())