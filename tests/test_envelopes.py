"""Unit tests for the suitability envelope + HSI combiners.

The critical invariant: any single lethal factor (e.g. DO -> 0) must drive the
geometric-mean HSI to 0 -- this is what lets the model capture a hypoxia/heat
"squeeze". An arithmetic mean would mask it.
"""
import numpy as np

from treestoseas.model.envelopes import trapezoid, combine_hsi


def test_trapezoid_plateau_and_zero():
    bp = [2, 18, 28, 36]   # oyster temperature
    assert trapezoid(22.0, bp).item() == 1.0          # in the optimum plateau
    assert trapezoid(0.0, bp).item() == 0.0           # below lower bound
    assert trapezoid(40.0, bp).item() == 0.0          # above upper bound
    # midpoint of the rising limb (2 -> 18) is 10 -> 0.5
    assert abs(trapezoid(10.0, bp).item() - 0.5) < 1e-9


def test_trapezoid_nan_propagates():
    assert np.isnan(trapezoid(np.nan, [2, 18, 28, 36]).item())


def test_geometric_mean_zero_dominates():
    good = np.array([1.0, 1.0, 1.0])
    lethal = np.array([0.0, 0.0, 0.0])   # e.g. anoxia
    hsi = combine_hsi({"temp": good, "sal": good, "do": lethal})
    assert np.allclose(hsi, 0.0)         # one lethal factor zeros the whole HSI


def test_geometric_mean_all_optimal():
    ones = np.ones(5)
    hsi = combine_hsi({"a": ones, "b": ones, "c": ones})
    assert np.allclose(hsi, 1.0)


def test_nan_factor_is_ignored_not_lethal():
    measured = np.array([0.8, 0.8])
    missing = np.array([np.nan, np.nan])  # unmeasured factor must not zero HSI
    hsi = combine_hsi({"a": measured, "b": missing})
    assert np.allclose(hsi, 0.8, atol=1e-9)


def test_liebig_min():
    hsi = combine_hsi({"a": np.array([0.9]), "b": np.array([0.3])},
                      method="liebig_min")
    assert abs(hsi.item() - 0.3) < 1e-9
