"""Headline figures for the proof-of-concept.

  plot_factor_curves        - the trapezoidal suitability curve per environmental factor
  plot_hsi_heatmap          - site x time heatmap of HSI (the dynamic "when/where" map)
  plot_stress_with_mortality- HSI time series with observed oyster mortality overlaid

All functions take an output ``path`` and return it (or None on failure).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # headless-safe
import matplotlib.pyplot as plt  # noqa: E402

from ..model.envelopes import trapezoid

_XRANGE = {
    "temp_C": (0, 40),
    "salinity_ppt": (0, 45),
    "DO_mgL": (0, 12),
    "pH": (6.5, 8.5),
}


def plot_factor_curves(species_cfg, path):
    factors = species_cfg["factors"]
    n = len(factors)
    fig, axes = plt.subplots(1, n, figsize=(3.2 * n, 3.0), squeeze=False)
    for ax, (name, bp) in zip(axes[0], factors.items()):
        lo, hi = _XRANGE.get(name, (bp[0], bp[3]))
        x = np.linspace(lo, hi, 400)
        ax.plot(x, trapezoid(x, bp), lw=2)
        ax.set_title(name)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlabel(name)
        ax.set_ylabel("suitability")
    fig.suptitle(f"{species_cfg.get('common_name', 'species')} — factor suitability")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def plot_hsi_heatmap(hsi_df, path, datetime_col="datetime", site_col="site"):
    df = hsi_df.copy()
    if site_col not in df.columns:
        df[site_col] = "all"
    df[datetime_col] = pd.to_datetime(df[datetime_col], errors="coerce")
    df["day"] = df[datetime_col].dt.floor("D")
    pivot = df.pivot_table(index=site_col, columns="day", values="HSI", aggfunc="mean")
    if pivot.empty:
        return None
    fig, ax = plt.subplots(figsize=(11, 2 + 0.5 * len(pivot)))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn",
                   vmin=0, vmax=1, interpolation="nearest")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    xt = np.linspace(0, pivot.shape[1] - 1, min(10, pivot.shape[1])).astype(int)
    ax.set_xticks(xt)
    ax.set_xticklabels([pivot.columns[i].strftime("%Y-%m-%d") for i in xt],
                       rotation=45, ha="right", fontsize=8)
    ax.set_title("Habitat Suitability Index (HSI) — site × time")
    fig.colorbar(im, ax=ax, label="HSI (0 = lethal, 1 = optimal)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def plot_stress_with_mortality(hsi_df, mort_df, path,
                               datetime_col="datetime", site_col="site",
                               mort_date_col="Date", mort_resp_col="MortalityRate"):
    h = hsi_df.copy()
    if site_col not in h.columns:
        h[site_col] = "all"
    h[datetime_col] = pd.to_datetime(h[datetime_col], errors="coerce")
    m = mort_df.copy()
    m[mort_date_col] = pd.to_datetime(m[mort_date_col], errors="coerce", format="mixed")

    sites = [s for s in h[site_col].dropna().unique()]
    sites = sites[:4] or ["all"]
    fig, axes = plt.subplots(len(sites), 1, figsize=(11, 2.6 * len(sites)),
                             squeeze=False, sharex=True)
    for ax, site in zip(axes[:, 0], sites):
        hs = h[h[site_col] == site].sort_values(datetime_col)
        ax.plot(hs[datetime_col], hs["HSI"], color="seagreen", lw=1.2, label="HSI")
        ax.axhspan(0, 0.2, color="red", alpha=0.08)  # stress band
        ax.set_ylim(0, 1.05)
        ax.set_ylabel(f"{site}\nHSI", fontsize=9)
        ms = m[m.get("Site") == site] if "Site" in m.columns else m
        if len(ms) and mort_resp_col in ms.columns:
            ax2 = ax.twinx()
            ax2.scatter(ms[mort_date_col],
                        pd.to_numeric(ms[mort_resp_col], errors="coerce"),
                        color="black", s=14, label="observed mortality")
            ax2.set_ylabel("mortality", fontsize=9)
    axes[0, 0].set_title("Modeled suitability (HSI) vs. observed oyster mortality")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path
