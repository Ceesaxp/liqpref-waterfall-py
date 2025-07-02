#!/usr/bin/env python3
"""
Test suite for priority groups with different multiples within same stack order
"""

import unittest
from waterfall import WaterfallCalculator, ShareClass, PreferenceType


class TestPriorityGroups(unittest.TestCase):
    def setUp(self):
        """Set up test scenario with multiple shareholders at same priority level"""
        self.calculator = WaterfallCalculator()
        
        # Series B shareholders (all at priority 2, different multiples)
        self.sh1 = ShareClass(
            name="B: Shareholder 1",
            shares=1000000,
            invested=10000000,
            preference_type=PreferenceType.NON_PARTICIPATING,
            preference_multiple=2.0,
            priority=2
        )
        
        self.sh2 = ShareClass(
            name="B: Shareholder 2", 
            shares=500000,
            invested=5000000,
            preference_type=PreferenceType.NON_PARTICIPATING,
            preference_multiple=1.5,
            priority=2
        )
        
        self.sh3 = ShareClass(
            name="B: Shareholder 3",
            shares=500000, 
            invested=5000000,
            preference_type=PreferenceType.NON_PARTICIPATING,
            preference_multiple=1.25,
            priority=2
        )
        
        # Add a lower priority class
        self.common = ShareClass(
            name="Common",
            shares=1000000,
            invested=0,
            preference_type=PreferenceType.COMMON,
            priority=0
        )
        
        self.calculator.add_share_class(self.sh1)
        self.calculator.add_share_class(self.sh2)
        self.calculator.add_share_class(self.sh3)
        self.calculator.add_share_class(self.common)

    def test_pro_rata_within_priority_insufficient_funds(self):
        """Test pro-rata distribution when insufficient funds for full liquidation preferences"""
        # Total LP: 20M + 7.5M + 6.25M = 33.75M
        # Exit: $20M - not enough for all LPs
        
        distribution = self.calculator.calculate_distribution(20000000)
        
        # Expected pro-rata within Series B level
        total_lp = (10000000 * 2.0) + (5000000 * 1.5) + (5000000 * 1.25)  # 33.75M
        
        expected_sh1 = 20000000 * (20000000 / total_lp)  # ~11.85M
        expected_sh2 = 20000000 * (7500000 / total_lp)   # ~4.44M
        expected_sh3 = 20000000 * (6250000 / total_lp)   # ~3.70M
        
        self.assertAlmostEqual(distribution["B: Shareholder 1"], expected_sh1, delta=1000)
        self.assertAlmostEqual(distribution["B: Shareholder 2"], expected_sh2, delta=1000)
        self.assertAlmostEqual(distribution["B: Shareholder 3"], expected_sh3, delta=1000)
        self.assertEqual(distribution["Common"], 0)  # Nothing left for common

    def test_full_liquidation_preferences_paid(self):
        """Test when there's enough money to pay all liquidation preferences"""
        # Exit value higher than total LPs
        distribution = self.calculator.calculate_distribution(40000000)
        
        # All should get their full liquidation preferences
        self.assertAlmostEqual(distribution["B: Shareholder 1"], 20000000, delta=1000)  # 10M * 2.0
        self.assertAlmostEqual(distribution["B: Shareholder 2"], 7500000, delta=1000)   # 5M * 1.5
        self.assertAlmostEqual(distribution["B: Shareholder 3"], 6250000, delta=1000)   # 5M * 1.25
        
        # Remaining 6.25M should go to common
        self.assertAlmostEqual(distribution["Common"], 6250000, delta=1000)

    def test_mixed_priority_levels(self):
        """Test with shareholders at different priority levels"""
        # Add Series A at higher priority
        series_a = ShareClass(
            name="A: Investor",
            shares=200000,
            invested=2000000,
            preference_type=PreferenceType.NON_PARTICIPATING,
            preference_multiple=2.0,
            priority=3
        )
        self.calculator.add_share_class(series_a)
        
        # At $25M: Series A gets 4M, Series B gets pro-rated share of remaining 21M
        distribution = self.calculator.calculate_distribution(25000000)
        
        # Series A should get full preference first
        self.assertAlmostEqual(distribution["A: Investor"], 4000000, delta=1000)
        
        # Series B should get pro-rated from remaining $21M
        remaining = 21000000
        total_lp_b = 33750000  # Total LP for Series B
        
        expected_sh1 = remaining * (20000000 / total_lp_b)
        expected_sh2 = remaining * (7500000 / total_lp_b)
        expected_sh3 = remaining * (6250000 / total_lp_b)
        
        self.assertAlmostEqual(distribution["B: Shareholder 1"], expected_sh1, delta=1000)
        self.assertAlmostEqual(distribution["B: Shareholder 2"], expected_sh2, delta=1000)
        self.assertAlmostEqual(distribution["B: Shareholder 3"], expected_sh3, delta=1000)

    def test_total_distribution_equals_exit_value(self):
        """Ensure total distribution always equals exit value"""
        test_values = [10000000, 20000000, 33750000, 40000000, 50000000]
        
        for exit_value in test_values:
            distribution = self.calculator.calculate_distribution(exit_value)
            total = sum(distribution.values())
            self.assertAlmostEqual(total, exit_value, delta=1000,
                                 msg=f"Total should equal exit value at ${exit_value}")

    def test_sbda_csv_scenario(self):
        """Test the actual sbda.csv scenario"""
        from csv_waterfall import parse_cap_table
        
        # Parse sbda.csv
        calc = parse_cap_table('sbda.csv')
        
        # Test $20M scenario - should only pay Series B level
        distribution = calc.calculate_distribution(20000000)
        
        # All Series B should get something, others should get 0
        series_b_total = 0
        for name, amount in distribution.items():
            if name.startswith('B:'):
                series_b_total += amount
                self.assertGreater(amount, 0, f"{name} should get something")
            elif name.startswith('A:') or name.startswith('Comm:') or name == 'Options':
                self.assertEqual(amount, 0, f"{name} should get nothing at $20M")
        
        # Series B should get the full $20M
        self.assertAlmostEqual(series_b_total, 20000000, delta=1000)


if __name__ == '__main__':
    unittest.main()