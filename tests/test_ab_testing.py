#!/usr/bin/env python3
"""
Tests for ab_testing.py
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from ab_testing import ABTesting


class TestABTesting(unittest.TestCase):
    """Test ABTesting class"""

    def setUp(self):
        """Set up test fixtures"""
        self.ab_test = ABTesting(confidence_level=0.95)

    def test_calculate_mean(self):
        """Test mean calculation"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        mean = self.ab_test.calculate_mean(values)
        self.assertEqual(mean, 3.0)

        # Empty list
        mean_empty = self.ab_test.calculate_mean([])
        self.assertEqual(mean_empty, 0.0)

    def test_calculate_variance(self):
        """Test variance calculation"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        variance = self.ab_test.calculate_variance(values)
        self.assertGreater(variance, 0)

        # Single value should have variance 0
        variance_single = self.ab_test.calculate_variance([5.0])
        self.assertEqual(variance_single, 0.0)

    def test_t_test(self):
        """Test t-test"""
        # Group A: lower values
        group_a = [0.5, 0.6, 0.55, 0.52, 0.58]
        # Group B: higher values (should be significantly better)
        group_b = [0.8, 0.85, 0.82, 0.83, 0.81]

        t_stat, p_value, is_significant = self.ab_test.t_test(group_a, group_b)

        # B should be better than A
        self.assertGreater(t_stat, 0)

        # Should be significant
        self.assertTrue(is_significant or p_value < 0.05)

    def test_calculate_effect_size(self):
        """Test Cohen's d calculation"""
        group_a = [0.5, 0.6, 0.55]
        group_b = [0.8, 0.85, 0.82]

        effect_size = self.ab_test.calculate_effect_size(group_a, group_b)

        # Effect size should be large for this example
        self.assertGreater(effect_size, 0)

    def test_analyze(self):
        """Test full analysis"""
        version_a = [
            {'quality_score': 0.7, 'satisfaction': 0.75},
            {'quality_score': 0.72, 'satisfaction': 0.77},
            {'quality_score': 0.68, 'satisfaction': 0.73}
        ]

        version_b = [
            {'quality_score': 0.85, 'satisfaction': 0.88},
            {'quality_score': 0.87, 'satisfaction': 0.90},
            {'quality_score': 0.83, 'satisfaction': 0.86}
        ]

        results = self.ab_test.analyze(version_a, version_b, ['quality_score', 'satisfaction'])

        # Should have results for both metrics
        self.assertIn('quality_score', results['metrics'])
        self.assertIn('satisfaction', results['metrics'])

        # Should have a recommendation
        self.assertIn('recommendation', results)

        # Version B should be the winner for quality_score
        self.assertEqual(results['metrics']['quality_score']['winner'], 'version_b')


if __name__ == '__main__':
    unittest.main()
