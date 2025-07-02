"""
Comprehensive tests for participation cap logic and iterative application.

Tests participation caps, iterative cap application algorithm,
and edge cases for capped participating preferred shares.
"""

import unittest
from liquidation_waterfall import WaterfallCalculator, ShareClass, PreferenceType
from .test_fixtures import (
    create_participation_cap_table,
    assert_distribution_totals_exit_value,
    assert_no_negative_distributions,
    assert_participation_cap_respected
)


class TestParticipationCaps(unittest.TestCase):
    """Test participation cap application and edge cases."""
    
    def test_participation_cap_reached(self):
        """Test participating preferred hitting their cap."""
        calc = create_participation_cap_table()
        
        # Series A: $2M invested with 2x cap = $4M max
        # At high exit, should be capped
        distribution = calc.calculate_distribution(20000000)
        
        # Series A should be capped at $4M
        self.assertAlmostEqual(distribution["Series A"], 4000000, delta=1000)
        assert_participation_cap_respected(calc, distribution, "Series A")
        assert_distribution_totals_exit_value(distribution, 20000000)
    
    def test_participation_cap_not_reached(self):
        """Test participating preferred not hitting their cap."""
        calc = create_participation_cap_table()
        
        # At lower exit, cap shouldn't be reached
        distribution = calc.calculate_distribution(5000000)
        
        # Series A: $2M LP + participation
        # Remaining after LPs: $5M - $2M - $1M = $2M
        # Series A participation: (200K/1M) * $2M = $400K
        # Total: $2M + $400K = $2.4M (under $4M cap)
        expected_series_a = 2000000 + (2000000 * 0.2)  # $2.4M
        
        self.assertAlmostEqual(distribution["Series A"], expected_series_a, delta=1000)
        self.assertLess(distribution["Series A"], 4000000)  # Under cap
        assert_participation_cap_respected(calc, distribution, "Series A")
        assert_distribution_totals_exit_value(distribution, 5000000)
    
    def test_multiple_capped_participants(self):
        """Test multiple participating preferred shares with caps."""
        calc = WaterfallCalculator()
        
        # Multiple participating shares with different caps
        series_a = ShareClass("Series A", 200000, 2000000, PreferenceType.PARTICIPATING, 1.0, 2.0, 2)  # 2x cap
        series_b = ShareClass("Series B", 200000, 3000000, PreferenceType.PARTICIPATING, 1.0, 1.5, 1)  # 1.5x cap
        common = ShareClass("Common", 600000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(series_a)
        calc.add_share_class(series_b)
        calc.add_share_class(common)
        
        # At $20M exit: Both should hit caps
        distribution = calc.calculate_distribution(20000000)
        
        # Series A cap: $2M * 2.0 = $4M
        # Series B cap: $3M * 1.5 = $4.5M
        self.assertAlmostEqual(distribution["Series A"], 4000000, delta=1000)
        self.assertAlmostEqual(distribution["Series B"], 4500000, delta=1000)
        
        # Remaining: $20M - $4M - $4.5M = $11.5M goes to common
        self.assertAlmostEqual(distribution["Common"], 11500000, delta=1000)
        
        assert_participation_cap_respected(calc, distribution, "Series A")
        assert_participation_cap_respected(calc, distribution, "Series B")
        assert_distribution_totals_exit_value(distribution, 20000000)
    
    def test_iterative_cap_application(self):
        """Test iterative cap application algorithm."""
        calc = WaterfallCalculator()
        
        # Scenario where caps are hit in multiple rounds
        capped_early = ShareClass("Early Cap", 100000, 1000000, PreferenceType.PARTICIPATING, 1.0, 1.5, 1)  # $1.5M cap
        capped_late = ShareClass("Late Cap", 200000, 2000000, PreferenceType.PARTICIPATING, 1.0, 3.0, 1)   # $6M cap
        common = ShareClass("Common", 700000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(capped_early)
        calc.add_share_class(capped_late)
        calc.add_share_class(common)
        
        # At $10M exit:
        # Round 1: LPs paid - Early: $1M, Late: $2M, remaining: $7M
        # Round 2: Participation distributed - Early hits cap first
        distribution = calc.calculate_distribution(10000000)
        
        # Early Cap should hit $1.5M cap
        self.assertAlmostEqual(distribution["Early Cap"], 1500000, delta=1000)
        
        # After Early Cap hits cap, remaining distributed to Late Cap and Common
        # Late Cap and Common continue participating
        assert_participation_cap_respected(calc, distribution, "Early Cap")
        assert_participation_cap_respected(calc, distribution, "Late Cap")
        assert_distribution_totals_exit_value(distribution, 10000000)
    
    def test_cap_exactly_reached(self):
        """Test edge case where cap is exactly reached."""
        calc = WaterfallCalculator()
        
        # Design scenario where cap is exactly hit
        participating = ShareClass("Exact Cap", 200000, 2000000, PreferenceType.PARTICIPATING, 1.0, 2.0, 1)
        common = ShareClass("Common", 800000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(participating)
        calc.add_share_class(common)
        
        # Calculate exit value where cap is exactly reached
        # LP: $2M, remaining for participation: $X
        # Participating share: 20%, so gets 20% * $X
        # Total: $2M + 20% * $X = $4M (2x cap)
        # Solving: 20% * $X = $2M → $X = $10M → Total exit = $12M
        distribution = calc.calculate_distribution(12000000)
        
        # Should get exactly $4M (2x cap)
        self.assertAlmostEqual(distribution["Exact Cap"], 4000000, delta=1000)
        self.assertAlmostEqual(distribution["Common"], 8000000, delta=1000)
        
        assert_participation_cap_respected(calc, distribution, "Exact Cap")
        assert_distribution_totals_exit_value(distribution, 12000000)
    
    def test_uncapped_participating_with_capped_participating(self):
        """Test mix of capped and uncapped participating shares."""
        calc = WaterfallCalculator()
        
        capped = ShareClass("Capped", 200000, 2000000, PreferenceType.PARTICIPATING, 1.0, 2.0, 1)    # 2x cap
        uncapped = ShareClass("Uncapped", 200000, 1000000, PreferenceType.PARTICIPATING, 1.0, None, 1)  # No cap
        common = ShareClass("Common", 600000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(capped)
        calc.add_share_class(uncapped)
        calc.add_share_class(common)
        
        # At $20M exit: Capped hits $4M, uncapped continues participating
        distribution = calc.calculate_distribution(20000000)
        
        # Capped at $4M
        self.assertAlmostEqual(distribution["Capped"], 4000000, delta=1000)
        
        # After cap hit, remaining distributed to uncapped and common
        # Uncapped should get more than its LP due to continued participation
        self.assertGreater(distribution["Uncapped"], 1000000)  # More than $1M LP
        
        assert_participation_cap_respected(calc, distribution, "Capped")
        assert_distribution_totals_exit_value(distribution, 20000000)
    
    def test_cap_lower_than_liquidation_preference(self):
        """Test edge case where cap is lower than liquidation preference."""
        calc = WaterfallCalculator()
        
        # Cap lower than LP (unusual but possible)
        weird_cap = ShareClass("Weird", 100000, 2000000, PreferenceType.PARTICIPATING, 1.0, 0.5, 1)  # 0.5x cap = $1M
        common = ShareClass("Common", 900000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(weird_cap)
        calc.add_share_class(common)
        
        # At any exit, should be capped at $1M (less than $2M LP)
        distribution = calc.calculate_distribution(10000000)
        
        # Should get cap amount, not liquidation preference
        self.assertAlmostEqual(distribution["Weird"], 1000000, delta=1000)  # $1M cap, not $2M LP
        self.assertAlmostEqual(distribution["Common"], 9000000, delta=1000)
        
        assert_participation_cap_respected(calc, distribution, "Weird")
        assert_distribution_totals_exit_value(distribution, 10000000)
    
    def test_zero_cap_behavior(self):
        """Test behavior with zero cap (should mean no cap)."""
        calc = WaterfallCalculator()
        
        # Zero cap should mean uncapped
        zero_cap = ShareClass("Zero Cap", 200000, 1000000, PreferenceType.PARTICIPATING, 1.0, 0, 1)
        common = ShareClass("Common", 800000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(zero_cap)
        calc.add_share_class(common)
        
        # At high exit, should get full participation (no cap applied)
        distribution = calc.calculate_distribution(20000000)
        
        # Should get LP + full pro-rata participation
        remaining_after_lp = 19000000  # $20M - $1M LP
        expected_zero_cap = 1000000 + (remaining_after_lp * 0.2)  # LP + 20% participation
        expected_common = remaining_after_lp * 0.8
        
        self.assertAlmostEqual(distribution["Zero Cap"], expected_zero_cap, delta=1000)
        self.assertAlmostEqual(distribution["Common"], expected_common, delta=1000)
        assert_distribution_totals_exit_value(distribution, 20000000)
    
    def test_cap_application_order_independence(self):
        """Test that cap application doesn't depend on share class order."""
        # Test with different orders of the same share classes
        orders = [
            ["A", "B", "C"],
            ["C", "A", "B"], 
            ["B", "C", "A"]
        ]
        
        distributions = []
        
        for order in orders:
            calc = WaterfallCalculator()
            
            classes = {
                "A": ShareClass("A", 200000, 1000000, PreferenceType.PARTICIPATING, 1.0, 2.0, 1),
                "B": ShareClass("B", 200000, 2000000, PreferenceType.PARTICIPATING, 1.0, 1.5, 1),
                "C": ShareClass("Common", 600000, 0, PreferenceType.COMMON)
            }
            
            # Add in specified order
            for name in order:
                calc.add_share_class(classes[name])
            
            distribution = calc.calculate_distribution(15000000)
            distributions.append(distribution)
        
        # All distributions should be identical regardless of order
        for i in range(1, len(distributions)):
            for name in ["A", "B", "Common"]:
                self.assertAlmostEqual(
                    distributions[0][name], 
                    distributions[i][name], 
                    delta=1000,
                    msg=f"Distribution for {name} differs with order {orders[i]}"
                )


class TestParticipationCapEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for participation caps."""
    
    def test_single_capped_participant_with_common(self):
        """Test simple case with one capped participant and common."""
        calc = WaterfallCalculator()
        
        capped = ShareClass("Capped", 250000, 2000000, PreferenceType.PARTICIPATING, 1.0, 2.0, 1)  # $4M cap
        common = ShareClass("Common", 750000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(capped)
        calc.add_share_class(common)
        
        # Test multiple exit values
        exit_values = [3000000, 6000000, 10000000, 20000000]
        
        for exit_value in exit_values:
            distribution = calc.calculate_distribution(exit_value)
            
            # Should never exceed cap
            self.assertLessEqual(distribution["Capped"], 4000000 * 1.01)  # Small tolerance
            assert_participation_cap_respected(calc, distribution, "Capped")
            assert_distribution_totals_exit_value(distribution, exit_value)
    
    def test_all_participants_capped_scenario(self):
        """Test scenario where all participating shares hit their caps."""
        calc = WaterfallCalculator()
        
        # All participants with low caps
        p1 = ShareClass("P1", 200000, 1000000, PreferenceType.PARTICIPATING, 1.0, 1.2, 1)  # $1.2M cap
        p2 = ShareClass("P2", 200000, 2000000, PreferenceType.PARTICIPATING, 1.0, 1.5, 1)  # $3M cap
        common = ShareClass("Common", 600000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(p1)
        calc.add_share_class(p2)
        calc.add_share_class(common)
        
        # High exit where all hit caps
        distribution = calc.calculate_distribution(50000000)
        
        # All should be at their caps
        self.assertAlmostEqual(distribution["P1"], 1200000, delta=1000)   # $1.2M cap
        self.assertAlmostEqual(distribution["P2"], 3000000, delta=1000)   # $3M cap
        
        # Common gets the rest
        expected_common = 50000000 - 1200000 - 3000000
        self.assertAlmostEqual(distribution["Common"], expected_common, delta=1000)
        
        assert_participation_cap_respected(calc, distribution, "P1")
        assert_participation_cap_respected(calc, distribution, "P2")
        assert_distribution_totals_exit_value(distribution, 50000000)
    
    def test_participating_cap_with_non_participating_shares(self):
        """Test capped participating shares with non-participating shares present."""
        calc = WaterfallCalculator()
        
        # Mix of share types
        non_part = ShareClass("Non Part", 100000, 3000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 2)
        part_capped = ShareClass("Part Capped", 200000, 2000000, PreferenceType.PARTICIPATING, 1.0, 2.0, 1)
        common = ShareClass("Common", 700000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(non_part)
        calc.add_share_class(part_capped)
        calc.add_share_class(common)
        
        # At $15M exit: Non-part takes LP, part-capped participates with cap
        distribution = calc.calculate_distribution(15000000)
        
        # Non-participating should get its LP or convert
        self.assertGreaterEqual(distribution["Non Part"], 3000000 * 0.9)  # At least 90% of LP
        
        # Participating should respect cap
        assert_participation_cap_respected(calc, distribution, "Part Capped")
        assert_distribution_totals_exit_value(distribution, 15000000)
    
    def test_fractional_cap_multiples(self):
        """Test caps with fractional multiples."""
        calc = WaterfallCalculator()
        
        # Fractional cap multiple
        fractional = ShareClass("Fractional", 300000, 2000000, PreferenceType.PARTICIPATING, 1.0, 1.25, 1)  # 1.25x cap
        common = ShareClass("Common", 700000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(fractional)
        calc.add_share_class(common)
        
        # At high exit
        distribution = calc.calculate_distribution(20000000)
        
        # Should be capped at $2M * 1.25 = $2.5M
        self.assertAlmostEqual(distribution["Fractional"], 2500000, delta=1000)
        self.assertAlmostEqual(distribution["Common"], 17500000, delta=1000)
        
        assert_participation_cap_respected(calc, distribution, "Fractional")
        assert_distribution_totals_exit_value(distribution, 20000000)
    
    def test_very_high_cap_effectively_uncapped(self):
        """Test very high cap that's effectively uncapped."""
        calc = WaterfallCalculator()
        
        # Very high cap that won't be reached
        high_cap = ShareClass("High Cap", 200000, 1000000, PreferenceType.PARTICIPATING, 1.0, 100.0, 1)  # 100x cap
        common = ShareClass("Common", 800000, 0, PreferenceType.COMMON)
        
        calc.add_share_class(high_cap)
        calc.add_share_class(common)
        
        # Even at high exit, shouldn't hit cap
        distribution = calc.calculate_distribution(50000000)
        
        # Should get full participation without hitting $100M cap
        remaining_after_lp = 49000000  # $50M - $1M LP
        expected_high_cap = 1000000 + (remaining_after_lp * 0.2)  # LP + 20% participation
        
        self.assertAlmostEqual(distribution["High Cap"], expected_high_cap, delta=1000)
        self.assertLess(distribution["High Cap"], 100000000)  # Well under cap
        
        assert_participation_cap_respected(calc, distribution, "High Cap")
        assert_distribution_totals_exit_value(distribution, 50000000)


if __name__ == '__main__':
    unittest.main()