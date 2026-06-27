"""Honest decomposition of the headline spatial validation (Program 195).

Added 2026-06-27 during the Stage 2.5/3 integrity+review pass. The pooled per-tow
Spearman rho reported originally (croaker +0.20, blue crab +0.18, flounder +0.14 over
4,312 tows) BLENDS two eras: bottom dissolved oxygen is missing from ~39% of tows
(every pre-1996 tow), and the geometric-mean combiner (np.nanmean over log-suitability)
averages over whatever factors are present -- so DO-less tows contribute a 2-factor
(temp+salinity) HSI. That inflates the croaker/blue-crab pooled numbers (a Simpson's
paradox). This script quantifies the honest picture per species:

    - pooled rho (all tows with a defined HSI)
    - complete-case rho (only tows that actually measured bottom DO)
    - raw bottom-temperature baseline rho (does a thermometer alone do as well?)
    - HSI~temperature rho (is the HSI just a temperature relabeling?)
    - partial rho(HSI ~ CPUE | bottom temperature) (does the envelope add skill over temp?)

Reading: southern flounder is the clean, load-bearing multi-axis case (salinity-driven,
temperature-independent, survives partialling temperature); croaker is a weak
temperature-shaped preference; blue crab is plateau-flat (kept as a labeled tolerance
layer, not an occurrence predictor).

Output (data/processed/, git-ignored per SEAMAP terms):
    headline_decomposition.csv
Run: python scripts/headline_decomposition.py
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd
import yaml
from scipy.stats import rankdata, spearmanr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from treestoseas.io import load_program195                                   # noqa: E402
from treestoseas.model.envelopes import combine_hsi, factor_suitability      # noqa: E402

SPECIES = ["blue_crab", "southern_flounder", "atlantic_croaker"]


def partial_spearman(a, b, c):
    """First-order Spearman partial correlation of a,b controlling for c."""
    ra, rb, rc = rankdata(a), rankdata(b), rankdata(c)
    rab = np.corrcoef(ra, rb)[0, 1]
    rac = np.corrcoef(ra, rc)[0, 1]
    rbc = np.corrcoef(rb, rc)[0, 1]
    return (rab - rac * rbc) / np.sqrt((1 - rac ** 2) * (1 - rbc ** 2))


def find_extract():
    hits = glob.glob(os.path.join(ROOT, "data", "raw", "*Pamlico Sound Survey*ABUNDANCEBIOMASS*.csv"))
    if not hits:
        sys.exit("No Program 195 extract found in data/raw/.")
    return max(hits, key=os.path.getmtime)


def main():
    path = find_extract()
    print(f"Loading {os.path.basename(path)}")
    df = load_program195(path)
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))

    tows = (df.drop_duplicates("COLLECTIONNUMBER")
              [["COLLECTIONNUMBER", "YEAR", "EFFORT", "TEMPBOTTOM", "SALINITYBOTTOM", "BDO"]]
              .copy())
    tows = tows[tows["EFFORT"] > 0]

    n = len(tows)
    miss = tows["BDO"].isna().mean()
    pre96_miss = tows.loc[tows["YEAR"] < 1996, "BDO"].isna().mean()
    print(f"\ntows (EFFORT>0): {n}")
    print(f"bottom-DO missing: {100 * miss:.1f}%   (pre-1996 missing: {100 * pre96_miss:.1f}%)")

    print(f"\n{'species':18s} {'n_all':>6s} {'rho_all':>8s} {'n_cc':>6s} {'rho_cc':>8s} "
          f"{'rho_temp':>9s} {'rho_HSI~T':>10s} {'partial':>8s}")
    rows = []
    for key in SPECIES:
        caught = df[df["species_key"] == key].groupby("COLLECTIONNUMBER")["NUMBERTOTAL"].sum()
        t = tows.copy()
        t["NUMBER"] = t["COLLECTIONNUMBER"].map(caught).fillna(0.0)
        t["cpue"] = t["NUMBER"] / t["EFFORT"]
        vals = {"temp_C": t["TEMPBOTTOM"].to_numpy(),
                "salinity_ppt": t["SALINITYBOTTOM"].to_numpy(),
                "DO_mgL": t["BDO"].to_numpy()}
        t["HSI"] = combine_hsi(factor_suitability(vals, cfg[key]["factors"]), method="geometric_mean")
        t = t.dropna(subset=["HSI", "cpue"])

        r_all, _ = spearmanr(t["HSI"], t["cpue"])
        cc = t[t["BDO"].notna() & t["TEMPBOTTOM"].notna()]
        r_cc, _ = spearmanr(cc["HSI"], cc["cpue"])
        r_temp, _ = spearmanr(cc["TEMPBOTTOM"], cc["cpue"])
        r_hsi_t, _ = spearmanr(cc["HSI"], cc["TEMPBOTTOM"])
        pr = partial_spearman(cc["HSI"].values, cc["cpue"].values, cc["TEMPBOTTOM"].values)

        rows.append(dict(species=key, n_all=len(t), rho_all=r_all, n_cc=len(cc),
                         rho_complete_case=r_cc, rho_raw_temp=r_temp,
                         rho_hsi_vs_temp=r_hsi_t, partial_hsi_given_temp=pr))
        print(f"{key:18s} {len(t):6d} {r_all:+8.3f} {len(cc):6d} {r_cc:+8.3f} "
              f"{r_temp:+9.3f} {r_hsi_t:+10.3f} {pr:+8.3f}")

    proc = os.path.join(ROOT, "data", "processed")
    os.makedirs(proc, exist_ok=True)
    out = os.path.join(proc, "headline_decomposition.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\nSaved: {out}")
    print("\nReading: flounder is the clean multi-axis case (rho stable, temp-independent, "
          "survives partialling temp); croaker is a weak temperature-shaped preference; "
          "blue crab is plateau-flat (raw temperature does as well or better).")


if __name__ == "__main__":
    main()
