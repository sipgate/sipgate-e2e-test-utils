import unittest

from sipgate_e2e_test_utils.metrics import count_metric

metrics = """
# HELP unlabeled_counter_total
# TYPE unlabeled_counter_total counter
unlabeled_counter_total 10.0

# HELP labeled_counter_total
# TYPE labeled_counter_total counter
labeled_counter_total{label1="a"} 11.0
labeled_counter_total{label1="b", label2="1"} 9.0
labeled_counter_total{label1="b", label2="2"} 12.0

# HELP unlabeled_gauge
# TYPE unlabeled_gauge gauge
unlabeled_gauge 3.0

# HELP labeled_gauge
# TYPE labeled_gauge gauge
labeled_gauge{label1="a"} 5.0
labeled_gauge{label1="b", label2="1"} 4.0
labeled_gauge{label1="b", label2="2"} 3.0

# HELP a_histogram
# TYPE a_histogram histogram
a_histogram_sum 100
"""


class TestMetrics(unittest.IsolatedAsyncioTestCase):
    def test_finds_count_of_missing_metric(self):
        self.assertEqual(0, count_metric(metrics, 'non_existing'))

    def test_fails_for_unsupported_metric(self):
        with self.assertRaises(ValueError):
            count_metric(metrics, 'a_histogram')

    # counter

    def test_finds_value_of_unlabeled_counter(self):
        self.assertEqual(10, count_metric(metrics, 'unlabeled_counter_total'))

    def test_finds_value_of_labeled_counter(self):
        self.assertEqual(32, count_metric(metrics, 'labeled_counter_total'))

    def test_finds_sum_of_labeled_counter__given_partially_matching_labels(self):
        self.assertEqual(21, count_metric(metrics, 'labeled_counter_total', {'label1': 'b'}))

    def test_finds_sum_of_labeled_counter__given_fully_matching_labels(self):
        self.assertEqual(9, count_metric(metrics, 'labeled_counter_total', {'label1': 'b', 'label2': '1'}))

    # gauge

    def test_finds_value_of_unlabeled_gauge(self):
        self.assertEqual(3, count_metric(metrics, 'unlabeled_gauge'))

    def test_finds_value_of_labeled_gauge(self):
        self.assertEqual(12, count_metric(metrics, 'labeled_gauge'))

    def test_finds_sum_of_labeled_gauge__given_partially_matching_labels(self):
        self.assertEqual(7, count_metric(metrics, 'labeled_gauge', {'label1': 'b'}))

    def test_finds_sum_of_labeled_gauge__given_fully_matching_labels(self):
        self.assertEqual(4, count_metric(metrics, 'labeled_gauge', {'label1': 'b', 'label2': '1'}))
