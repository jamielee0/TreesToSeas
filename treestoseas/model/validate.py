"""Validate modeled habitat suitability against OBSERVED oyster biology.

This is the payoff of having Ty's paired dataset: we can test whether a mechanistic
T x S x DO (+pH) stress index actually predicts observed oyster mortality and growth,
rather than only overlaying it against survey windows. The core idea:

    For each census interval (prev_date, date] at a site, accumulate a "stress load"
    from the HSI time series (mean of 1 - HSI, scaled by days). Then test whether
    stress load correlates with the survivorship decrement / mortality observed at
    the end of that interval (Spearman rank correlation -- robust, non-parametric).

A positive, significant rank correlation between accumulated stress and observed
mortality is the proof-of-concept's headline validation result.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from scipy.stats import spearmanr
except Exception:  # scipy optional at import time
    spearmanr = None


def accumulate_stress_between(hsi_df, start, end, site=None,
                              hsi_col="HSI", datetime_col="datetime", site_col="site"):
    """Mean stress (1 - HSI) over the half-open interval (start, end] at a site.

    Returns a dict with ``mean_stress`` (0-1), ``n_obs`` in the window, and
    ``stress_days`` (mean_stress * interval length in days).
    """
    df = hsi_df
    if site is not None and site_col in df.columns:
        df = df[df[site_col] == site]
    mask = (df[datetime_col] > start) & (df[datetime_col] <= end)
    window = df.loc[mask, hsi_col].to_numpy(dtype=float)
    if window.size == 0 or np.all(np.isnan(window)):
        return {"mean_stress": np.nan, "n_obs": 0, "stress_days": np.nan}
    mean_stress = float(np.nanmean(1.0 - window))
    days = max((pd.Timestamp(end) - pd.Timestamp(start)).days, 1)
    return {"mean_stress": mean_stress, "n_obs": int(window.size),
            "stress_days": mean_stress * days}


def validate_against_mortality(hsi_df, mort_df, *,
                               response_col="MortalityRate",
                               site_col="Site", date_col="Date",
                               group_cols=("Site", "Strain", "BagNumber"),
                               hsi_site_col="site", hsi_datetime_col="datetime"):
    """Pair accumulated stress with observed per-census mortality and rank-correlate.

    Parameters
    ----------
    hsi_df : DataFrame
        Output of :func:`suitability_timeseries` (needs ``HSI`` + datetime + site).
    mort_df : DataFrame
        Mortality census data (e.g. ``MortalityContinuous.csv``). Must have a date
        column, a site column, and a numeric ``response_col``.
    response_col : str
        Observed response to predict (e.g. ``MortalityRate`` or a survivorship
        decrement). Higher = worse condition is assumed for the sign check.

    Returns
    -------
    dict
        ``{'spearman_r', 'p_value', 'n_pairs', 'spearman_abs', 'pairs': DataFrame}``.
        ``spearman_abs`` is |r|, used as the Stage-2 transition metric.
    """
    m = mort_df.copy()
    m[date_col] = pd.to_datetime(m[date_col], errors="coerce", format="mixed")
    m = m.dropna(subset=[date_col])

    h = hsi_df.copy()
    h[hsi_datetime_col] = pd.to_datetime(h[hsi_datetime_col], errors="coerce")

    group_cols = [c for c in group_cols if c in m.columns]
    records = []
    for _, grp in m.groupby(group_cols) if group_cols else [("all", m)]:
        grp = grp.sort_values(date_col)
        prev_date = None
        for _, row in grp.iterrows():
            date = row[date_col]
            site = row.get(site_col)
            if prev_date is None:
                # first census: use a 14-day lookback as the interval
                start = date - pd.Timedelta(days=14)
            else:
                start = prev_date
            stress = accumulate_stress_between(
                h, start, date, site=site,
                site_col=hsi_site_col, datetime_col=hsi_datetime_col)
            resp = pd.to_numeric(row.get(response_col), errors="coerce")
            records.append({
                "site": site, "date": date,
                "stress_days": stress["stress_days"],
                "mean_stress": stress["mean_stress"],
                "n_env_obs": stress["n_obs"],
                "response": resp,
            })
            prev_date = date

    pairs = pd.DataFrame(records).dropna(subset=["stress_days", "response"])
    pairs = pairs[pairs["n_env_obs"] > 0]

    result = {"spearman_r": np.nan, "p_value": np.nan,
              "n_pairs": int(len(pairs)), "spearman_abs": np.nan, "pairs": pairs}
    if len(pairs) >= 5 and spearmanr is not None:
        r, p = spearmanr(pairs["stress_days"], pairs["response"])
        result.update(spearman_r=float(r), p_value=float(p),
                      spearman_abs=float(abs(r)))
    return result
