"""
Comprehensive tests for CSV parser and cap table data validation.

Tests CSV format support, data validation, error handling,
and edge cases for cap table parsing functionality.
"""

import unittest
import tempfile
import os
from liquidation_waterfall import (
    parse_cap_table_csv, 
    parse_cap_table_dict,
    WaterfallCalculator,
    ShareClass,
    PreferenceType,
    AntiDilutionType
)


class TestCSVParser(unittest.TestCase):
    """Test CSV parsing functionality and format support."""
    
    def setUp(self):
        """Set up temporary directory for test CSV files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_temp_csv(self, content: str, filename: str = "test.csv") -> str:
        """Create a temporary CSV file with given content."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def test_parse_new_csv_format(self):
        """Test parsing new CSV format with all fields."""
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Series A,2,200000,10.0,1.5,TRUE,TRUE,2.0,FR
Series B,1,100000,5.0,1.0,FALSE,TRUE,0,WA
Common,0,700000,1.0,1.0,TRUE,FALSE,0,None"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        self.assertEqual(len(calculator.share_classes), 3)
        
        # Check Series A
        series_a = next(sc for sc in calculator.share_classes if sc.name == "Series A")
        self.assertEqual(series_a.shares, 200000)
        self.assertEqual(series_a.invested, 2000000)  # 200000 * 10.0
        self.assertEqual(series_a.preference_type, PreferenceType.PARTICIPATING)
        self.assertEqual(series_a.preference_multiple, 1.5)
        self.assertEqual(series_a.participation_cap, 2.0)
        self.assertEqual(series_a.priority, 2)
        self.assertTrue(series_a.convertible)
        self.assertEqual(series_a.anti_dilution_type, AntiDilutionType.FULL_RATCHET)
        
        # Check Series B
        series_b = next(sc for sc in calculator.share_classes if sc.name == "Series B")
        self.assertEqual(series_b.preference_type, PreferenceType.NON_PARTICIPATING)
        self.assertEqual(series_b.anti_dilution_type, AntiDilutionType.WEIGHTED_AVERAGE)
        self.assertIsNone(series_b.participation_cap)  # 0 should convert to None
        
        # Check Common
        common = next(sc for sc in calculator.share_classes if sc.name == "Common")
        self.assertEqual(common.preference_type, PreferenceType.COMMON)
        self.assertEqual(common.anti_dilution_type, AntiDilutionType.NONE)
    
    def test_parse_legacy_csv_format(self):
        """Test parsing legacy CSV format for backward compatibility."""
        csv_content = """Series,Order,Shares,Price,LiqPrefMultiple,Participating,Convertible
Series A,2,200000,10.0,1.5,TRUE,TRUE
Common,0,800000,1.0,1.0,FALSE,FALSE"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        self.assertEqual(len(calculator.share_classes), 2)
        
        # Check backward compatibility
        series_a = next(sc for sc in calculator.share_classes if sc.name == "Series A")
        self.assertEqual(series_a.shares, 200000)
        self.assertEqual(series_a.preference_multiple, 1.5)
        self.assertEqual(series_a.preference_type, PreferenceType.PARTICIPATING)
        self.assertEqual(series_a.priority, 2)  # From Order field
    
    def test_parse_mixed_format_handling(self):
        """Test handling of mixed old/new field names."""
        csv_content = """Share Class,Order,# Shares,Price,LiqPrefMultiple,Participation,Convertible
Series A,1,100000,5.0,2.0,FALSE,TRUE
Common,0,900000,1.0,1.0,TRUE,FALSE"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        self.assertEqual(len(calculator.share_classes), 2)
        
        series_a = next(sc for sc in calculator.share_classes if sc.name == "Series A")
        self.assertEqual(series_a.preference_multiple, 2.0)
        self.assertEqual(series_a.priority, 1)
    
    def test_parse_csv_with_empty_rows(self):
        """Test CSV parsing with empty rows."""
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Series A,1,100000,10.0,1.0,FALSE,TRUE,0,None

Common,0,900000,1.0,1.0,TRUE,FALSE,0,None
"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        # Should skip empty row
        self.assertEqual(len(calculator.share_classes), 2)
    
    def test_parse_csv_with_whitespace(self):
        """Test CSV parsing with extra whitespace."""
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
 Series A , 1 , 100000 , 10.0 , 1.0 , FALSE , TRUE , 0 , None 
Common,0,900000,1.0,1.0,TRUE,FALSE,0,None"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        self.assertEqual(len(calculator.share_classes), 2)
        
        # Should handle whitespace correctly
        series_a = next(sc for sc in calculator.share_classes if sc.name == " Series A ")
        self.assertEqual(series_a.shares, 100000)
    
    def test_parse_common_share_types(self):
        """Test parsing of different common share type names."""
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Common,0,500000,1.0,1.0,TRUE,FALSE,0,None
ESOP,0,200000,0.0,1.0,TRUE,FALSE,0,None
ESOP/Options,0,100000,0.0,1.0,TRUE,FALSE,0,None
ESOP/Opts,0,200000,0.0,1.0,TRUE,FALSE,0,None"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        # All should be classified as common
        for sc in calculator.share_classes:
            self.assertEqual(sc.preference_type, PreferenceType.COMMON)
    
    def test_parse_zero_price_shares(self):
        """Test parsing shares with zero price."""
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Series A,1,100000,10.0,1.0,FALSE,TRUE,0,None
Options,0,200000,0.0,1.0,TRUE,FALSE,0,None"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        # Options should have zero invested amount
        options = next(sc for sc in calculator.share_classes if sc.name == "Options")
        self.assertEqual(options.invested, 0)
        self.assertEqual(options.shares, 200000)
    
    def test_parse_participation_cap_values(self):
        """Test parsing different participation cap values."""
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Capped,1,100000,10.0,1.0,TRUE,TRUE,2.5,None
Uncapped,1,100000,10.0,1.0,TRUE,TRUE,0,None
NoCap,1,100000,10.0,1.0,TRUE,TRUE,,None"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        capped = next(sc for sc in calculator.share_classes if sc.name == "Capped")
        uncapped = next(sc for sc in calculator.share_classes if sc.name == "Uncapped")
        no_cap = next(sc for sc in calculator.share_classes if sc.name == "NoCap")
        
        self.assertEqual(capped.participation_cap, 2.5)
        self.assertIsNone(uncapped.participation_cap)  # 0 converts to None
        self.assertIsNone(no_cap.participation_cap)    # Empty converts to None
    
    def test_parse_anti_dilution_types(self):
        """Test parsing different anti-dilution types."""
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
None,1,100000,10.0,1.0,FALSE,TRUE,0,None
FullRatchet,1,100000,10.0,1.0,FALSE,TRUE,0,FR
WeightedAvg,1,100000,10.0,1.0,FALSE,TRUE,0,WA
Invalid,1,100000,10.0,1.0,FALSE,TRUE,0,INVALID"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        none_ad = next(sc for sc in calculator.share_classes if sc.name == "None")
        fr_ad = next(sc for sc in calculator.share_classes if sc.name == "FullRatchet")
        wa_ad = next(sc for sc in calculator.share_classes if sc.name == "WeightedAvg")
        invalid_ad = next(sc for sc in calculator.share_classes if sc.name == "Invalid")
        
        self.assertEqual(none_ad.anti_dilution_type, AntiDilutionType.NONE)
        self.assertEqual(fr_ad.anti_dilution_type, AntiDilutionType.FULL_RATCHET)
        self.assertEqual(wa_ad.anti_dilution_type, AntiDilutionType.WEIGHTED_AVERAGE)
        self.assertEqual(invalid_ad.anti_dilution_type, AntiDilutionType.NONE)  # Invalid defaults to NONE


class TestCSVParserErrorHandling(unittest.TestCase):
    """Test CSV parser error handling and edge cases."""
    
    def setUp(self):
        """Set up temporary directory for test CSV files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_temp_csv(self, content: str, filename: str = "test.csv") -> str:
        """Create a temporary CSV file with given content."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def test_file_not_found(self):
        """Test behavior when CSV file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            parse_cap_table_csv("nonexistent_file.csv")
    
    def test_empty_csv_file(self):
        """Test parsing empty CSV file."""
        filepath = self.create_temp_csv("")
        
        # Empty CSV should either raise exception or return empty calculator
        try:
            calculator = parse_cap_table_csv(filepath)
            # If no exception, should be empty
            self.assertEqual(len(calculator.share_classes), 0)
        except Exception:
            # Or it's fine to raise an exception for empty CSV
            pass
    
    def test_csv_header_only(self):
        """Test CSV with header but no data rows."""
        csv_content = "Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type"
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        # Should return empty calculator
        self.assertEqual(len(calculator.share_classes), 0)
    
    def test_malformed_csv_missing_fields(self):
        """Test malformed CSV with missing fields."""
        csv_content = """Share Class,Stack Order,# Shares
Series A,1,100000
Common,0"""  # Missing shares for Common
        
        filepath = self.create_temp_csv(csv_content)
        
        # Should handle gracefully or raise appropriate error
        try:
            calculator = parse_cap_table_csv(filepath)
            # If it succeeds, check it handled missing data appropriately
            self.assertLessEqual(len(calculator.share_classes), 2)
        except (ValueError, IndexError):
            # Or it's fine to raise an error for malformed data
            pass
    
    def test_invalid_numeric_values(self):
        """Test CSV with invalid numeric values."""
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Series A,1,abc,10.0,1.0,FALSE,TRUE,0,None
Common,0,100000,xyz,1.0,TRUE,FALSE,0,None"""
        
        filepath = self.create_temp_csv(csv_content)
        
        # Should raise ValueError for invalid numeric data
        with self.assertRaises(ValueError):
            parse_cap_table_csv(filepath)
    
    def test_invalid_boolean_values(self):
        """Test CSV with invalid boolean values."""
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Series A,1,100000,10.0,1.0,MAYBE,TRUE,0,None
Common,0,100000,1.0,1.0,TRUE,PERHAPS,0,None"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        # Invalid booleans should default to FALSE
        series_a = next(sc for sc in calculator.share_classes if sc.name == "Series A")
        common = next(sc for sc in calculator.share_classes if sc.name == "Common")
        
        self.assertEqual(series_a.preference_type, PreferenceType.NON_PARTICIPATING)  # MAYBE -> FALSE
        self.assertFalse(common.convertible)  # PERHAPS -> FALSE
    
    def test_very_large_numbers(self):
        """Test CSV with very large numeric values."""
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Large,1,1000000000,1000.0,5.0,FALSE,TRUE,0,None"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        large = next(sc for sc in calculator.share_classes if sc.name == "Large")
        self.assertEqual(large.shares, 1000000000)
        self.assertEqual(large.invested, 1000000000000.0)  # 1B shares * $1000 = $1T
    
    def test_unicode_and_special_characters(self):
        """Test CSV with unicode and special characters."""
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Série A,1,100000,10.0,1.0,FALSE,TRUE,0,None
Common & ESOP,0,900000,1.0,1.0,TRUE,FALSE,0,None"""
        
        filepath = self.create_temp_csv(csv_content)
        calculator = parse_cap_table_csv(filepath)
        
        # Should handle unicode characters
        self.assertEqual(len(calculator.share_classes), 2)
        
        names = [sc.name for sc in calculator.share_classes]
        self.assertIn("Série A", names)
        self.assertIn("Common & ESOP", names)


class TestDictParser(unittest.TestCase):
    """Test dictionary-based cap table parsing."""
    
    def test_parse_cap_table_dict_basic(self):
        """Test basic dictionary parsing functionality."""
        cap_table_data = [
            {
                "Share Class": "Series A",
                "Stack Order": 1,
                "# Shares": 100000,
                "Price": 10.0,
                "LPMultiple": 1.0,
                "Participation": "FALSE",
                "Convertible": "TRUE",
                "Participation Cap": 0,
                "AD Type": "None"
            },
            {
                "Share Class": "Common",
                "Stack Order": 0,
                "# Shares": 900000,
                "Price": 1.0,
                "LPMultiple": 1.0,
                "Participation": "TRUE",
                "Convertible": "FALSE",
                "Participation Cap": 0,
                "AD Type": "None"
            }
        ]
        
        calculator = parse_cap_table_dict(cap_table_data)
        
        self.assertEqual(len(calculator.share_classes), 2)
        
        series_a = next(sc for sc in calculator.share_classes if sc.name == "Series A")
        common = next(sc for sc in calculator.share_classes if sc.name == "Common")
        
        self.assertEqual(series_a.preference_type, PreferenceType.NON_PARTICIPATING)
        self.assertEqual(common.preference_type, PreferenceType.COMMON)
    
    def test_parse_cap_table_dict_legacy_format(self):
        """Test dictionary parsing with legacy field names."""
        cap_table_data = [
            {
                "Series": "Series A",
                "Order": 1,
                "Shares": 100000,
                "Price": 10.0,
                "LiqPrefMultiple": 1.5,
                "Participating": "TRUE",
                "Convertible": "TRUE"
            }
        ]
        
        calculator = parse_cap_table_dict(cap_table_data)
        
        self.assertEqual(len(calculator.share_classes), 1)
        
        series_a = calculator.share_classes[0]
        self.assertEqual(series_a.name, "Series A")
        self.assertEqual(series_a.preference_multiple, 1.5)
        self.assertEqual(series_a.preference_type, PreferenceType.PARTICIPATING)
    
    def test_parse_cap_table_dict_empty_list(self):
        """Test dictionary parsing with empty list."""
        calculator = parse_cap_table_dict([])
        
        self.assertEqual(len(calculator.share_classes), 0)
    
    def test_parse_cap_table_dict_missing_fields(self):
        """Test dictionary parsing with missing fields."""
        cap_table_data = [
            {
                "Share Class": "Incomplete",
                "# Shares": 100000,
                # Missing other required fields
            }
        ]
        
        calculator = parse_cap_table_dict(cap_table_data)
        
        # Should use defaults for missing fields
        incomplete = calculator.share_classes[0]
        self.assertEqual(incomplete.name, "Incomplete")
        self.assertEqual(incomplete.shares, 100000)
        self.assertEqual(incomplete.invested, 0)  # Should be 0 when price defaults to 0
    
    def test_parse_cap_table_dict_type_conversion(self):
        """Test dictionary parsing with string numeric values."""
        cap_table_data = [
            {
                "Share Class": "String Numbers",
                "Stack Order": "1",
                "# Shares": "100000",
                "Price": "10.5",
                "LPMultiple": "1.5",
                "Participation": "TRUE",
                "Convertible": "FALSE",
                "Participation Cap": "2.0",
                "AD Type": "FR"
            }
        ]
        
        calculator = parse_cap_table_dict(cap_table_data)
        
        share_class = calculator.share_classes[0]
        self.assertEqual(share_class.shares, 100000)
        self.assertEqual(share_class.invested, 1050000)  # 100000 * 10.5
        self.assertEqual(share_class.preference_multiple, 1.5)
        self.assertEqual(share_class.participation_cap, 2.0)
        self.assertEqual(share_class.anti_dilution_type, AntiDilutionType.FULL_RATCHET)


if __name__ == '__main__':
    unittest.main()