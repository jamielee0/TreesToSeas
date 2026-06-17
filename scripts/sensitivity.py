"""Sensitivity / robustness of the headline Program 195 validation to envelope uncertainty.

Many tolerance breakpoints are TRANSFERRED (Chesapeake/Gulf/lab), so the fair question is:
does the positive "suitability predicts catch" signal survive perturbing the thresholds?

We Monte-Carlo perturb every meaningful breakpoint by +/-15% (keeping each envelope
monotonic), recompute the per-tow HSI from the survey's own bottom T/S/DO, and recompute
Spearman(HSI, CPUE) per species. If the signal is robust, the perturbed distribution of
rho stays positive and significant.

Outputs (data/processed/): sensitivity_summary.csv, sensitivity.png
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from treestoseas.io import load_program195                                # noqa: E402
from treestoseas.model.envelopes import factor_suitability, combine_hsi   # noqa: E402

SPECIES = ["blue_crab", "southern_flounder", "atlantic_croaker"]
N_MC = 300
FRAC = 0.15
rng = np.random.default_rng(42)


def perturb(bp):
    """Perturb 4 breakpoints by +/-FRAC, then sort to stay monotonic. Huge one-sided caps kept."""
    bp = np.array(bp, float)
    out = bp * (1 + rng.uniform(-FRAC, FRAC, size=bp.shape))
    out[bp >= 1000] = bp[bp >= 1000]   # keep one-sided plateau caps fixed
    return np.sort(out)


def tow_tables(df):
    tables = {}
    for key in SPECIES:
        tows = (df.drop_duplicates("COLLECTIONNUMBER")
                  [["COLLECTIONNUMBER", "EFFORT", "TEMPBOTTOM", "SALINITYBOTTOM", "BDO"]].copy())
        caught = df[df["species_key"] == key].groupby("COLLECTIONNUMBER")["NUMBERTOTAL"].sum()
        tows["NUMBER"] = tows["COLLECTIONNUMBER"].map(caught).fillna(0.0)
        tows = tows[tows["EFFORT"] > 0]
        tows["cpue"] = tows["NUMBER"] / tows["EFFORT"]
        tables[key] = tows
    return tables


def rho_for(tows, factors):
    vals = {"temp_C": tows["TEMPBOTTOM"].to_numpy(), "salinity_ppt": tows["SALINITYBOTTOM"].to_numpy(),
            "DO_mgL": tows["BDO"].to_numpy()}
    hsi = combine_hsi(factor_suitability(vals, factors), "geometric_mean")
    m = pd.notna(hsi) & tows["cpue"].notna()
    if m.sum() < 20:
        return np.nan, np.nan
    r, p = spearmanr(hsi[m], tows["cpue"].to_numpy()[m])
    return r, p


def main():
    path = max(glob.glob(os.path.join(ROOT, "data", "raw", "*Pamlico Sound Survey*ABUNDANCEBIOMASS*.csv")),
               key=os.path.getmtime)
    df = load_program195(path)
    species_all = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))
    tables = tow_tables(df)

    rows = []
    dist = {}
    for key in SPECIES:
        base_factors = species_all[key]["factors"]
        r0, p0 = rho_for(tables[key], base_factors)
        rs = []
        for _ in range(N_MC):
            pf = {f: list(perturb(bp)) for f, bp in base_factors.items() if f in ("temp_C", "salinity_ppt", "DO_mgL")}
            r, _ = rho_for(tables[key], pf)
            if r == r:
                rs.append(r)
        rs = np.array(rs)
        dist[key] = rs
        rows.append({
            "species": key, "baseline_rho": round(float(r0), 3),
            "perturbed_median_rho": round(float(np.median(rs)), 3),
            "perturbed_p05": round(float(np.percentile(rs, 5)), 3),
            "perturbed_p95": round(float(np.percentile(rs, 95)), 3),
            "frac_positive": round(float((rs > 0).mean()), 3),
        })

    summ = pd.DataFrame(rows)
    proc = os.path.join(ROOT, "data", "processed"); os.makedirs(proc, exist_ok=True)
    summ.to_csv(os.path.join(proc, "sensitivity_summary.csv"), index=False)

    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.boxplot([dist[k] for k in SPECIES], showfliers=False)
    ax.set_xticks(range(1, len(SPECIES) + 1))
    ax.set_xticklabels([species_all[k]["common_name"] for k in SPECIES])
    for i, k in enumerate(SPECIES, 1):
        ax.scatter([i], [summ[summ.species == k]["baseline_rho"].iloc[0]], color="red", zorder=5, label="baseline" if i == 1 else None)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("Spearman rho (HSI vs CPUE)")
    ax.set_title(f"Robustness to +/-{int(FRAC*100)}% envelope perturbation ({N_MC} draws)\n"
                 "boxes = perturbed distribution; red = baseline")
    ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(proc, "sensitivity.png"), dpi=140); plt.close(fig)

    pd.set_option("display.width", 160)
    print(f"=== Envelope-uncertainty robustness ({N_MC} perturbations, +/-{int(FRAC*100)}%) ===")
    print(summ.to_string(index=False))
    print(f"\nSaved: sensitivity_summary.csv, sensitivity.png")


if __name__ == "__main__":
    main()
