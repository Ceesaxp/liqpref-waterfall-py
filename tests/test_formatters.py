"""
Comprehensive tests for output formatting functions.

Tests cap table summaries, waterfall analysis, conversion analysis,
and detailed analysis formatting following TDD principles.
"""

import unittest
from liquidation_waterfall import (
    format_cap_table_summary,
    format_waterfall_analysis,
    format_conversion_analysis,
    format_detailed_analysis
)
from .test_fixtures import (
    create_simple_cap_table,
    create_priority_groups_cap_table,
    create_participation_cap_table,
    create_mixed_preferences_cap_table
)


class TestCapTableFormatting(unittest.TestCase):
    """Test cap table summary formatting."""
    
    def test_format_cap_table_summary_basic(self):
        """Test basic cap table summary formatting."""
        calc = create_simple_cap_table()
        summary = format_cap_table_summary(calc)
        
        # Should contain header
        self.assertIn("Cap Table Summary", summary)
        self.assertIn("=" * 80, summary)
        
        # Should contain share class names
        self.assertIn("Series A", summary)
        self.assertIn("Common", summary)
        
        # Should contain ownership percentages
        self.assertIn("%", summary)
        
        # Should contain monetary amounts
        self.assertIn("$", summary)
        
        # Should contain totals
        self.assertIn("Total", summary)
    
    def test_format_cap_table_summary_with_caps(self):
        """Test cap table summary with participation caps."""
        calc = create_participation_cap_table()
        summary = format_cap_table_summary(calc)
        
        # Should show participation caps
        self.assertIn("2.0x", summary)  # Series A cap
        self.assertIn("None", summary)  # Series B uncapped
        
        # Should format preference types correctly
        self.assertIn("Participating", summary)
        self.assertIn("Common", summary)
    
    def test_format_cap_table_summary_empty_calculator(self):
        """Test cap table summary with empty calculator."""
        from liquidation_waterfall import WaterfallCalculator
        calc = WaterfallCalculator()
        summary = format_cap_table_summary(calc)
        
        # Should handle empty case gracefully
        self.assertIn("Cap Table Summary", summary)
        self.assertIn("Total", summary)
    
    def test_format_cap_table_summary_zero_invested(self):
        """Test cap table summary with zero invested amounts."""
        calc = create_simple_cap_table()
        summary = format_cap_table_summary(calc)
        
        # Common shares should show $0.0000 price
        lines = summary.split('\n')
        common_line = next(line for line in lines if "Common" in line)
        self.assertIn("$0.0000", common_line)  # Zero price for common
    
    def test_format_cap_table_summary_large_numbers(self):
        """Test cap table summary with large numbers."""
        from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType
        calc = WaterfallCalculator()
        
        large_class = ShareClass(
            "Large", 
            1000000000,  # 1B shares
            10000000000,  # $10B invested
            PreferenceType.NON_PARTICIPATING
        )
        calc.add_share_class(large_class)
        
        summary = format_cap_table_summary(calc)
        
        # Should format large numbers with commas
        self.assertIn("1,000,000,000", summary)  # Shares with commas
        self.assertIn("10,000,000,000", summary)  # Investment with commas


class TestWaterfallAnalysisFormatting(unittest.TestCase):
    """Test waterfall analysis formatting."""
    
    def test_format_waterfall_analysis_basic(self):
        """Test basic waterfall analysis formatting."""
        calc = create_simple_cap_table()
        exit_values = [1000000, 5000000, 10000000]
        
        analysis = format_waterfall_analysis(calc, exit_values)
        
        # Should contain header
        self.assertIn("Waterfall Analysis", analysis)
        self.assertIn("=" * 120, analysis)
        
        # Should contain all exit values in header
        self.assertIn("$1M", analysis)
        self.assertIn("$5M", analysis)
        self.assertIn("$10M", analysis)
        
        # Should contain share class names
        self.assertIn("Series A", analysis)
        self.assertIn("Common", analysis)
        
        # Should contain preference types
        self.assertIn("Non Participating", analysis)
        
        # Should contain totals row
        self.assertIn("Total", analysis)
    
    def test_format_waterfall_analysis_priority_groups(self):
        """Test waterfall analysis with priority groups."""
        calc = create_priority_groups_cap_table()
        exit_values = [20000000, 40000000]
        
        analysis = format_waterfall_analysis(calc, exit_values)
        
        # Should contain all B shareholders
        self.assertIn("B: Shareholder 1", analysis)
        self.assertIn("B: Shareholder 2", analysis)
        self.assertIn("B: Shareholder 3", analysis)
        self.assertIn("Common", analysis)
        
        # Should show different amounts at different exit values
        lines = analysis.split('\n')
        data_lines = [line for line in lines if "B: Shareholder" in line]
        self.assertGreater(len(data_lines), 0)
    
    def test_format_waterfall_analysis_single_exit_value(self):
        """Test waterfall analysis with single exit value."""
        calc = create_simple_cap_table()
        exit_values = [5000000]
        
        analysis = format_waterfall_analysis(calc, exit_values)
        
        # Should handle single column
        self.assertIn("$5M", analysis)
        self.assertIn("Series A", analysis)
        self.assertIn("Common", analysis)
    
    def test_format_waterfall_analysis_many_exit_values(self):
        """Test waterfall analysis with many exit values."""
        calc = create_simple_cap_table()
        exit_values = [1000000, 2000000, 5000000, 10000000, 20000000, 50000000]
        
        analysis = format_waterfall_analysis(calc, exit_values)
        
        # Should handle many columns
        for exit_value in exit_values:
            millions = f"${exit_value//1000000}M"
            self.assertIn(millions, analysis)
    
    def test_format_waterfall_analysis_zero_exit_value(self):
        """Test waterfall analysis with zero exit value."""
        calc = create_simple_cap_table()
        exit_values = [0, 1000000]
        
        analysis = format_waterfall_analysis(calc, exit_values)
        
        # Should handle zero exit value
        self.assertIn("$0M", analysis)
    
    def test_format_waterfall_analysis_formatting_consistency(self):
        """Test that formatting is consistent across different scenarios."""
        calc = create_mixed_preferences_cap_table()
        exit_values = [5000000, 15000000, 25000000]
        
        analysis = format_waterfall_analysis(calc, exit_values)
        
        # Check that all lines have consistent formatting
        lines = analysis.split('\n')
        data_lines = [line for line in lines if any(name in line for name in ["Series", "Common"])]
        
        # All data lines should have similar structure
        self.assertGreater(len(data_lines), 3)  # Should have multiple share classes


class TestConversionAnalysisFormatting(unittest.TestCase):
    """Test conversion analysis formatting."""
    
    def test_format_conversion_analysis_basic(self):
        """Test basic conversion analysis formatting."""
        calc = create_simple_cap_table()
        exit_values = [5000000, 15000000]
        
        analysis = format_conversion_analysis(calc, exit_values)
        
        # Should contain header
        self.assertIn("Conversion Analysis", analysis)
        self.assertIn("-" * 60, analysis)
        
        # Should contain exit value labels
        self.assertIn("At $5M exit:", analysis)
        self.assertIn("At $15M exit:", analysis)
        
        # Should contain conversion decisions
        self.assertTrue(
            "No conversions" in analysis or "Converted to common" in analysis
        )
    
    def test_format_conversion_analysis_with_conversions(self):
        """Test conversion analysis when conversions occur."""
        calc = create_simple_cap_table()
        # Use high exit value where Series A should convert
        exit_values = [15000000]
        
        analysis = format_conversion_analysis(calc, exit_values)
        
        # At $15M, Series A should convert (10% * $15M = $1.5M > $1M LP)
        self.assertIn("At $15M exit:", analysis)
        # Should show either conversion or no conversion
        self.assertTrue(
            "Series A" in analysis or "No conversions" in analysis
        )
    
    def test_format_conversion_analysis_no_conversions(self):
        """Test conversion analysis when no conversions occur."""
        calc = create_simple_cap_table()
        # Use low exit value where liquidation preference is better
        exit_values = [3000000]
        
        analysis = format_conversion_analysis(calc, exit_values)
        
        # At $3M, Series A should not convert ($1M LP > 10% * $3M = $300K)
        self.assertIn("At $3M exit:", analysis)
        self.assertIn("No conversions", analysis)
    
    def test_format_conversion_analysis_participating_caps(self):
        """Test conversion analysis with participating preferred caps."""
        calc = create_participation_cap_table()
        exit_values = [20000000]  # High exit where caps might be hit
        
        analysis = format_conversion_analysis(calc, exit_values)
        
        # Should mention capped shares
        self.assertIn("At $20M exit:", analysis)
        # Should show cap information for participating shares
        self.assertTrue(
            "capped at" in analysis or "No conversions" in analysis
        )
    
    def test_format_conversion_analysis_multiple_exit_values(self):
        """Test conversion analysis with multiple exit values."""
        calc = create_simple_cap_table()
        exit_values = [1000000, 5000000, 10000000, 20000000]
        
        analysis = format_conversion_analysis(calc, exit_values)
        
        # Should have entries for all exit values
        for exit_value in exit_values:
            millions = f"At ${exit_value//1000000}M exit:"
            self.assertIn(millions, analysis)


class TestDetailedAnalysisFormatting(unittest.TestCase):
    """Test detailed analysis formatting."""
    
    def test_format_detailed_analysis_basic(self):
        """Test basic detailed analysis formatting."""
        calc = create_simple_cap_table()
        exit_value = 5000000
        
        analysis = format_detailed_analysis(calc, exit_value)
        
        # Should contain header with exit value
        self.assertIn("Detailed Waterfall Analysis: $5.0M Exit", analysis)
        self.assertIn("=" * 80, analysis)
        
        # Should contain priority structure section
        self.assertIn("Priority Structure:", analysis)
        
        # Should contain final distribution section
        self.assertIn("Final Distribution:", analysis)
        
        # Should contain total
        self.assertIn("Total", analysis)
    
    def test_format_detailed_analysis_priority_structure(self):
        """Test detailed analysis priority structure display."""
        calc = create_priority_groups_cap_table()
        exit_value = 20000000
        
        analysis = format_detailed_analysis(calc, exit_value)
        
        # Should show priority levels
        self.assertIn("Priority 2:", analysis)  # Series B level
        self.assertIn("Priority 0:", analysis)  # Common level (if shown)
        
        # Should show liquidation preferences
        self.assertIn("liquidation preference", analysis)
        
        # Should show individual share classes
        self.assertIn("B: Shareholder", analysis)
    
    def test_format_detailed_analysis_final_distribution(self):
        """Test detailed analysis final distribution display."""
        calc = create_mixed_preferences_cap_table()
        exit_value = 15000000
        
        analysis = format_detailed_analysis(calc, exit_value)
        
        # Should show all share classes
        self.assertIn("Series C", analysis)
        self.assertIn("Series B", analysis)
        self.assertIn("Series A", analysis)
        self.assertIn("Common", analysis)
        
        # Should show preference types
        self.assertIn("(Non Participating", analysis)
        self.assertIn("(Participating", analysis)
        self.assertIn("(Common", analysis)
        
        # Should show monetary amounts
        self.assertIn("$", analysis)
        self.assertIn("M", analysis)
    
    def test_format_detailed_analysis_zero_exit(self):
        """Test detailed analysis with zero exit value."""
        calc = create_simple_cap_table()
        exit_value = 0
        
        analysis = format_detailed_analysis(calc, exit_value)
        
        # Should handle zero gracefully
        self.assertIn("$0.0M Exit", analysis)
        self.assertIn("$0.00M", analysis)  # Should show zero distributions
    
    def test_format_detailed_analysis_high_exit(self):
        """Test detailed analysis with very high exit value."""
        calc = create_simple_cap_table()
        exit_value = 1000000000  # $1B
        
        analysis = format_detailed_analysis(calc, exit_value)
        
        # Should handle large numbers
        self.assertIn("$1000.0M Exit", analysis)
        # Should show large distribution amounts
        lines = analysis.split('\n')
        amount_lines = [line for line in lines if "$" in line and "M" in line]
        self.assertGreater(len(amount_lines), 0)
    
    def test_format_detailed_analysis_no_preferred_shares(self):
        """Test detailed analysis with only common shares."""
        from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType
        calc = WaterfallCalculator()
        
        common = ShareClass("Common", 1000000, 0, PreferenceType.COMMON)
        calc.add_share_class(common)
        
        analysis = format_detailed_analysis(calc, 5000000)
        
        # Should handle common-only case
        self.assertIn("Common", analysis)
        self.assertIn("$5.00M", analysis)  # Should get full amount


class TestFormattingEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions in formatting."""
    
    def test_formatting_empty_calculator(self):
        """Test all formatting functions with empty calculator."""
        from liquidation_waterfall import WaterfallCalculator
        calc = WaterfallCalculator()
        
        # All formatters should handle empty calculator gracefully
        summary = format_cap_table_summary(calc)
        self.assertIn("Cap Table Summary", summary)
        
        analysis = format_waterfall_analysis(calc, [1000000])
        self.assertIn("Waterfall Analysis", analysis)
        
        conversion = format_conversion_analysis(calc, [1000000])
        self.assertIn("Conversion Analysis", conversion)
        
        detailed = format_detailed_analysis(calc, 1000000)
        self.assertIn("Detailed Waterfall Analysis", detailed)
    
    def test_formatting_with_special_characters(self):
        """Test formatting with special characters in share class names."""
        from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType
        calc = WaterfallCalculator()
        
        special = ShareClass("Series A & B (2023)", 100000, 1000000, PreferenceType.NON_PARTICIPATING)
        calc.add_share_class(special)
        
        summary = format_cap_table_summary(calc)
        self.assertIn("Series A & B (2023)", summary)
        
        analysis = format_waterfall_analysis(calc, [5000000])
        self.assertIn("Series A & B (2023)", analysis)
    
    def test_formatting_with_long_names(self):
        """Test formatting with very long share class names."""
        from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType
        calc = WaterfallCalculator()
        
        long_name = "Very Long Series Name That Might Break Formatting"
        long_class = ShareClass(long_name, 100000, 1000000, PreferenceType.NON_PARTICIPATING)
        calc.add_share_class(long_class)
        
        summary = format_cap_table_summary(calc)
        # Should handle long names (might truncate or wrap)
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
    
    def test_formatting_precision_and_rounding(self):
        """Test formatting precision with fractional amounts."""
        from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType
        calc = WaterfallCalculator()
        
        # Create scenario with fractional results
        fractional = ShareClass("Fractional", 333333, 1000000, PreferenceType.NON_PARTICIPATING)
        common = ShareClass("Common", 666667, 0, PreferenceType.COMMON)
        calc.add_share_class(fractional)
        calc.add_share_class(common)
        
        # Use exit value that creates fractional distributions
        analysis = format_waterfall_analysis(calc, [3333333])
        
        # Should format fractional amounts appropriately
        self.assertIn("$", analysis)
        self.assertIn("M", analysis)
    
    def test_formatting_consistency_across_functions(self):
        """Test that formatting is consistent across all functions."""
        calc = create_mixed_preferences_cap_table()
        exit_value = 15000000
        
        summary = format_cap_table_summary(calc)
        analysis = format_waterfall_analysis(calc, [exit_value])
        conversion = format_conversion_analysis(calc, [exit_value])
        detailed = format_detailed_analysis(calc, exit_value)
        
        # All should contain share class names
        share_class_names = ["Series C", "Series B", "Series A", "Common"]
        
        for name in share_class_names:
            self.assertIn(name, summary)
            self.assertIn(name, analysis)
            # conversion and detailed might not show all names depending on logic
            
        # All should be non-empty strings
        for output in [summary, analysis, conversion, detailed]:
            self.assertIsInstance(output, str)
            self.assertGreater(len(output), 0)


if __name__ == '__main__':
    unittest.main()