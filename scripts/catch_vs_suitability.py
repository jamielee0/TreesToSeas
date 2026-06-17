"""Catch-vs-suitability comparison for NC Program 195 (Pamlico Sound Survey).

The optional validation the proposal flagged: the survey records each tow's own
bottom temperature, salinity, and dissolved oxygen. So we can test the core thesis
DIRECTLY and self-contained — does the calibrated physiological suitability index
(from config/species.yaml) predict where each species is actually caught?

For every tow we compute HSI from its bottom T/S/DO, set CPUE = NUMBERTOTAL/EFFORT
(0 where the species was absent), and rank-correlate HSI with CPUE and with presence.
A positive Spearman rho supports the suitability model.

Outputs (data/processed/, git-ignored per SEAMAP terms):
    program195_annual_cpue.csv     - annual CPUE index per species
    catch_vs_suitability.png       - binned mean CPUE vs HSI, per species
Run: python scripts/catch_vs_suitability.py
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

from treestoseas.io import load_program195, annual_cpue_index            # noqa: E402
from treestoseas.model.envelopes import factor_suitability, combine_hsi  # noqa: E402

SPECIES = ["blue_crab", "southern_flounder", "atlantic_croaker"]


def find_extract():
    hits = glob.glob(os.path.join(ROOT, "data", "raw", "*Pamlico Sound Survey*ABUNDANCEBIOMASS*.csv"))
    if not hits:
        sys.exit("No Program 195 extract found in data/raw/ (Pamlico Sound Survey ABUNDANCEBIOMASS csv).")
    return max(hits, key=os.path.getmtime)


def tow_table(df, species_key, species_cfg):
    """All tows with bottom env + this species' CPUE + HSI from the tow's own conditions."""
    tows = (df.drop_duplicates("COLLECTIONNUMBER")
              [["COLLECTIONNUMBER", "YEAR", "EFFORT", "TEMPBOTTOM", "SALINITYBOTTOM", "BDO"]]
              .copy())
    caught = df[df["species_key"] == species_key].groupby("COLLECTIONNUMBER")["NUMBERTOTAL"].sum()
    tows["NUMBER"] = tows["COLLECTIONNUMBER"].map(caught).fillna(0.0)
    tows = tows[tows["EFFORT"] > 0]
    tows["cpue"] = tows["NUMBER"] / tows["EFFORT"]

    vals = {"temp_C": tows["TEMPBOTTOM"].to_numpy(),
            "salinity_ppt": tows["SALINITYBOTTOM"].to_numpy(),
            "DO_mgL": tows["BDO"].to_numpy()}
    scores = factor_suitability(vals, species_cfg["factors"])
    tows["HSI"] = combine_hsi(scores, method="geometric_mean")
    return tows.dropna(subset=["HSI", "cpue"])


def main():
    path = find_extract()
    print(f"Loading {os.path.basename(path)}")
    df = load_program195(path)
    species_all = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))

    proc = os.path.join(ROOT, "data", "processed")
    os.makedirs(proc, exist_ok=True)
    idx = annual_cpue_index(df, value="NUMBERTOTAL")
    idx.to_csv(os.path.join(proc, "program195_annual_cpue.csv"), index=False)

    fig, axes = plt.subplots(1, len(SPECIES), figsize=(4.2 * len(SPECIES), 3.6), squeeze=False)
    print("\n=== Per-tow: does HSI predict catch? (Spearman) ===")
    summary = []
    for ax, key in zip(axes[0], SPECIES):
        t = tow_table(df, key, species_all[key])
        r_cpue, p_cpue = spearmanr(t["HSI"], t["cpue"])
        r_pres, p_pres = spearmanr(t["HSI"], (t["NUMBER"] > 0).astype(int))
        summary.append((key, len(t), r_cpue, p_cpue, r_pres, p_pres))
        print(f"  {key:18s} n={len(t):5d}  HSI~CPUE rho={r_cpue:+.3f} (p={p_cpue:.1e})  "
              f"HSI~presence rho={r_pres:+.3f} (p={p_pres:.1e})")

        # binned mean CPUE by HSI decile (visual)
        t = t.copy()
        t["hsi_bin"] = pd.cut(t["HSI"], bins=np.linspace(0, 1, 11), include_lowest=True)
        binned = t.groupby("hsi_bin", observed=True)["cpue"].mean()
        centers = [iv.mid for iv in binned.index]
        ax.bar(centers, binned.values, width=0.08, color="seagreen", alpha=0.8)
        ax.set_title(f"{species_all[key]['common_name']}\nHSI~CPUE rho={r_cpue:+.2f}")
        ax.set_xlabel("Habitat Suitability Index (from tow's own T/S/DO)")
        ax.set_ylabel("mean CPUE (n / effort)")
        ax.set_xlim(0, 1)
    fig.suptitle("Program 195: modeled suitability vs. observed catch (per tow)")
    fig.tight_layout()
    figpath = os.path.join(proc, "catch_vs_suitability.png")
    fig.savefig(figpath, dpi=130)
    plt.close(fig)

    print(f"\nSaved: {os.path.join(proc, 'program195_annual_cpue.csv')}")
    print(f"Saved: {figpath}")
    print("\nInterpretation: positive rho = animals are caught where conditions are more "
          "suitable. HSI here uses bottom T/S/DO and the calibrated envelopes (no pH at tows).")


if __name__ == "__main__":
    main()
