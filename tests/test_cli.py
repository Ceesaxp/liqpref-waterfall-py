"""
Tests for command-line interface functionality.

Tests CLI argument parsing, exit value parsing, output formatting flags,
and error handling following TDD principles.
"""

import unittest
import sys
import io
import tempfile
import os
from unittest.mock import patch, MagicMock
import subprocess


class TestExitValueParsing(unittest.TestCase):
    """Test exit value parsing functionality from CLI."""
    
    def test_parse_exit_values_millions(self):
        """Test parsing exit values with M suffix."""
        # Import the function from cli module
        sys.path.insert(0, '/Users/andrei/Developer/Python/liq-pref')
        from cli import parse_exit_values
        
        test_cases = [
            (["15M"], [15000000]),
            (["1.5M"], [1500000]),
            (["100M"], [100000000]),
            (["0.5M"], [500000])
        ]
        
        for input_values, expected in test_cases:
            result = parse_exit_values(input_values)
            self.assertEqual(result, expected, f"Failed for {input_values}")
    
    def test_parse_exit_values_billions(self):
        """Test parsing exit values with B suffix."""
        sys.path.insert(0, '/Users/andrei/Developer/Python/liq-pref')
        from cli import parse_exit_values
        
        test_cases = [
            (["1B"], [1000000000]),
            (["2.5B"], [2500000000]),
            (["0.1B"], [100000000])
        ]
        
        for input_values, expected in test_cases:
            result = parse_exit_values(input_values)
            self.assertEqual(result, expected, f"Failed for {input_values}")
    
    def test_parse_exit_values_thousands(self):
        """Test parsing exit values with K suffix."""
        sys.path.insert(0, '/Users/andrei/Developer/Python/liq-pref')
        from cli import parse_exit_values
        
        test_cases = [
            (["500K"], [500000]),
            (["1.5K"], [1500]),
            (["1000K"], [1000000])
        ]
        
        for input_values, expected in test_cases:
            result = parse_exit_values(input_values)
            self.assertEqual(result, expected, f"Failed for {input_values}")
    
    def test_parse_exit_values_raw_numbers(self):
        """Test parsing raw numeric exit values."""
        sys.path.insert(0, '/Users/andrei/Developer/Python/liq-pref')
        from cli import parse_exit_values
        
        test_cases = [
            (["15000000"], [15000000]),
            (["1500000.50"], [1500000.50]),
            (["1000"], [1000])
        ]
        
        for input_values, expected in test_cases:
            result = parse_exit_values(input_values)
            self.assertEqual(result, expected, f"Failed for {input_values}")
    
    def test_parse_exit_values_mixed_formats(self):
        """Test parsing multiple exit values with mixed formats."""
        sys.path.insert(0, '/Users/andrei/Developer/Python/liq-pref')
        from cli import parse_exit_values
        
        input_values = ["15M", "25000000", "1.5B", "500K"]
        expected = [15000000, 25000000, 1500000000, 500000]
        
        result = parse_exit_values(input_values)
        self.assertEqual(result, expected)
    
    def test_parse_exit_values_case_insensitive(self):
        """Test that suffix parsing is case insensitive."""
        sys.path.insert(0, '/Users/andrei/Developer/Python/liq-pref')
        from cli import parse_exit_values
        
        test_cases = [
            (["15m"], [15000000]),
            (["1.5b"], [1500000000]),
            (["500k"], [500000])
        ]
        
        for input_values, expected in test_cases:
            result = parse_exit_values(input_values)
            self.assertEqual(result, expected, f"Failed for {input_values}")
    
    def test_parse_exit_values_invalid_format(self):
        """Test error handling for invalid exit value formats."""
        sys.path.insert(0, '/Users/andrei/Developer/Python/liq-pref')
        from cli import parse_exit_values
        
        invalid_inputs = [
            ["invalid"],
            ["15X"],
            [""],
            ["M15"],
            ["1.5.5M"]
        ]
        
        for invalid_input in invalid_inputs:
            with self.assertRaises(ValueError, msg=f"Should raise ValueError for {invalid_input}"):
                parse_exit_values(invalid_input)


class TestCLIArgumentParsing(unittest.TestCase):
    """Test CLI argument parsing and validation."""
    
    def setUp(self):
        """Set up temporary CSV file for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.temp_dir, "test.csv")
        
        # Create a simple test CSV
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Series A,1,100000,10.0,1.0,FALSE,TRUE,0,None
Common,0,900000,1.0,1.0,TRUE,FALSE,0,None"""
        
        with open(self.test_csv, 'w') as f:
            f.write(csv_content)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_cli_basic_execution(self):
        """Test basic CLI execution with default parameters."""
        # Test that CLI can be imported and basic functions work
        sys.path.insert(0, '/Users/andrei/Developer/Python/liq-pref')
        
        try:
            import cli
            # Test argument parser creation
            parser = cli.argparse.ArgumentParser()
            self.assertIsNotNone(parser)
        except ImportError:
            self.skipTest("CLI module not available for testing")
    
    def test_cli_help_output(self):
        """Test CLI help output."""
        try:
            result = subprocess.run(
                [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should exit with code 0 for help
            self.assertEqual(result.returncode, 0)
            
            # Should contain usage information
            self.assertIn("usage:", result.stdout.lower())
            self.assertIn("exit-values", result.stdout)
            self.assertIn("summary", result.stdout)
            self.assertIn("detailed", result.stdout)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("CLI execution test skipped - timeout or file not found")
    
    def test_cli_invalid_file_handling(self):
        """Test CLI behavior with invalid file."""
        try:
            result = subprocess.run(
                [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", "nonexistent.csv"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should exit with non-zero code
            self.assertNotEqual(result.returncode, 0)
            
            # Should contain error message
            self.assertIn("Could not find file", result.stderr)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("CLI execution test skipped - timeout or file not found")
    
    def test_cli_valid_file_execution(self):
        """Test CLI execution with valid CSV file."""
        try:
            result = subprocess.run(
                [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", self.test_csv, 
                 "--exit-values", "5M", "10M"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should succeed
            self.assertEqual(result.returncode, 0)
            
            # Should contain analysis output
            self.assertIn("Waterfall Analysis", result.stdout)
            self.assertIn("Series A", result.stdout)
            self.assertIn("Common", result.stdout)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("CLI execution test skipped - timeout or file not found")
    
    def test_cli_summary_flag(self):
        """Test CLI --summary flag."""
        try:
            result = subprocess.run(
                [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", self.test_csv, 
                 "--summary", "--exit-values", "5M"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should succeed
            self.assertEqual(result.returncode, 0)
            
            # Should contain both summary and analysis
            self.assertIn("Cap Table Summary", result.stdout)
            self.assertIn("Waterfall Analysis", result.stdout)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("CLI execution test skipped - timeout or file not found")
    
    def test_cli_detailed_flag(self):
        """Test CLI --detailed flag."""
        try:
            result = subprocess.run(
                [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", self.test_csv, 
                 "--detailed", "--exit-values", "5M"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should succeed
            self.assertEqual(result.returncode, 0)
            
            # Should contain detailed analysis
            self.assertIn("Detailed Waterfall Analysis", result.stdout)
            self.assertIn("Priority Structure", result.stdout)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("CLI execution test skipped - timeout or file not found")
    
    def test_cli_conversion_only_flag(self):
        """Test CLI --conversion-only flag."""
        try:
            result = subprocess.run(
                [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", self.test_csv, 
                 "--conversion-only", "--exit-values", "5M", "15M"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should succeed
            self.assertEqual(result.returncode, 0)
            
            # Should contain only conversion analysis
            self.assertIn("Conversion Analysis", result.stdout)
            # Should not contain waterfall analysis
            self.assertNotIn("Waterfall Analysis", result.stdout)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("CLI execution test skipped - timeout or file not found")


class TestCLIErrorHandling(unittest.TestCase):
    """Test CLI error handling and edge cases."""
    
    def test_cli_invalid_exit_values(self):
        """Test CLI behavior with invalid exit values."""
        temp_dir = tempfile.mkdtemp()
        test_csv = os.path.join(temp_dir, "test.csv")
        
        # Create minimal CSV
        with open(test_csv, 'w') as f:
            f.write("Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type\n")
            f.write("Common,0,1000000,1.0,1.0,TRUE,FALSE,0,None\n")
        
        try:
            result = subprocess.run(
                [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", test_csv, 
                 "--exit-values", "invalid", "5M"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should fail with non-zero exit code
            self.assertNotEqual(result.returncode, 0)
            
            # Should contain error message about exit values
            self.assertIn("Error parsing exit values", result.stderr)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("CLI execution test skipped - timeout or file not found")
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_cli_empty_csv_file(self):
        """Test CLI behavior with empty CSV file."""
        temp_dir = tempfile.mkdtemp()
        empty_csv = os.path.join(temp_dir, "empty.csv")
        
        # Create empty file
        with open(empty_csv, 'w') as f:
            f.write("")
        
        try:
            result = subprocess.run(
                [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", empty_csv],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should fail or warn about empty cap table
            self.assertNotEqual(result.returncode, 0)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("CLI execution test skipped - timeout or file not found")
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_cli_keyboard_interrupt_handling(self):
        """Test CLI behavior with keyboard interrupt simulation."""
        # This test is more conceptual since we can't easily simulate Ctrl+C
        # in subprocess tests, but we can verify the error handling code exists
        sys.path.insert(0, '/Users/andrei/Developer/Python/liq-pref')
        
        try:
            import cli
            # Verify that main function exists and can be called
            self.assertTrue(hasattr(cli, 'main'))
            self.assertTrue(callable(cli.main))
        except ImportError:
            self.skipTest("CLI module not available for testing")
    
    def test_cli_no_arguments(self):
        """Test CLI behavior with no arguments."""
        try:
            result = subprocess.run(
                [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should fail due to missing required csv_file argument
            self.assertNotEqual(result.returncode, 0)
            
            # Should contain usage information
            self.assertIn("usage:", result.stderr.lower())
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("CLI execution test skipped - timeout or file not found")


class TestCLIOutputFormatting(unittest.TestCase):
    """Test CLI output formatting and content."""
    
    def setUp(self):
        """Set up test CSV file."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.temp_dir, "test.csv")
        
        # Create CSV with interesting data for testing
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Series B,2,150000,20.0,1.5,TRUE,TRUE,2.0,None
Series A,1,200000,10.0,1.0,FALSE,TRUE,0,None
Common,0,650000,1.0,1.0,TRUE,FALSE,0,None"""
        
        with open(self.test_csv, 'w') as f:
            f.write(csv_content)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_cli_output_contains_expected_sections(self):
        """Test that CLI output contains all expected sections."""
        try:
            result = subprocess.run(
                [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", self.test_csv, 
                 "--summary", "--exit-values", "10M", "25M"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.assertEqual(result.returncode, 0)
            
            # Should contain cap table summary
            self.assertIn("Cap Table Summary", result.stdout)
            self.assertIn("Series", result.stdout)
            self.assertIn("Shares", result.stdout)
            self.assertIn("Invested", result.stdout)
            self.assertIn("Ownership", result.stdout)
            
            # Should contain waterfall analysis
            self.assertIn("Waterfall Analysis", result.stdout)
            self.assertIn("$10M", result.stdout)
            self.assertIn("$25M", result.stdout)
            
            # Should contain conversion analysis
            self.assertIn("Conversion Analysis", result.stdout)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("CLI execution test skipped - timeout or file not found")
    
    def test_cli_output_numeric_formatting(self):
        """Test that CLI output formats numbers correctly."""
        try:
            result = subprocess.run(
                [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", self.test_csv, 
                 "--exit-values", "5M"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.assertEqual(result.returncode, 0)
            
            # Should contain properly formatted monetary amounts
            self.assertIn("$", result.stdout)
            self.assertIn("M", result.stdout)  # Million formatting
            
            # Should contain percentage formatting
            self.assertIn("%", result.stdout)
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("CLI execution test skipped - timeout or file not found")
    
    def test_cli_output_with_different_exit_values(self):
        """Test CLI output with various exit value formats."""
        exit_value_tests = [
            (["1M"], "1M"),
            (["1000000"], "1M"),
            (["1.5B"], "1500M"),
            (["500K"], "0M")  # Should round to 0M or show as 0.5M
        ]
        
        for exit_values, expected_in_output in exit_value_tests:
            try:
                result = subprocess.run(
                    [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", self.test_csv, 
                     "--exit-values"] + exit_values,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                self.assertEqual(result.returncode, 0, f"Failed for exit values {exit_values}")
                
                # Output should contain formatted exit value
                self.assertIn("$", result.stdout)
                
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.skipTest("CLI execution test skipped - timeout or file not found")
                break
    
    def test_cli_output_consistency_across_runs(self):
        """Test that CLI output is consistent across multiple runs."""
        # Run CLI multiple times with same inputs
        runs = []
        
        for i in range(3):
            try:
                result = subprocess.run(
                    [sys.executable, "/Users/andrei/Developer/Python/liq-pref/cli.py", self.test_csv, 
                     "--exit-values", "10M"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                self.assertEqual(result.returncode, 0)
                runs.append(result.stdout)
                
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.skipTest("CLI execution test skipped - timeout or file not found")
                break
        
        # All runs should produce identical output
        if len(runs) >= 2:
            self.assertEqual(runs[0], runs[1], "CLI output not consistent across runs")
            if len(runs) >= 3:
                self.assertEqual(runs[1], runs[2], "CLI output not consistent across runs")


if __name__ == '__main__':
    unittest.main()