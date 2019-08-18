import unittest

import numpy as np

from anal_py.anal_utils import calculate_metrics


class TestAnalUtils(unittest.TestCase):

    def test_calculate_metrics(self):
        calculated = np.array([[1, 2, 3], [3, 2, 1]], dtype=float)
        predicted = np.array([[1, 3, 2], [1, 2, 3]], dtype=float)
        metrics = calculate_metrics(calculated, predicted, 3)
        self.assertTrue(np.allclose(metrics, [0., 1., 1., 1., 1., 1., 1.29099445, 1.04666667]))
