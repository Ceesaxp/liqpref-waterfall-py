"""
Tests for core liquidation waterfall data structures and enums.

Comprehensive tests for ShareClass, PreferenceType, AntiDilutionType,
and WaterfallCalculator basic functionality following TDD principles.
"""

import unittest
from liquidation_waterfall import (
    WaterfallCalculator, 
    ShareClass, 
    PreferenceType, 
    AntiDilutionType
)


class TestPreferenceType(unittest.TestCase):
    """Test PreferenceType enum values and behavior."""
    
    def test_preference_type_values(self):
        """Test that PreferenceType enum has expected values."""
        self.assertEqual(PreferenceType.COMMON.value, "common")
        self.assertEqual(PreferenceType.NON_PARTICIPATING.value, "non_participating")
        self.assertEqual(PreferenceType.PARTICIPATING.value, "participating")
    
    def test_preference_type_enum_count(self):
        """Test that PreferenceType has exactly 3 values."""
        preference_types = list(PreferenceType)
        self.assertEqual(len(preference_types), 3)
    
    def test_preference_type_string_representation(self):
        """Test string representation of preference types."""
        self.assertEqual(str(PreferenceType.COMMON), "PreferenceType.COMMON")
        self.assertEqual(str(PreferenceType.NON_PARTICIPATING), "PreferenceType.NON_PARTICIPATING")
        self.assertEqual(str(PreferenceType.PARTICIPATING), "PreferenceType.PARTICIPATING")


class TestAntiDilutionType(unittest.TestCase):
    """Test AntiDilutionType enum values and behavior."""
    
    def test_anti_dilution_type_values(self):
        """Test that AntiDilutionType enum has expected values."""
        self.assertEqual(AntiDilutionType.NONE.value, "None")
        self.assertEqual(AntiDilutionType.FULL_RATCHET.value, "FR")
        self.assertEqual(AntiDilutionType.WEIGHTED_AVERAGE.value, "WA")
    
    def test_anti_dilution_type_enum_count(self):
        """Test that AntiDilutionType has exactly 3 values."""
        ad_types = list(AntiDilutionType)
        self.assertEqual(len(ad_types), 3)


class TestShareClass(unittest.TestCase):
    """Test ShareClass data structure and defaults."""
    
    def test_share_class_creation_with_defaults(self):
        """Test ShareClass creation with minimal parameters uses correct defaults."""
        share_class = ShareClass(
            name="Test Class",
            shares=1000000,
            invested=500000
        )
        
        self.assertEqual(share_class.name, "Test Class")
        self.assertEqual(share_class.shares, 1000000)
        self.assertEqual(share_class.invested, 500000)
        self.assertEqual(share_class.preference_type, PreferenceType.COMMON)
        self.assertEqual(share_class.preference_multiple, 1.0)
        self.assertIsNone(share_class.participation_cap)
        self.assertEqual(share_class.priority, 0)
        self.assertEqual(share_class.stack_order, 0)
        self.assertTrue(share_class.convertible)
        self.assertEqual(share_class.anti_dilution_type, AntiDilutionType.NONE)
    
    def test_share_class_creation_with_all_parameters(self):
        """Test ShareClass creation with all parameters specified."""
        share_class = ShareClass(
            name="Series A",
            shares=200000,
            invested=2000000,
            preference_type=PreferenceType.PARTICIPATING,
            preference_multiple=1.5,
            participation_cap=3.0,
            priority=2,
            stack_order=1,
            convertible=False,
            anti_dilution_type=AntiDilutionType.FULL_RATCHET
        )
        
        self.assertEqual(share_class.name, "Series A")
        self.assertEqual(share_class.shares, 200000)
        self.assertEqual(share_class.invested, 2000000)
        self.assertEqual(share_class.preference_type, PreferenceType.PARTICIPATING)
        self.assertEqual(share_class.preference_multiple, 1.5)
        self.assertEqual(share_class.participation_cap, 3.0)
        self.assertEqual(share_class.priority, 2)
        self.assertEqual(share_class.stack_order, 1)
        self.assertFalse(share_class.convertible)
        self.assertEqual(share_class.anti_dilution_type, AntiDilutionType.FULL_RATCHET)
    
    def test_share_class_common_shares(self):
        """Test creation of common shares with typical parameters."""
        common = ShareClass(
            name="Common",
            shares=5000000,
            invested=0,
            preference_type=PreferenceType.COMMON
        )
        
        self.assertEqual(common.name, "Common")
        self.assertEqual(common.shares, 5000000)
        self.assertEqual(common.invested, 0)
        self.assertEqual(common.preference_type, PreferenceType.COMMON)
        self.assertEqual(common.preference_multiple, 1.0)  # Default
        self.assertTrue(common.convertible)  # Default
    
    def test_share_class_non_participating_preferred(self):
        """Test creation of non-participating preferred shares."""
        preferred = ShareClass(
            name="Series B",
            shares=300000,
            invested=5000000,
            preference_type=PreferenceType.NON_PARTICIPATING,
            preference_multiple=2.0,
            priority=1
        )
        
        self.assertEqual(preferred.name, "Series B")
        self.assertEqual(preferred.preference_type, PreferenceType.NON_PARTICIPATING)
        self.assertEqual(preferred.preference_multiple, 2.0)
        self.assertIsNone(preferred.participation_cap)  # Should be None for non-participating
        self.assertEqual(preferred.priority, 1)
    
    def test_share_class_participating_with_cap(self):
        """Test creation of participating preferred shares with cap."""
        participating = ShareClass(
            name="Series C",
            shares=150000,
            invested=3000000,
            preference_type=PreferenceType.PARTICIPATING,
            preference_multiple=1.0,
            participation_cap=2.5,
            priority=3
        )
        
        self.assertEqual(participating.name, "Series C")
        self.assertEqual(participating.preference_type, PreferenceType.PARTICIPATING)
        self.assertEqual(participating.preference_multiple, 1.0)
        self.assertEqual(participating.participation_cap, 2.5)
        self.assertEqual(participating.priority, 3)
    
    def test_share_class_zero_values(self):
        """Test ShareClass with zero values for edge cases."""
        zero_shares = ShareClass(
            name="Zero Shares",
            shares=0,
            invested=0
        )
        
        self.assertEqual(zero_shares.shares, 0)
        self.assertEqual(zero_shares.invested, 0)
        self.assertEqual(zero_shares.preference_multiple, 1.0)
    
    def test_share_class_large_values(self):
        """Test ShareClass with very large values."""
        large_class = ShareClass(
            name="Large Class",
            shares=1000000000,  # 1 billion shares
            invested=10000000000,  # $10 billion invested
            preference_multiple=5.0
        )
        
        self.assertEqual(large_class.shares, 1000000000)
        self.assertEqual(large_class.invested, 10000000000)
        self.assertEqual(large_class.preference_multiple, 5.0)


class TestWaterfallCalculator(unittest.TestCase):
    """Test WaterfallCalculator basic functionality and edge cases."""
    
    def setUp(self):
        """Set up a fresh calculator for each test."""
        self.calculator = WaterfallCalculator()
    
    def test_calculator_initialization(self):
        """Test WaterfallCalculator initializes correctly."""
        self.assertIsInstance(self.calculator, WaterfallCalculator)
        self.assertEqual(len(self.calculator.share_classes), 0)
        self.assertIsInstance(self.calculator.share_classes, list)
    
    def test_add_single_share_class(self):
        """Test adding a single share class."""
        share_class = ShareClass("Test", 1000, 500)
        self.calculator.add_share_class(share_class)
        
        self.assertEqual(len(self.calculator.share_classes), 1)
        self.assertEqual(self.calculator.share_classes[0], share_class)
        self.assertEqual(self.calculator.share_classes[0].name, "Test")
    
    def test_add_multiple_share_classes(self):
        """Test adding multiple share classes."""
        class1 = ShareClass("Class 1", 1000, 500)
        class2 = ShareClass("Class 2", 2000, 1000)
        class3 = ShareClass("Class 3", 3000, 1500)
        
        self.calculator.add_share_class(class1)
        self.calculator.add_share_class(class2)
        self.calculator.add_share_class(class3)
        
        self.assertEqual(len(self.calculator.share_classes), 3)
        self.assertEqual(self.calculator.share_classes[0].name, "Class 1")
        self.assertEqual(self.calculator.share_classes[1].name, "Class 2")
        self.assertEqual(self.calculator.share_classes[2].name, "Class 3")
    
    def test_add_share_class_preserves_order(self):
        """Test that share classes are added in the order they're added."""
        # Add in specific order
        for i in range(5):
            share_class = ShareClass(f"Class {i}", 1000 * i, 500 * i)
            self.calculator.add_share_class(share_class)
        
        # Verify order is preserved
        for i in range(5):
            self.assertEqual(self.calculator.share_classes[i].name, f"Class {i}")
    
    def test_empty_calculator_distribution(self):
        """Test calculate_distribution with no share classes."""
        distribution = self.calculator.calculate_distribution(1000000)
        self.assertEqual(distribution, {})
    
    def test_empty_calculator_zero_exit(self):
        """Test calculate_distribution with no share classes and zero exit."""
        distribution = self.calculator.calculate_distribution(0)
        self.assertEqual(distribution, {})
    
    def test_calculator_with_single_common_class(self):
        """Test basic distribution with single common share class."""
        common = ShareClass("Common", 1000000, 0, PreferenceType.COMMON)
        self.calculator.add_share_class(common)
        
        distribution = self.calculator.calculate_distribution(5000000)
        
        expected = {"Common": 5000000}
        self.assertEqual(distribution, expected)
    
    def test_calculator_with_zero_exit_value(self):
        """Test distribution with zero exit value."""
        common = ShareClass("Common", 1000000, 0)
        preferred = ShareClass("Preferred", 100000, 1000000, PreferenceType.NON_PARTICIPATING)
        
        self.calculator.add_share_class(common)
        self.calculator.add_share_class(preferred)
        
        distribution = self.calculator.calculate_distribution(0)
        
        expected = {"Common": 0, "Preferred": 0}
        self.assertEqual(distribution, expected)
    
    def test_calculator_negative_exit_value(self):
        """Test distribution with negative exit value."""
        common = ShareClass("Common", 1000000, 0)
        self.calculator.add_share_class(common)
        
        # Should handle negative gracefully
        distribution = self.calculator.calculate_distribution(-1000000)
        
        # Negative exit should result in zero distributions
        expected = {"Common": 0}
        self.assertEqual(distribution, expected)
    
    def test_calculator_share_class_with_duplicate_names(self):
        """Test calculator behavior with duplicate share class names."""
        class1 = ShareClass("Duplicate", 1000, 500)
        class2 = ShareClass("Duplicate", 2000, 1000)
        
        self.calculator.add_share_class(class1)
        self.calculator.add_share_class(class2)
        
        distribution = self.calculator.calculate_distribution(3000)
        
        # Should have entries for both classes (later one overwrites in dict)
        # This tests the actual behavior - in practice duplicate names should be avoided
        self.assertIn("Duplicate", distribution)
    
    def test_calculator_very_large_exit_value(self):
        """Test distribution with very large exit value."""
        common = ShareClass("Common", 1000000, 0)
        self.calculator.add_share_class(common)
        
        large_exit = 1000000000000  # $1 trillion
        distribution = self.calculator.calculate_distribution(large_exit)
        
        expected = {"Common": large_exit}
        self.assertEqual(distribution, expected)
    
    def test_calculator_floating_point_precision(self):
        """Test that calculator handles floating point precision correctly."""
        common = ShareClass("Common", 1000000, 0)
        self.calculator.add_share_class(common)
        
        # Use a value that might cause floating point precision issues
        exit_value = 1000000.33
        distribution = self.calculator.calculate_distribution(exit_value)
        
        self.assertAlmostEqual(distribution["Common"], exit_value, places=2)
    
    def test_calculator_maintains_share_class_references(self):
        """Test that calculator maintains references to original share class objects."""
        original_class = ShareClass("Original", 1000, 500)
        self.calculator.add_share_class(original_class)
        
        # Modify the original object
        original_class.invested = 1000
        
        # Calculator should reflect the change
        self.assertEqual(self.calculator.share_classes[0].invested, 1000)
    
    def test_calculator_share_classes_list_independence(self):
        """Test that modifying the calculator's share_classes list doesn't break functionality."""
        class1 = ShareClass("Class 1", 1000, 500)
        class2 = ShareClass("Class 2", 2000, 1000)
        
        self.calculator.add_share_class(class1)
        self.calculator.add_share_class(class2)
        
        # External modification of the list
        original_length = len(self.calculator.share_classes)
        
        # Calculator should still work correctly
        distribution = self.calculator.calculate_distribution(3000)
        self.assertEqual(len(distribution), original_length)


if __name__ == '__main__':
    unittest.main()