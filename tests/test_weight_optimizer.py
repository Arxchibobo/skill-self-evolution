#!/usr/bin/env python3
"""
Tests for weight_optimizer.py
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from weight_optimizer import WeightOptimizer


class TestWeightOptimizer(unittest.TestCase):
    """Test WeightOptimizer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.optimizer = WeightOptimizer()

    def test_calculate_time_decay(self):
        """Test time decay calculation"""
        # Recent data should have decay close to 1
        decay_recent = self.optimizer.calculate_time_decay(1)
        self.assertGreater(decay_recent, 0.98)

        # Data from 60 days ago should have decay of ~0.5 (half-life)
        decay_half_life = self.optimizer.calculate_time_decay(60)
        self.assertAlmostEqual(decay_half_life, 0.5, places=2)

        # Old data should have low decay
        decay_old = self.optimizer.calculate_time_decay(180)
        self.assertLess(decay_old, 0.2)

    def test_calculate_weights(self):
        """Test weight calculation"""
        elements = {
            'element1': [
                {'quality_score': 0.9, 'timestamp': datetime.now().isoformat()},
                {'quality_score': 0.85, 'timestamp': datetime.now().isoformat()}
            ],
            'element2': [
                {'quality_score': 0.7, 'timestamp': (datetime.now() - timedelta(days=30)).isoformat()}
            ]
        }

        weights = self.optimizer.calculate_weights(elements)

        # Should return weights for both elements
        self.assertIn('element1', weights)
        self.assertIn('element2', weights)

        # Weights should be between 0 and 1
        self.assertGreaterEqual(weights['element1'], 0)
        self.assertLessEqual(weights['element1'], 1)

        # element1 should have higher weight (better quality, more recent)
        self.assertGreater(weights['element1'], weights['element2'])

    def test_smoothing(self):
        """Test smoothing factor"""
        elements = {
            'element1': [
                {'quality_score': 0.9, 'timestamp': datetime.now().isoformat()}
            ]
        }

        previous_weights = {'element1': 0.5}

        # With smoothing, new weight should be between old and new
        weights = self.optimizer.calculate_weights(elements, previous_weights)

        # New weight should be influenced by previous weight
        self.assertNotEqual(weights['element1'], 0.9)
        self.assertGreater(weights['element1'], previous_weights['element1'])


if __name__ == '__main__':
    unittest.main()
