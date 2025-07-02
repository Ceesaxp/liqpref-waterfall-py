#!/usr/bin/env python3
"""
Tests for the updated waterfall calculator based on new README requirements
"""

import unittest
from updated_challenge import create_updated_challenge_cap_table


class TestUpdatedWaterfallCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = create_updated_challenge_cap_table()

    def test_cap_table_structure(self):
        """Test that the cap table is created correctly"""
        self.assertEqual(len(self.calculator.share_classes), 10)
        
        # Check that Series E has highest priority
        series_e = next(sc for sc in self.calculator.share_classes if sc.name == "Series E")
        self.assertEqual(series_e.stack_order, 7)
        self.assertEqual(series_e.shares, 1500000)
        self.assertEqual(series_e.invested, 13500000)

    def test_180m_all_convert_scenario(self):
        """Test the $180M scenario where all shares convert to common"""
        distribution = self.calculator.calculate_distribution(180000000)
        
        # Expected values from README (in millions)
        expected = {
            "Series E": 57.2,
            "Series D": 33.1,
            "Series C": 22.9,
            "Series B2": 2.6,
            "Series B1": 6.3,
            "Series A2": 4.1,
            "Series A1": 7.0,
            "Seed": 3.0,
            "Common": 24.8,
            "ESOP/Options": 19.1
        }
        
        for name, expected_millions in expected.items():
            actual_millions = distribution.get(name, 0) / 1000000
            self.assertAlmostEqual(actual_millions, expected_millions, delta=0.1,
                                 msg=f"{name}: expected {expected_millions}M, got {actual_millions}M")

    def test_18m_liquidation_only_scenario(self):
        """Test the $18M scenario where only Series E and D get liquidation preferences"""
        distribution = self.calculator.calculate_distribution(18000000)
        
        # Expected: Series E gets $13.5M, Series D gets $4.5M, others get $0
        self.assertAlmostEqual(distribution.get("Series E", 0), 13500000, delta=1000)
        self.assertAlmostEqual(distribution.get("Series D", 0), 4500000, delta=1000)
        self.assertEqual(distribution.get("Series C", 0), 0)
        self.assertEqual(distribution.get("Common", 0), 0)
        self.assertEqual(distribution.get("ESOP/Options", 0), 0)

    def test_15m_challenge_scenario(self):
        """Test the $15M scenario from the updated challenge"""
        distribution = self.calculator.calculate_distribution(15000000)
        
        # At $15M, only Series E should get its full liquidation preference
        self.assertAlmostEqual(distribution.get("Series E", 0), 13500000, delta=1000)
        self.assertAlmostEqual(distribution.get("Series D", 0), 1500000, delta=1000)
        
        # All others should get $0
        for name in ["Series C", "Series B2", "Series B1", "Series A2", "Series A1", "Seed", "Common", "ESOP/Options"]:
            self.assertEqual(distribution.get(name, 0), 0)

    def test_50m_conversion_scenario(self):
        """Test the $50M scenario - no conversions due to stacking"""
        distribution = self.calculator.calculate_distribution(50000000)
        
        # With corrected logic, Series E should NOT convert at $50M
        # They take their liquidation preference of $13.5M
        series_e_amount = distribution.get("Series E", 0)
        self.assertAlmostEqual(series_e_amount, 13500000, delta=1000)
        
        # Series D gets their full $30.45M
        self.assertAlmostEqual(distribution.get("Series D", 0), 30450000, delta=1000)
        
        # Series C gets the remaining ~$6.05M
        self.assertAlmostEqual(distribution.get("Series C", 0), 6050000, delta=10000)
        
        # Common and ESOP should get $0
        self.assertEqual(distribution.get("Common", 0), 0)
        self.assertEqual(distribution.get("ESOP/Options", 0), 0)

    def test_250m_all_convert_scenario(self):
        """Test the $250M scenario where everyone converts"""
        distribution = self.calculator.calculate_distribution(250000000)
        
        # Everyone should get more than their liquidation preferences
        total_shares = sum(sc.shares for sc in self.calculator.share_classes)
        
        for sc in self.calculator.share_classes:
            if sc.preference_multiple > 0:  # Has liquidation preference
                expected_conversion = 250000000 * (sc.shares / total_shares)
                liquidation_preference = sc.invested * sc.preference_multiple
                
                if expected_conversion > liquidation_preference:
                    # Should convert
                    actual_amount = distribution.get(sc.name, 0)
                    self.assertAlmostEqual(actual_amount, expected_conversion, delta=10000,
                                         msg=f"{sc.name} should convert at $250M")

    def test_total_distribution_equals_exit_value(self):
        """Test that total distribution always equals exit value"""
        test_values = [15000000, 18000000, 50000000, 75000000, 150000000, 180000000, 250000000]
        
        for exit_value in test_values:
            distribution = self.calculator.calculate_distribution(exit_value)
            total_distributed = sum(distribution.values())
            self.assertAlmostEqual(total_distributed, exit_value, delta=1000,
                                 msg=f"Total distribution should equal exit value at ${exit_value}")


if __name__ == '__main__':
    unittest.main()