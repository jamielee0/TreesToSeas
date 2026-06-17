"""Unit tests for the degree-day phenology layer."""
import numpy as np

from treestoseas.model.degree_days import growing_degree_days, days_to_gdd_target


def test_gdd_basic_accumulation():
    temps = [20, 22, 18, 25]      # base 20 -> contributions 0, 2, 0, 5
    cum = growing_degree_days(temps, base_C=20.0)
    assert np.allclose(cum, [0, 2, 2, 7])


def test_gdd_upper_cutoff():
    temps = [30, 30]             # base 20, cutoff 25 -> capped at 25 -> 5 each
    cum = growing_degree_days(temps, base_C=20.0, upper_C=25.0)
    assert np.allclose(cum, [5, 10])


def test_gdd_nan_treated_as_zero():
    temps = [22, np.nan, 23]     # base 20 -> 2, 0, 3
    cum = growing_degree_days(temps, base_C=20.0)
    assert np.allclose(cum, [2, 2, 5])


def test_days_to_target():
    temps = [21, 21, 21, 21]     # +1/day above base 20
    assert days_to_gdd_target(temps, base_C=20.0, target_gdd=3) == 2  # 0-indexed day 2 -> cum=3
    assert days_to_gdd_target(temps, base_C=20.0, target_gdd=99) is None
