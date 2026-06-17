"""Per-factor suitability curves and Habitat Suitability Index (HSI) combiners.

The model is deliberately *mechanistic and transparent* (not machine-learned):
each environmental factor maps to a [0, 1] suitability through a trapezoidal
membership function, and the factors are combined into a single HSI. The default
combiner is the geometric mean, so that ANY single lethal factor (e.g. DO -> 0)
drives the whole HSI to 0 -- this is what captures a true hypoxia/heat "squeeze".
An arithmetic mean would mask it. A Liebig minimum-factor combiner is also provided.
"""
from __future__ import annotations

import warnings

import numpy as np


def trapezoid(x, breakpoints):
    """Trapezoidal suitability in [0, 1].

    Parameters
    ----------
    x : array-like
        Environmental values (e.g. temperature in C).
    breakpoints : sequence of 4 floats
        [lo_zero, lo_one, hi_one, hi_zero]. Suitability is 0 at/below ``lo_zero``,
        ramps to 1 by ``lo_one``, holds 1 to ``hi_one``, ramps back to 0 by
        ``hi_zero``. NaN inputs propagate to NaN outputs.
    """
    lo0, lo1, hi1, hi0 = (float(b) for b in breakpoints)
    x = np.asarray(x, dtype=float)
    s = np.zeros_like(x)

    # plateau
    s = np.where((x >= lo1) & (x <= hi1), 1.0, s)
    # rising limb
    if lo1 > lo0:
        m = (x > lo0) & (x < lo1)
        s = np.where(m, (x - lo0) / (lo1 - lo0), s)
    # falling limb
    if hi0 > hi1:
        m = (x > hi1) & (x < hi0)
        s = np.where(m, (hi0 - x) / (hi0 - hi1), s)

    s = np.clip(s, 0.0, 1.0)
    return np.where(np.isnan(x), np.nan, s)


def factor_suitability(values, factors):
    """Compute per-factor suitability for one species.

    Parameters
    ----------
    values : dict[str, array-like]
        Environmental time series keyed by canonical variable name
        (e.g. ``temp_C``, ``salinity_ppt``, ``DO_mgL``, ``pH``).
    factors : dict[str, list]
        Breakpoints per factor, as in ``config/species.yaml``.

    Returns
    -------
    dict[str, np.ndarray]
        Suitability score arrays for each factor that is present in ``values``.
    """
    out = {}
    for name, bp in factors.items():
        if name in values and values[name] is not None:
            out[name] = trapezoid(values[name], bp)
    return out


def combine_hsi(factor_scores, method="geometric_mean"):
    """Combine per-factor suitabilities into a single HSI in [0, 1].

    Parameters
    ----------
    factor_scores : dict[str, array-like] | sequence of array-like
        Per-factor suitability arrays.
    method : {'geometric_mean', 'liebig_min'}
        ``geometric_mean`` -> any zero factor zeros the HSI (captures squeezes).
        ``liebig_min``      -> HSI equals the single most-limiting factor.

    NaN factors are ignored (treated as "not measured") rather than zeroing the HSI.
    """
    if isinstance(factor_scores, dict):
        arrays = list(factor_scores.values())
    else:
        arrays = list(factor_scores)
    if not arrays:
        raise ValueError("combine_hsi requires at least one factor")

    stack = np.vstack([np.asarray(a, dtype=float) for a in arrays])

    # Days where every factor is NaN (nothing measured) legitimately yield NaN HSI;
    # suppress the resulting all-NaN/empty-slice RuntimeWarnings.
    with warnings.catch_warnings(), np.errstate(divide="ignore", invalid="ignore"):
        warnings.simplefilter("ignore", RuntimeWarning)
        if method == "geometric_mean":
            logs = np.log(stack)          # log(0) -> -inf -> exp(mean) -> 0
            return np.exp(np.nanmean(logs, axis=0))
        if method == "liebig_min":
            return np.nanmin(stack, axis=0)
    raise ValueError(f"unknown combiner: {method!r}")
