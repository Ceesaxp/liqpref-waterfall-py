import unittest
from waterfall import WaterfallCalculator, ShareClass, PreferenceType


class TestWaterfallCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = WaterfallCalculator()

    def test_calculator_initialization(self):
        self.assertIsInstance(self.calculator, WaterfallCalculator)

    def test_add_common_shares(self):
        common = ShareClass(
            name="Common",
            shares=1000000,
            invested=0,
            preference_type=PreferenceType.COMMON
        )
        self.calculator.add_share_class(common)
        self.assertEqual(len(self.calculator.share_classes), 1)
        self.assertEqual(self.calculator.share_classes[0].name, "Common")

    def test_add_preferred_shares(self):
        preferred_a = ShareClass(
            name="Preferred A",
            shares=200000,
            invested=900000,
            preference_type=PreferenceType.PARTICIPATING,
            preference_multiple=1.0,
            participation_cap=2.0,
            priority=1
        )
        self.calculator.add_share_class(preferred_a)
        self.assertEqual(len(self.calculator.share_classes), 1)
        self.assertEqual(self.calculator.share_classes[0].invested, 900000)

    def test_simple_all_common_distribution(self):
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

    def test_non_participating_liquidation_preference(self):
        # Common: 1M shares, Preferred A: 200K shares, $900K invested, 1x non-participating
        common = ShareClass("Common", 1000000, 0, PreferenceType.COMMON)
        preferred_a = ShareClass(
            "Preferred A", 200000, 900000,
            PreferenceType.NON_PARTICIPATING, 1.0, None, 1 # pyright: ignore
        )

        self.calculator.add_share_class(common)
        self.calculator.add_share_class(preferred_a)

        # At $3M exit: Preferred A gets $900K, Common gets remaining $2.1M
        distribution = self.calculator.calculate_distribution(3000000)
        expected = {"Common": 2100000, "Preferred A": 900000}
        self.assertEqual(distribution, expected)

    def test_participating_liquidation_preference_basic(self):
        # Test basic participating preference from the challenge example
        # Common: 1M shares (33.33%), Preferred C: 1.5M shares, $15M invested (50%)
        # At $25M exit: Preferred C gets $15M + pro-rata share of remaining $10M
        common = ShareClass("Common", 1000000, 0, PreferenceType.COMMON)
        preferred_c = ShareClass(
            "Preferred C", 1500000, 15000000,
            PreferenceType.PARTICIPATING, 1.0, 2.0, 3
        )

        self.calculator.add_share_class(common)
        self.calculator.add_share_class(preferred_c)

        # At $25M: Preferred C gets $15M liquidation + 60% of remaining $10M = $15M + $6M = $21M
        # Common gets 40% of remaining $10M = $4M
        distribution = self.calculator.calculate_distribution(25000000)
        expected = {"Common": 4000000, "Preferred C": 21000000}
        self.assertEqual(distribution, expected)

    def test_participating_with_cap(self):
        # Test the 2x cap scenario from the challenge
        # Common: 1M shares, Preferred A: 200K shares, $900K invested, 1x participating with 2x cap
        # At higher exit values, Preferred A should be capped at 2x = $1.8M
        common = ShareClass("Common", 1000000, 0, PreferenceType.COMMON)
        preferred_a = ShareClass(
            "Preferred A", 200000, 900000,
            PreferenceType.PARTICIPATING, 1.0, 2.0, 1
        )

        self.calculator.add_share_class(common)
        self.calculator.add_share_class(preferred_a)

        # At $6M exit: Preferred A would get $900K + (200K/1.2M) * $5.1M = $900K + $850K = $1.75M (no cap)
        # At $7M exit: Preferred A would get $900K + (200K/1.2M) * $6.1M = $900K + $1.017M = $1.917M
        # This exceeds 2x cap of $1.8M, so Preferred A gets capped at $1.8M
        distribution = self.calculator.calculate_distribution(7000000)
        expected = {"Common": 5200000, "Preferred A": 1800000}
        self.assertEqual(distribution, expected)

    def test_conversion_to_common(self):
        # Test conversion decision from the challenge example
        # At high exit values, preferred shares might get more by converting to common
        # Example: investor with 20% ownership, $1M invested, 1x non-participating
        # At $6M exit: liquidation preference = $1M, conversion = 20% * $6M = $1.2M
        common = ShareClass("Common", 800000, 0, PreferenceType.COMMON)  # 80%
        preferred_a = ShareClass(
            "Preferred A", 200000, 1000000,  # 20%
            PreferenceType.NON_PARTICIPATING, 1.0, None, 1 # pyright: ignore
        )

        self.calculator.add_share_class(common)
        self.calculator.add_share_class(preferred_a)

        # At $6M exit: Preferred A should convert to common to get 20% = $1.2M instead of $1M
        distribution = self.calculator.calculate_distribution(6000000)
        expected = {"Common": 4800000, "Preferred A": 1200000}  # Both get pro-rata as common
        self.assertEqual(distribution, expected)

    def test_full_challenge_example_25m(self):
        # Test the full challenge example at $25M exit
        # From README: Common (1M), Preferred A (200K, $900K), Preferred B (300K, $2.1M), Preferred C (1.5M, $15M)
        common = ShareClass("Common", 1000000, 0, PreferenceType.COMMON)
        preferred_a = ShareClass("Preferred A", 200000, 900000, PreferenceType.PARTICIPATING, 1.0, 2.0, 1)
        preferred_b = ShareClass("Preferred B", 300000, 2100000, PreferenceType.PARTICIPATING, 1.0, 2.0, 2)
        preferred_c = ShareClass("Preferred C", 1500000, 15000000, PreferenceType.PARTICIPATING, 1.0, 2.0, 3)

        self.calculator.add_share_class(common)
        self.calculator.add_share_class(preferred_a)
        self.calculator.add_share_class(preferred_b)
        self.calculator.add_share_class(preferred_c)

        # From the challenge: At $25M exit
        # - Founders: $2.33m (33.33% of $7m remaining)
        # - Series A: $0.9m + $0.47m = $1.37m (6.67% of $7m)
        # - Series B: $2.1m + $0.7m = $2.8m (10% of $7m)
        # - Series C: $15m + $3.5m = $18.5m (50% of $7m)
        distribution = self.calculator.calculate_distribution(25000000)

        # Expected values from the challenge description
        expected = {
            "Common": 2330000,         # 33.33% of $7M remaining
            "Preferred A": 1370000,    # $900K + 6.67% of $7M
            "Preferred B": 2800000,    # $2.1M + 10% of $7M
            "Preferred C": 18500000    # $15M + 50% of $7M
        }

        # Allow for small rounding differences
        for name, expected_amount in expected.items():
            self.assertAlmostEqual(distribution[name], expected_amount, delta=10000)


if __name__ == '__main__':
    unittest.main()
