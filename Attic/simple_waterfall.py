#!/usr/bin/env python3
"""
Simple Waterfall Calculator

Basic command-line tool that reads a cap table CSV and produces
a waterfall table for specified exit values.
"""

import sys
from csv_waterfall import parse_cap_table, print_waterfall_analysis


def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_waterfall.py <captable.csv> [exit_value1] [exit_value2] ...")
        print("Example: python simple_waterfall.py captable.csv 15000000 25000000 50000000")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Parse exit values from command line, or use defaults
    if len(sys.argv) > 2:
        try:
            exit_values = [float(x) for x in sys.argv[2:]]
        except ValueError:
            print("Error: Exit values must be numbers")
            sys.exit(1)
    else:
        # Default exit values
        exit_values = [15000000, 25000000, 50000000, 100000000]
    
    try:
        # Parse cap table and run analysis
        calculator = parse_cap_table(csv_file)
        print_waterfall_analysis(calculator, exit_values)
        
    except FileNotFoundError:
        print(f"Error: Could not find file '{csv_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()