"""
Enhanced tests for basic waterfall calculator functionality.

Updated to use test fixtures and comprehensive edge cases
following TDD and Tidy First principles.
"""

import unittest
from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType
from .test_fixtures import (
    create_simple_cap_table,
    create_participation_cap_table,
    assert_distribution_totals_exit_value,
    assert_no_negative_distributions
)


class TestWaterfallCalculator(unittest.TestCase):
    """Basic waterfall calculator functionality tests."""
    
    def setUp(self):
        self.calculator = WaterfallCalculator()

    # Basic Initialization Tests
    
    def test_calculator_initialization(self):
        """Test WaterfallCalculator initializes correctly."""
        self.assertIsInstance(self.calculator, WaterfallCalculator)
        self.assertEqual(len(self.calculator.share_classes), 0)

    def test_add_share_class(self):
        """Test adding share classes to calculator."""
        common = ShareClass(
            name="Common",
            shares=1000000,
            invested=0,
            preference_type=PreferenceType.COMMON
        )
        
        self.calculator.add_share_class(common)
        self.assertEqual(len(self.calculator.share_classes), 1)
        self.assertEqual(self.calculator.share_classes[0].name, "Common")

    def test_empty_calculator_returns_empty_distribution(self):
        """Test empty calculator returns empty distribution."""
        distribution = self.calculator.calculate_distribution(5000000)
        self.assertEqual(distribution, {})

    # Basic Distribution Tests
    
    def test_single_common_share_class(self):
        """Test distribution with only common shares."""
        common = ShareClass(
            name="Common",
            shares=1000000,
            invested=0,
            preference_type=PreferenceType.COMMON
        )
        self.calculator.add_share_class(common)

        distribution = self.calculator.calculate_distribution(5000000)
        expected = {"Common": 5000000}
        self.assertEqual(distribution, expected)
        assert_distribution_totals_exit_value(distribution, 5000000)

    def test_non_participating_liquidation_preference(self):
        """Test basic non-participating liquidation preference."""
        calc = create_simple_cap_table()
        
        # At $3M exit: Series A gets $1M LP, Common gets remaining $2M
        distribution = calc.calculate_distribution(3000000)
        
        expected = {"Series A": 1000000, "Common": 2000000}
        self.assertEqual(distribution, expected)
        assert_distribution_totals_exit_value(distribution, 3000000)
        assert_no_negative_distributions(distribution)

    def test_non_participating_conversion_to_common(self):
        """Test non-participating preferred converting to common when advantageous."""
        calc = create_simple_cap_table()
        
        # At $10M exit: Series A (10% ownership) gets 10% = $1M vs $1M LP
        # Should be indifferent, but at $11M gets $1.1M vs $1M LP - should convert
        distribution = calc.calculate_distribution(11000000)
        
        # Series A should convert: 100K / 1M total shares = 10% of $11M = $1.1M
        expected_series_a = 11000000 * 0.1  # $1.1M
        expected_common = 11000000 * 0.9    # $9.9M
        
        self.assertAlmostEqual(distribution["Series A"], expected_series_a, delta=1000)
        self.assertAlmostEqual(distribution["Common"], expected_common, delta=1000)
        assert_distribution_totals_exit_value(distribution, 11000000)

    def test_participating_basic_distribution(self):
        """Test basic participating preference distribution."""
        calc = create_participation_cap_table()
        
        # At $6M exit:
        # Series A: $2M LP + participation in remaining $3M
        # Series B: $1M LP + participation in remaining $3M  
        # Common: participation in remaining $3M only
        # Total shares: 200K + 100K + 700K = 1M
        
        distribution = calc.calculate_distribution(6000000)
        
        remaining_after_lp = 6000000 - 2000000 - 1000000  # $3M
        
        # Series A: $2M LP + (200K/1M) * $3M = $2M + $600K = $2.6M
        expected_series_a = 2000000 + (remaining_after_lp * 0.2)
        # Series B: $1M LP + (100K/1M) * $3M = $1M + $300K = $1.3M  
        expected_series_b = 1000000 + (remaining_after_lp * 0.1)
        # Common: (700K/1M) * $3M = $2.1M
        expected_common = remaining_after_lp * 0.7
        
        self.assertAlmostEqual(distribution["Series A"], expected_series_a, delta=1000)
        self.assertAlmostEqual(distribution["Series B"], expected_series_b, delta=1000)
        self.assertAlmostEqual(distribution["Common"], expected_common, delta=1000)
        assert_distribution_totals_exit_value(distribution, 6000000)

    def test_participating_with_cap_applied(self):
        """Test participating preference with cap limitation."""
        calc = create_participation_cap_table()
        
        # At $20M exit: Series A should hit 2x cap = $4M max
        distribution = calc.calculate_distribution(20000000)
        
        # Series A capped at $4M (2x * $2M investment)
        self.assertAlmostEqual(distribution["Series A"], 4000000, delta=1000)
        
        # Series B uncapped, gets $1M LP + participation
        # Common gets participation
        # Remaining after Series A cap and Series B LP: $20M - $4M - $1M = $15M
        # Series B and Common split this: 100K + 700K = 800K shares
        remaining_for_participation = 20000000 - 4000000 - 1000000  # $15M
        
        expected_series_b = 1000000 + (remaining_for_participation * 0.125)  # 100K/800K
        expected_common = remaining_for_participation * 0.875  # 700K/800K
        
        self.assertAlmostEqual(distribution["Series B"], expected_series_b, delta=1000)
        self.assertAlmostEqual(distribution["Common"], expected_common, delta=1000)
        assert_distribution_totals_exit_value(distribution, 20000000)

    # Edge Cases
    
    def test_zero_exit_value(self):
        """Test behavior with zero exit value."""
        calc = create_simple_cap_table()
        distribution = calc.calculate_distribution(0)
        
        expected = {"Series A": 0, "Common": 0}
        self.assertEqual(distribution, expected)

    def test_very_small_exit_value(self):
        """Test behavior with exit value smaller than liquidation preferences."""
        calc = create_simple_cap_table()
        
        # $500K exit, but Series A has $1M liquidation preference
        distribution = calc.calculate_distribution(500000)
        
        # Series A should get the full $500K, Common gets nothing
        expected = {"Series A": 500000, "Common": 0}
        self.assertEqual(distribution, expected)
        assert_distribution_totals_exit_value(distribution, 500000)

    def test_exit_value_exactly_equals_liquidation_preference(self):
        """Test when exit value exactly equals liquidation preference."""
        calc = create_simple_cap_table()
        
        # $1M exit exactly equals Series A liquidation preference
        distribution = calc.calculate_distribution(1000000)
        
        expected = {"Series A": 1000000, "Common": 0}
        self.assertEqual(distribution, expected)
        assert_distribution_totals_exit_value(distribution, 1000000)

    def test_very_large_exit_value(self):
        """Test behavior with very large exit values."""
        calc = create_simple_cap_table()
        
        # $1B exit - should convert to pro-rata
        distribution = calc.calculate_distribution(1000000000)
        
        # Series A: 10% of $1B = $100M
        # Common: 90% of $1B = $900M
        self.assertAlmostEqual(distribution["Series A"], 100000000, delta=10000)
        self.assertAlmostEqual(distribution["Common"], 900000000, delta=10000)
        assert_distribution_totals_exit_value(distribution, 1000000000)

    def test_multiple_share_classes_same_preference_type(self):
        """Test multiple share classes with same preference type."""
        calc = WaterfallCalculator()
        
        # Two non-participating preferred at same priority
        series_a = ShareClass("Series A", 100000, 1000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        series_b = ShareClass("Series B", 200000, 2000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        common = ShareClass("Common", 700000, 0, PreferenceType.COMMON, priority=0)
        
        calc.add_share_class(series_a)
        calc.add_share_class(series_b)
        calc.add_share_class(common)
        
        # At $5M exit: Both should get their full LP, remaining goes to common
        distribution = calc.calculate_distribution(5000000)
        
        expected = {
            "Series A": 1000000,
            "Series B": 2000000, 
            "Common": 2000000
        }
        self.assertEqual(distribution, expected)
        assert_distribution_totals_exit_value(distribution, 5000000)


if __name__ == '__main__':
    unittest.main()