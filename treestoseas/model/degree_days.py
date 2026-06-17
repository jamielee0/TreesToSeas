"""Degree-day (accumulated thermal unit) phenology layer.

Degree-days predict the TIMING of development/spawning/activity for poikilotherms
and are well-supported for *pre-maturation* growth (Neuheimer & Taggart 2007, CJFAS:
GDD explained >92% of length-at-day variance across 9 fish species). They are kept
STRICTLY SEPARATE from the survival envelope (envelopes.py) because a plain GDD sum
breaks down near thermal extremes -- the upper-lethal limits and hypoxia are handled
by the suitability envelope, not by degree-days.
"""
from __future__ import annotations

import numpy as np


def growing_degree_days(temp_daily, base_C, upper_C=None):
    """Accumulate growing degree-days: cumulative sum of max(0, Tmean - base_C).

    Parameters
    ----------
    temp_daily : array-like
        Daily mean temperature (deg C), ordered in time.
    base_C : float
        Species base (threshold) temperature below which no development accrues.
    upper_C : float, optional
        Upper cutoff; daily temperature is capped here before differencing
        (a simple way to stop over-counting on very hot days).

    Returns
    -------
    np.ndarray
        Cumulative GDD aligned with ``temp_daily`` (NaNs treated as 0 contribution).
    """
    t = np.asarray(temp_daily, dtype=float)
    if upper_C is not None:
        t = np.minimum(t, float(upper_C))
    contrib = np.clip(t - float(base_C), 0.0, None)
    contrib = np.where(np.isnan(contrib), 0.0, contrib)
    return np.cumsum(contrib)


def days_to_gdd_target(temp_daily, base_C, target_gdd, upper_C=None):
    """Index of the first day on which cumulative GDD reaches ``target_gdd``.

    Returns ``None`` if the target is never reached within the series.
    """
    cum = growing_degree_days(temp_daily, base_C, upper_C=upper_C)
    hits = np.where(cum >= float(target_gdd))[0]
    return int(hits[0]) if hits.size else None
