"""
Comprehensive tests for waterfall algorithm scenarios and conversion logic.

Tests complex waterfall scenarios, conversion decisions, priority handling,
and algorithmic edge cases following TDD principles.
"""

import unittest
from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType
from .test_fixtures import (
    create_simple_cap_table,
    create_mixed_preferences_cap_table,
    assert_distribution_totals_exit_value,
    assert_no_negative_distributions,
    assert_liquidation_preference_not_exceeded,
    assert_participation_cap_respected
)


class TestWaterfallAlgorithm(unittest.TestCase):
    """Test complex waterfall algorithm scenarios."""
    
    def test_single_non_participating_conversion_decision(self):
        """Test conversion decision for single non-participating preferred."""
        calc = create_simple_cap_table()
        
        # Series A: 100K shares, $1M invested, 1x non-participating
        # Common: 900K shares
        # Total shares: 1M
        
        # At $5M exit: Series A ownership = 10%
        # Liquidation preference: $1M
        # Pro-rata if converted: 10% * $5M = $500K
        # Should take liquidation preference ($1M > $500K)
        distribution = calc.calculate_distribution(5000000)
        
        self.assertEqual(distribution["Series A"], 1000000)  # Takes LP
        self.assertEqual(distribution["Common"], 4000000)   # Gets remainder
        
        assert_liquidation_preference_not_exceeded(calc, distribution, "Series A")
        assert_distribution_totals_exit_value(distribution, 5000000)
    
    def test_single_non_participating_conversion_to_common(self):
        """Test non-participating preferred converting when pro-rata is better."""
        calc = create_simple_cap_table()
        
        # At $15M exit: Series A ownership = 10%
        # Liquidation preference: $1M  
        # Pro-rata if converted: 10% * $15M = $1.5M
        # Should convert ($1.5M > $1M)
        distribution = calc.calculate_distribution(15000000)
        
        expected_series_a = 15000000 * 0.1  # $1.5M
        expected_common = 15000000 * 0.9    # $13.5M
        
        self.assertAlmostEqual(distribution["Series A"], expected_series_a, delta=1000)
        self.assertAlmostEqual(distribution["Common"], expected_common, delta=1000)
        assert_distribution_totals_exit_value(distribution, 15000000)
    
    def test_participating_never_converts(self):
        """Test that participating preferred never converts to common."""
        calc = WaterfallCalculator()
        
        # Participating preferred that would get more as common (but shouldn't convert)
        participating = ShareClass(
            name="Participating",
            shares=900000,  # 90% ownership
            invested=500000,  # Only $500K invested
            preference_type=PreferenceType.PARTICIPATING,
            preference_multiple=1.0,
            priority=1
        )
        
        common = ShareClass("Common", 100000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(participating)
        calc.add_share_class(common)
        
        # At $10M exit: 
        # If converted: 90% * $10M = $9M
        # As participating: $500K LP + 90% * $9.5M remaining = $500K + $8.55M = $9.05M
        # Participating is better, and they shouldn't convert anyway
        distribution = calc.calculate_distribution(10000000)
        
        # Participating gets LP + participation
        remaining_after_lp = 10000000 - 500000  # $9.5M
        expected_participating = 500000 + (remaining_after_lp * 0.9)  # $500K + $8.55M
        expected_common = remaining_after_lp * 0.1  # $950K
        
        self.assertAlmostEqual(distribution["Participating"], expected_participating, delta=1000)
        self.assertAlmostEqual(distribution["Common"], expected_common, delta=1000)
        assert_distribution_totals_exit_value(distribution, 10000000)
    
    def test_multiple_non_participating_conversion_decisions(self):
        """Test conversion decisions with multiple non-participating preferred."""
        calc = WaterfallCalculator()
        
        # Series A: 10% ownership, $1M invested, 1x LP
        series_a = ShareClass("Series A", 100000, 1000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 2)
        # Series B: 20% ownership, $3M invested, 1x LP  
        series_b = ShareClass("Series B", 200000, 3000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        # Common: 70% ownership
        common = ShareClass("Common", 700000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(series_a)
        calc.add_share_class(series_b)
        calc.add_share_class(common)
        
        # At $20M exit:
        # Series A: LP=$1M vs Pro-rata=10%*$20M=$2M → Should convert
        # Series B: LP=$3M vs Pro-rata=20%*$20M=$4M → Should convert
        # Both convert → all get pro-rata
        distribution = calc.calculate_distribution(20000000)
        
        expected_series_a = 20000000 * 0.1  # $2M
        expected_series_b = 20000000 * 0.2  # $4M  
        expected_common = 20000000 * 0.7    # $14M
        
        self.assertAlmostEqual(distribution["Series A"], expected_series_a, delta=1000)
        self.assertAlmostEqual(distribution["Series B"], expected_series_b, delta=1000)
        self.assertAlmostEqual(distribution["Common"], expected_common, delta=1000)
        assert_distribution_totals_exit_value(distribution, 20000000)
    
    def test_partial_conversion_scenario(self):
        """Test scenario where some preferred convert and others don't."""
        calc = WaterfallCalculator()
        
        # Series A: High investment, low ownership → likely won't convert
        series_a = ShareClass("Series A", 100000, 5000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 2)
        # Series B: Low investment, high ownership → likely will convert
        series_b = ShareClass("Series B", 400000, 1000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        # Common
        common = ShareClass("Common", 500000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(series_a)
        calc.add_share_class(series_b)
        calc.add_share_class(common)
        
        # At $10M exit:
        # Series A: LP=$5M vs Pro-rata=10%*$10M=$1M → Keep LP
        # Series B: LP=$1M vs Pro-rata=40%*$10M=$4M → Convert
        distribution = calc.calculate_distribution(10000000)
        
        # Series A keeps liquidation preference
        self.assertEqual(distribution["Series A"], 5000000)
        
        # Remaining $5M split between Series B (converting) and Common
        # Series B: 400K shares, Common: 500K shares → Total: 900K
        remaining = 5000000
        expected_series_b = remaining * (400000 / 900000)  # ~$2.22M
        expected_common = remaining * (500000 / 900000)    # ~$2.78M
        
        self.assertAlmostEqual(distribution["Series B"], expected_series_b, delta=1000)
        self.assertAlmostEqual(distribution["Common"], expected_common, delta=1000)
        assert_distribution_totals_exit_value(distribution, 10000000)
    
    def test_priority_ordering_basic(self):
        """Test that priority ordering is respected."""
        calc = WaterfallCalculator()
        
        # Higher priority gets paid first
        high_priority = ShareClass("High", 100000, 2000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 2)
        low_priority = ShareClass("Low", 100000, 3000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        common = ShareClass("Common", 800000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(high_priority)
        calc.add_share_class(low_priority)
        calc.add_share_class(common)
        
        # At $3M exit: Only enough for high priority + partial low priority
        distribution = calc.calculate_distribution(3000000)
        
        # High priority gets full $2M
        self.assertEqual(distribution["High"], 2000000)
        # Low priority gets remaining $1M (partial of $3M LP)
        self.assertEqual(distribution["Low"], 1000000)
        # Common gets nothing
        self.assertEqual(distribution["Common"], 0)
        
        assert_distribution_totals_exit_value(distribution, 3000000)
    
    def test_priority_ordering_complex(self):
        """Test complex priority ordering with multiple levels."""
        calc = WaterfallCalculator()
        
        # 3 priority levels
        p3 = ShareClass("Priority 3", 100000, 1000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 3)
        p2 = ShareClass("Priority 2", 100000, 2000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 2)
        p1 = ShareClass("Priority 1", 100000, 3000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        common = ShareClass("Common", 700000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(p3)
        calc.add_share_class(p2)
        calc.add_share_class(p1)
        calc.add_share_class(common)
        
        # At $10M exit: All get full LP + remainder to common
        distribution = calc.calculate_distribution(10000000)
        
        self.assertEqual(distribution["Priority 3"], 1000000)  # Full LP
        self.assertEqual(distribution["Priority 2"], 2000000)  # Full LP
        self.assertEqual(distribution["Priority 1"], 3000000)  # Full LP
        self.assertEqual(distribution["Common"], 4000000)     # Remainder
        
        assert_distribution_totals_exit_value(distribution, 10000000)
    
    def test_insufficient_funds_priority_groups(self):
        """Test insufficient funds distributed by priority."""
        calc = WaterfallCalculator()
        
        # Two classes at different priorities with high LPs
        high = ShareClass("High", 100000, 5000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 2)
        low = ShareClass("Low", 100000, 5000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        
        calc.add_share_class(high)
        calc.add_share_class(low)
        
        # At $3M exit: Not enough for both $5M LPs
        distribution = calc.calculate_distribution(3000000)
        
        # High priority gets full amount
        self.assertEqual(distribution["High"], 3000000)
        # Low priority gets nothing
        self.assertEqual(distribution["Low"], 0)
        
        assert_distribution_totals_exit_value(distribution, 3000000)
    
    def test_mixed_preferences_complex_scenario(self):
        """Test complex scenario with all preference types."""
        calc = create_mixed_preferences_cap_table()
        
        # At $15M exit: Test the full algorithm
        distribution = calc.calculate_distribution(15000000)
        
        # Verify all share classes get something reasonable
        for name, amount in distribution.items():
            self.assertGreaterEqual(amount, 0, f"{name} should not have negative amount")
        
        # Test specific assertions
        assert_distribution_totals_exit_value(distribution, 15000000)
        assert_no_negative_distributions(distribution)
        
        # Series C (highest priority) should get its LP first
        series_c_lp = 3000000 * 1.5  # $4.5M
        self.assertGreaterEqual(distribution["Series C"], series_c_lp * 0.9)  # At least 90% of LP
    
    def test_conversion_decision_edge_case_equal_amounts(self):
        """Test conversion decision when LP equals pro-rata amount."""
        calc = WaterfallCalculator()
        
        # Design scenario where LP exactly equals pro-rata
        # 10% ownership, $1M invested, at $10M exit
        # LP = $1M, Pro-rata = 10% * $10M = $1M
        preferred = ShareClass("Preferred", 100000, 1000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        common = ShareClass("Common", 900000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(preferred)
        calc.add_share_class(common)
        
        distribution = calc.calculate_distribution(10000000)
        
        # When equal, should be indifferent (implementation may choose either)
        # Just verify total is correct
        assert_distribution_totals_exit_value(distribution, 10000000)
        self.assertGreaterEqual(distribution["Preferred"], 1000000 * 0.99)  # At least 99% of LP
    
    def test_zero_liquidation_preference_multiple(self):
        """Test share class with zero liquidation preference multiple."""
        calc = WaterfallCalculator()
        
        zero_lp = ShareClass("Zero LP", 200000, 1000000, PreferenceType.NON_PARTICIPATING, 0.0, None, 1)
        common = ShareClass("Common", 800000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(zero_lp)
        calc.add_share_class(common)
        
        # At $5M exit: Zero LP should convert (gets 20% vs $0 LP)
        distribution = calc.calculate_distribution(5000000)
        
        expected_zero_lp = 5000000 * 0.2  # $1M
        expected_common = 5000000 * 0.8   # $4M
        
        self.assertAlmostEqual(distribution["Zero LP"], expected_zero_lp, delta=1000)
        self.assertAlmostEqual(distribution["Common"], expected_common, delta=1000)
        assert_distribution_totals_exit_value(distribution, 5000000)
    
    def test_very_high_liquidation_preference_multiple(self):
        """Test share class with very high liquidation preference multiple."""
        calc = WaterfallCalculator()
        
        high_lp = ShareClass("High LP", 100000, 1000000, PreferenceType.NON_PARTICIPATING, 10.0, None, 1)
        common = ShareClass("Common", 900000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(high_lp)
        calc.add_share_class(common)
        
        # At $5M exit: High LP = $10M, Pro-rata = 10% * $5M = $500K
        # Should take liquidation preference but capped at exit value
        distribution = calc.calculate_distribution(5000000)
        
        # High LP consumes entire exit value
        self.assertEqual(distribution["High LP"], 5000000)
        self.assertEqual(distribution["Common"], 0)
        
        assert_distribution_totals_exit_value(distribution, 5000000)


class TestConversionLogic(unittest.TestCase):
    """Focused tests on conversion logic and decision making."""
    
    def test_conversion_threshold_detection(self):
        """Test detecting the exact threshold where conversion becomes optimal."""
        calc = create_simple_cap_table()
        
        # Series A: 10% ownership, $1M LP
        # Threshold is at $10M exit (10% * $10M = $1M LP)
        
        # Just below threshold
        distribution_below = calc.calculate_distribution(9999999)
        self.assertEqual(distribution_below["Series A"], 1000000)  # Takes LP
        
        # Just above threshold  
        distribution_above = calc.calculate_distribution(10000001)
        expected_above = 10000001 * 0.1
        self.assertAlmostEqual(distribution_above["Series A"], expected_above, delta=1000)  # Converts
    
    def test_conversion_with_multiple_rounds_stacking(self):
        """Test conversion decisions don't break stacking waterfall."""
        calc = WaterfallCalculator()
        
        # Series B: High priority, might not convert
        series_b = ShareClass("Series B", 100000, 3000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 2)
        # Series A: Low priority, might convert
        series_a = ShareClass("Series A", 200000, 1000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        # Common
        common = ShareClass("Common", 700000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(series_b)
        calc.add_share_class(series_a)
        calc.add_share_class(common)
        
        # At $8M exit:
        # Series B: LP=$3M vs Pro-rata=10%*$8M=$800K → Keep LP  
        # Series A: LP=$1M vs Pro-rata considering Series B took $3M
        # Remaining $5M: Series A gets 20% = $1M, but their LP is also $1M
        # Should be close decision
        distribution = calc.calculate_distribution(8000000)
        
        # Series B should definitely keep LP
        self.assertEqual(distribution["Series B"], 3000000)
        
        # Verify total is correct
        assert_distribution_totals_exit_value(distribution, 8000000)
    
    def test_conversion_decision_independence(self):
        """Test that each class makes independent optimal conversion decisions."""
        calc = WaterfallCalculator()
        
        # Class 1: Clear convert case
        class1 = ShareClass("Convert", 400000, 500000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        # Class 2: Clear don't convert case  
        class2 = ShareClass("Dont Convert", 100000, 3000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        # Common
        common = ShareClass("Common", 500000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(class1)
        calc.add_share_class(class2)
        calc.add_share_class(common)
        
        # At $6M exit:
        # Convert: LP=$500K vs Pro-rata=40%*$6M=$2.4M → Convert
        # Don't Convert: LP=$3M vs Pro-rata=10%*$6M=$600K → Keep LP
        distribution = calc.calculate_distribution(6000000)
        
        # Don't Convert keeps LP
        self.assertEqual(distribution["Dont Convert"], 3000000)
        
        # Remaining $3M split between Convert and Common
        # Convert: 400K shares, Common: 500K shares → Total: 900K
        remaining = 3000000
        expected_convert = remaining * (400000 / 900000)
        expected_common = remaining * (500000 / 900000)
        
        self.assertAlmostEqual(distribution["Convert"], expected_convert, delta=1000)
        self.assertAlmostEqual(distribution["Common"], expected_common, delta=1000)
        assert_distribution_totals_exit_value(distribution, 6000000)


if __name__ == '__main__':
    unittest.main()