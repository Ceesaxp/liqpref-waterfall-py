"""
Integration tests for end-to-end liquidation waterfall workflows.

Tests real-world scenarios, CSV-to-analysis pipelines, and performance
with actual cap table data following TDD principles.
"""

import unittest
import tempfile
import os
from liquidation_waterfall import (
    parse_cap_table_csv,
    format_cap_table_summary,
    format_waterfall_analysis,
    format_conversion_analysis,
    format_detailed_analysis,
    WaterfallCalculator,
    ShareClass,
    PreferenceType
)
from .test_fixtures import assert_distribution_totals_exit_value


class TestRealWorldScenarios(unittest.TestCase):
    """Test real-world cap table scenarios and data."""
    
    def test_captable_3_csv_integration(self):
        """Test integration with captable-3.csv file."""
        try:
            calc = parse_cap_table_csv('captable-3.csv')
            
            # Verify cap table loaded correctly
            self.assertGreater(len(calc.share_classes), 0)
            
            # Test various exit scenarios
            exit_values = [15000000, 50000000, 100000000, 180000000]
            
            for exit_value in exit_values:
                distribution = calc.calculate_distribution(exit_value)
                
                # Basic validation
                assert_distribution_totals_exit_value(distribution, exit_value)
                self.assertGreater(len(distribution), 0)
                
                # All amounts should be non-negative
                for name, amount in distribution.items():
                    self.assertGreaterEqual(amount, 0, f"{name} has negative amount at ${exit_value}")
            
            # Test formatting integration
            summary = format_cap_table_summary(calc)
            self.assertIn("Series E", summary)
            
            analysis = format_waterfall_analysis(calc, exit_values)
            self.assertIn("Waterfall Analysis", analysis)
            
        except FileNotFoundError:
            self.skipTest("captable-3.csv not found - skipping integration test")
    
    def test_sbda_csv_integration(self):
        """Test integration with sbda.csv file."""
        try:
            calc = parse_cap_table_csv('sbda.csv')
            
            # Verify priority groups functionality
            self.assertGreater(len(calc.share_classes), 0)
            
            # Test scenario where Series B shareholders have different multiples
            distribution = calc.calculate_distribution(20000000)
            
            # Verify Series B shareholders get proportional amounts
            series_b_total = 0
            for name, amount in distribution.items():
                if name.startswith('B:'):
                    series_b_total += amount
                    self.assertGreater(amount, 0, f"{name} should get something at $20M")
            
            # Series B should get significant portion at $20M
            self.assertGreater(series_b_total, 9000000)  # At least $9M
            
            assert_distribution_totals_exit_value(distribution, 20000000)
            
        except FileNotFoundError:
            self.skipTest("sbda.csv not found - skipping integration test")
    
    def test_simple_captable_csv_integration(self):
        """Test integration with simple_captable.csv if available."""
        try:
            calc = parse_cap_table_csv('simple_captable.csv')
            
            # Test basic functionality
            distribution = calc.calculate_distribution(5000000)
            assert_distribution_totals_exit_value(distribution, 5000000)
            
            # Test formatting
            summary = format_cap_table_summary(calc)
            self.assertIn("Cap Table Summary", summary)
            
        except FileNotFoundError:
            self.skipTest("simple_captable.csv not found - skipping integration test")


class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end workflows."""
    
    def setUp(self):
        """Set up temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_temp_csv(self, content: str, filename: str = "test.csv") -> str:
        """Create a temporary CSV file."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def test_csv_to_analysis_pipeline_complete(self):
        """Test complete pipeline from CSV to formatted analysis."""
        # Create a comprehensive CSV
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Series C,3,100000,30.0,1.5,FALSE,TRUE,0,None
Series B,2,150000,20.0,1.0,TRUE,TRUE,2.0,FR
Series A,1,200000,10.0,1.0,TRUE,TRUE,0,WA
Common,0,550000,1.0,1.0,TRUE,FALSE,0,None"""
        
        filepath = self.create_temp_csv(csv_content)
        
        # Parse CSV
        calc = parse_cap_table_csv(filepath)
        self.assertEqual(len(calc.share_classes), 4)
        
        # Generate all analysis types
        exit_values = [5000000, 15000000, 25000000]
        
        summary = format_cap_table_summary(calc)
        waterfall = format_waterfall_analysis(calc, exit_values)
        conversion = format_conversion_analysis(calc, exit_values)
        
        # Verify all outputs are generated
        self.assertGreater(len(summary), 100)
        self.assertGreater(len(waterfall), 200)
        self.assertGreater(len(conversion), 100)
        
        # Verify key content is present
        for output in [summary, waterfall, conversion]:
            self.assertIn("Series C", output)
            self.assertIn("Series B", output)
            self.assertIn("Series A", output)
            self.assertIn("Common", output)
        
        # Test detailed analysis for each exit value
        for exit_value in exit_values:
            detailed = format_detailed_analysis(calc, exit_value)
            self.assertGreater(len(detailed), 100)
            self.assertIn(f"${exit_value/1000000:.1f}M Exit", detailed)
    
    def test_programmatic_cap_table_creation_workflow(self):
        """Test workflow using programmatic cap table creation."""
        # Create cap table programmatically
        calc = WaterfallCalculator()
        
        # Add various share classes
        series_a = ShareClass(
            "Series A", 100000, 2000000, 
            PreferenceType.PARTICIPATING, 1.0, 2.5, 2
        )
        series_b = ShareClass(
            "Series B", 150000, 1500000,
            PreferenceType.NON_PARTICIPATING, 1.5, None, 1
        )
        common = ShareClass(
            "Common", 750000, 0,
            PreferenceType.COMMON, priority=0
        )
        
        calc.add_share_class(series_a)
        calc.add_share_class(series_b)
        calc.add_share_class(common)
        
        # Run complete analysis
        exit_values = [2000000, 8000000, 20000000]
        
        # Test all distributions
        for exit_value in exit_values:
            distribution = calc.calculate_distribution(exit_value)
            assert_distribution_totals_exit_value(distribution, exit_value)
            
            # Verify logical results
            if exit_value >= 3500000:  # Above total LPs
                # Series A should get at least its LP
                self.assertGreaterEqual(distribution["Series A"], 2000000 * 0.95)
                # Series B should get at least its LP  
                self.assertGreaterEqual(distribution["Series B"], 2250000 * 0.95)  # 1.5 * 1.5M
        
        # Test formatting workflow
        summary = format_cap_table_summary(calc)
        analysis = format_waterfall_analysis(calc, exit_values)
        
        self.assertIn("2.5x", summary)  # Series A cap
        self.assertIn("Participating", summary)
        self.assertIn("Non Participating", summary)
    
    def test_library_vs_csv_consistency(self):
        """Test that library and CSV approaches give same results."""
        # Create cap table via CSV
        csv_content = """Share Class,Stack Order,# Shares,Price,LPMultiple,Participation,Convertible,Participation Cap,AD Type
Series A,1,200000,5.0,1.0,FALSE,TRUE,0,None
Common,0,800000,1.0,1.0,TRUE,FALSE,0,None"""
        
        filepath = self.create_temp_csv(csv_content)
        csv_calc = parse_cap_table_csv(filepath)
        
        # Create equivalent cap table programmatically
        prog_calc = WaterfallCalculator()
        series_a = ShareClass("Series A", 200000, 1000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        common = ShareClass("Common", 800000, 0, PreferenceType.COMMON, priority=0)
        prog_calc.add_share_class(series_a)
        prog_calc.add_share_class(common)
        
        # Test multiple exit values
        exit_values = [500000, 1000000, 3000000, 10000000]
        
        for exit_value in exit_values:
            csv_dist = csv_calc.calculate_distribution(exit_value)
            prog_dist = prog_calc.calculate_distribution(exit_value)
            
            # Should get identical results
            for name in ["Series A", "Common"]:
                self.assertAlmostEqual(
                    csv_dist[name], prog_dist[name], delta=1000,
                    msg=f"Mismatch for {name} at ${exit_value}: CSV={csv_dist[name]}, Prog={prog_dist[name]}"
                )
    
    def test_complex_multi_round_scenario(self):
        """Test complex scenario with multiple financing rounds."""
        # Create realistic multi-round scenario
        calc = WaterfallCalculator()
        
        # Seed round
        seed = ShareClass("Seed", 50000, 500000, PreferenceType.NON_PARTICIPATING, 1.0, None, 1)
        
        # Series A
        series_a = ShareClass("Series A", 100000, 2000000, PreferenceType.NON_PARTICIPATING, 1.0, None, 2)
        
        # Series B  
        series_b = ShareClass("Series B", 75000, 3000000, PreferenceType.PARTICIPATING, 1.0, 2.0, 3)
        
        # Series C
        series_c = ShareClass("Series C", 50000, 5000000, PreferenceType.PARTICIPATING, 1.0, 3.0, 4)
        
        # Common + ESOP
        common = ShareClass("Common", 600000, 0, PreferenceType.COMMON, priority=0)
        esop = ShareClass("ESOP", 125000, 0, PreferenceType.COMMON, priority=0)
        
        for sc in [seed, series_a, series_b, series_c, common, esop]:
            calc.add_share_class(sc)
        
        # Test various exit scenarios
        exit_scenarios = [
            (8000000, "Low exit - some conversions"),
            (25000000, "Medium exit - mixed strategies"),
            (100000000, "High exit - mostly conversions"),
            (500000000, "Very high exit - all convert")
        ]
        
        for exit_value, scenario in exit_scenarios:
            distribution = calc.calculate_distribution(exit_value)
            
            # Validate basic properties
            assert_distribution_totals_exit_value(distribution, exit_value)
            
            for name, amount in distribution.items():
                self.assertGreaterEqual(amount, 0, f"{name} negative in {scenario}")
            
            # Validate that higher priority gets paid first at low exits
            if exit_value <= 10000000:
                # Series C should get more than earlier rounds at low exits
                self.assertGreaterEqual(
                    distribution["Series C"], 
                    distribution["Series A"],
                    f"Priority violation in {scenario}"
                )


class TestPerformanceAndScalability(unittest.TestCase):
    """Test performance with large cap tables and many exit values."""
    
    def test_large_cap_table_performance(self):
        """Test performance with large number of share classes."""
        calc = WaterfallCalculator()
        
        # Create 50 share classes (reasonable large cap table)
        for i in range(50):
            share_class = ShareClass(
                f"Investor {i}",
                shares=10000 + i * 1000,
                invested=100000 + i * 50000,
                preference_type=PreferenceType.NON_PARTICIPATING if i % 2 == 0 else PreferenceType.PARTICIPATING,
                preference_multiple=1.0 + (i % 3) * 0.5,
                participation_cap=2.0 if i % 3 == 0 and i % 2 == 1 else None,
                priority=i // 10  # Group into priority levels
            )
            calc.add_share_class(share_class)
        
        # Test calculation performance
        import time
        start_time = time.time()
        
        distribution = calc.calculate_distribution(50000000)
        
        calc_time = time.time() - start_time
        
        # Should complete reasonably quickly (< 1 second for 50 classes)
        self.assertLess(calc_time, 1.0, f"Calculation took {calc_time:.3f}s for 50 share classes")
        
        # Verify correctness
        assert_distribution_totals_exit_value(distribution, 50000000)
        self.assertEqual(len(distribution), 50)
    
    def test_many_exit_values_performance(self):
        """Test performance with many exit values."""
        calc = WaterfallCalculator()
        
        # Moderate cap table
        for i in range(10):
            share_class = ShareClass(
                f"Class {i}",
                shares=100000,
                invested=1000000,
                preference_type=PreferenceType.NON_PARTICIPATING,
                priority=i
            )
            calc.add_share_class(share_class)
        
        # Test many exit values
        exit_values = [i * 1000000 for i in range(1, 101)]  # 1M to 100M in 1M increments
        
        import time
        start_time = time.time()
        
        for exit_value in exit_values:
            distribution = calc.calculate_distribution(exit_value)
            assert_distribution_totals_exit_value(distribution, exit_value)
        
        total_time = time.time() - start_time
        
        # Should complete 100 calculations reasonably quickly
        self.assertLess(total_time, 5.0, f"100 calculations took {total_time:.3f}s")
    
    def test_formatting_performance_with_large_data(self):
        """Test formatting performance with large datasets."""
        calc = WaterfallCalculator()
        
        # Create moderate cap table
        for i in range(20):
            share_class = ShareClass(
                f"Share Class {i:02d}",
                shares=50000 + i * 10000,
                invested=500000 + i * 250000,
                preference_type=PreferenceType.PARTICIPATING if i % 2 else PreferenceType.NON_PARTICIPATING,
                priority=i // 5
            )
            calc.add_share_class(share_class)
        
        # Test formatting with many exit values
        exit_values = [i * 5000000 for i in range(1, 21)]  # 5M to 100M
        
        import time
        start_time = time.time()
        
        # Test all formatting functions
        summary = format_cap_table_summary(calc)
        analysis = format_waterfall_analysis(calc, exit_values)
        conversion = format_conversion_analysis(calc, exit_values)
        
        for exit_value in exit_values[:5]:  # Test detailed for subset
            detailed = format_detailed_analysis(calc, exit_value)
        
        format_time = time.time() - start_time
        
        # Should complete formatting reasonably quickly
        self.assertLess(format_time, 3.0, f"Formatting took {format_time:.3f}s")
        
        # Verify outputs are substantial
        self.assertGreater(len(summary), 1000)
        self.assertGreater(len(analysis), 5000)
        self.assertGreater(len(conversion), 2000)


if __name__ == '__main__':
    unittest.main()