"""Sharpened validation of suitability vs. Program 195 catch.

Adds to the basic per-tow Spearman:
  - AUC of HSI as a presence/absence classifier (rank-based, no sklearn needed)
  - within-year correlation (controls for year-to-year trends / shared confounding)
  - June vs September split (the survey's two seasons)
  - a clean proposal figure: presence rate by HSI decile, per species

Outputs (data/processed/, git-ignored per SEAMAP terms):
  program195_validation_summary.csv
  suitability_validation.png
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr, rankdata

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from treestoseas.io import load_program195                                # noqa: E402
from treestoseas.model.envelopes import factor_suitability, combine_hsi   # noqa: E402

SPECIES = ["blue_crab", "southern_flounder", "atlantic_croaker"]


def auc_rank(scores, labels):
    """AUC of `scores` for binary `labels` via the Mann-Whitney rank identity."""
    scores = np.asarray(scores, float); labels = np.asarray(labels, int)
    n1 = int(labels.sum()); n0 = int((labels == 0).sum())
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(scores)
    return (r[labels == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def tow_table(df, species_key, species_cfg):
    cols = ["COLLECTIONNUMBER", "YEAR", "MONTH", "DEPTHZONE", "LOCATION",
            "EFFORT", "TEMPBOTTOM", "SALINITYBOTTOM", "BDO"]
    tows = df.drop_duplicates("COLLECTIONNUMBER")[cols].copy()
    caught = df[df["species_key"] == species_key].groupby("COLLECTIONNUMBER")["NUMBERTOTAL"].sum()
    tows["NUMBER"] = tows["COLLECTIONNUMBER"].map(caught).fillna(0.0)
    tows = tows[tows["EFFORT"] > 0]
    tows["cpue"] = tows["NUMBER"] / tows["EFFORT"]
    tows["present"] = (tows["NUMBER"] > 0).astype(int)
    vals = {"temp_C": tows["TEMPBOTTOM"].to_numpy(),
            "salinity_ppt": tows["SALINITYBOTTOM"].to_numpy(),
            "DO_mgL": tows["BDO"].to_numpy()}
    scores = factor_suitability(vals, species_cfg["factors"])
    tows["HSI"] = combine_hsi(scores, method="geometric_mean")
    return tows.dropna(subset=["HSI", "cpue"])


def within_year(t):
    rhos = []
    for _, g in t.groupby("YEAR"):
        if len(g) >= 10 and g["HSI"].nunique() > 3 and g["cpue"].nunique() > 3:
            r = spearmanr(g["HSI"], g["cpue"])[0]
            if r == r:
                rhos.append(r)
    if not rhos:
        return np.nan, np.nan, 0
    return float(np.median(rhos)), float(np.mean([r > 0 for r in rhos])), len(rhos)


def season_rho(t, months):
    s = t[t["MONTH"].isin(months)]
    if len(s) < 30:
        return np.nan, len(s)
    return float(spearmanr(s["HSI"], s["cpue"])[0]), len(s)


def main():
    hits = glob.glob(os.path.join(ROOT, "data", "raw", "*Pamlico Sound Survey*ABUNDANCEBIOMASS*.csv"))
    if not hits:
        sys.exit("No Program 195 extract in data/raw/.")
    path = max(hits, key=os.path.getmtime)
    print(f"Loading {os.path.basename(path)}")
    df = load_program195(path)
    species_all = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))

    rows = []
    fig, axes = plt.subplots(1, len(SPECIES), figsize=(4.0 * len(SPECIES), 3.4), squeeze=False)
    for ax, key in zip(axes[0], SPECIES):
        t = tow_table(df, key, species_all[key])
        r_cpue, p_cpue = spearmanr(t["HSI"], t["cpue"])
        r_pres, p_pres = spearmanr(t["HSI"], t["present"])
        auc = auc_rank(t["HSI"], t["present"])
        wy_med, wy_fpos, wy_n = within_year(t)
        jun_r, jun_n = season_rho(t, [5, 6, 7])
        sep_r, sep_n = season_rho(t, [8, 9, 10])
        rows.append({
            "species": key, "n_tows": len(t),
            "rho_HSI_CPUE": round(r_cpue, 3), "p_CPUE": p_cpue,
            "rho_HSI_presence": round(r_pres, 3), "AUC_presence": round(auc, 3),
            "within_year_median_rho": round(wy_med, 3),
            "within_year_frac_positive": round(wy_fpos, 2), "n_years": wy_n,
            "rho_June": round(jun_r, 3), "n_June": jun_n,
            "rho_Sept": round(sep_r, 3), "n_Sept": sep_n,
        })
        # proposal figure: presence rate by HSI decile
        t = t.copy()
        t["bin"] = pd.cut(t["HSI"], np.linspace(0, 1, 11), include_lowest=True)
        pr = t.groupby("bin", observed=True)["present"].mean()
        centers = [iv.mid for iv in pr.index]
        ax.bar(centers, pr.values, width=0.085, color="#2E7D46", alpha=0.85)
        ax.set_title(f"{species_all[key]['common_name']}\nAUC={auc:.2f}, rho={r_cpue:+.2f}")
        ax.set_xlabel("Habitat Suitability Index")
        ax.set_ylabel("fraction of tows present")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    fig.suptitle("Program 195 (1987-2021): physiological suitability vs. observed occurrence")
    fig.tight_layout()
    proc = os.path.join(ROOT, "data", "processed"); os.makedirs(proc, exist_ok=True)
    figpath = os.path.join(proc, "suitability_validation.png")
    fig.savefig(figpath, dpi=140); plt.close(fig)

    summ = pd.DataFrame(rows)
    summ.to_csv(os.path.join(proc, "program195_validation_summary.csv"), index=False)
    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("\n=== Validation summary ===")
    print(summ.to_string(index=False))
    print(f"\nSaved: {figpath}")


if __name__ == "__main__":
    main()
