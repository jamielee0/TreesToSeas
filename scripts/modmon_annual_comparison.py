"""Population-scale (annual) test: does a more-suitable HABITAT YEAR show higher
Program 195 abundance?

This extends the per-tow spatial validation (catch_vs_suitability.py) to the temporal
scale. We drive the calibrated envelopes with the INDEPENDENT ModMon environmental
record (T / salinity / DO), aggregate to annual warm-season (May-Oct) habitat metrics,
and correlate against the Program 195 annual CPUE index for the same years.

This is a deliberately STRINGENT test. Annual abundance is dominated by recruitment,
fishing, and larval supply, not just that year's adult habitat -- so weak or null
same-year correlations are informative, not a failure. We therefore also test a
1-year lag (habitat in year t vs abundance in year t+1) and a "stress exposure" metric.

ModMon caveat: rows are not separated into surface/bottom here, so the bottom-water
hypoxia signal that demersal species feel is diluted (a refinement, not a blocker).

Outputs (data/processed/, git-ignored):
    modmon_annual_summary.csv  -  correlations per species x region x metric
    modmon_annual_timeseries.png
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
WARM_MONTHS = [5, 6, 7, 8, 9, 10]
STRESS = 0.2


def _spear(a, b):
    m = pd.notna(a) & pd.notna(b)
    if m.sum() < 5:
        return np.nan, np.nan, int(m.sum())
    r, p = spearmanr(a[m], b[m])
    return float(r), float(p), int(m.sum())


def annual_habitat(modmon, species_cfg):
    """Annual warm-season habitat metrics for one species from ModMon T/S/DO."""
    vals = {"temp_C": modmon["temp_C"].to_numpy(),
            "salinity_ppt": modmon["salinity_ppt"].to_numpy(),
            "DO_mgL": modmon["DO_mgL"].to_numpy()}
    scores = factor_suitability(vals, species_cfg["factors"])
    m = modmon.copy()
    m["HSI"] = combine_hsi(scores, method="geometric_mean")
    m = m.dropna(subset=["HSI"])
    g = m.groupby("YEAR")["HSI"]
    return pd.DataFrame({
        "YEAR": g.mean().index,
        "mean_HSI": g.mean().to_numpy(),
        "frac_stress": g.apply(lambda s: float((s < STRESS).mean())).to_numpy(),
        "n_env": g.size().to_numpy(),
    })


def main():
    mm = pd.read_csv(os.path.join(ROOT, "data", "raw", "modmon_all_stations.csv"),
                     low_memory=False)
    mm["datetime"] = pd.to_datetime(mm["datetime"], errors="coerce")
    mm = mm.dropna(subset=["datetime"])
    mm["YEAR"] = mm["datetime"].dt.year
    mm = mm[mm["datetime"].dt.month.isin(WARM_MONTHS)]

    p195_path = max(glob.glob(os.path.join(ROOT, "data", "raw",
                    "*Pamlico Sound Survey*ABUNDANCEBIOMASS*.csv")), key=os.path.getmtime)
    df195 = load_program195(p195_path)
    species_all = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))

    regions = {
        "system": (mm, df195),
        "pamlico_sound": (mm[mm["site"].str.startswith("pamlico-sound", na=False)],
                          df195[df195["LOCATION"].str.contains("PAMLICO SOUND", na=False)]),
    }

    rows = []
    ts_store = {}  # for the figure (system region)
    for region, (mm_r, df_r) in regions.items():
        cpue = annual_cpue_index(df_r, value="NUMBERTOTAL")
        for key in SPECIES:
            hab = annual_habitat(mm_r, species_all[key])
            sp = cpue[cpue["species_key"] == key][["YEAR", "cpue"]]
            merged = hab.merge(sp, on="YEAR", how="inner").sort_values("YEAR")
            lag = hab.merge(sp.assign(YEAR=sp["YEAR"] - 1), on="YEAR", how="inner")  # habitat[t] vs cpue[t+1]

            r_mean, p_mean, n = _spear(merged["mean_HSI"], merged["cpue"])
            r_str, p_str, _ = _spear(merged["frac_stress"], merged["cpue"])
            r_lag, p_lag, n_lag = _spear(lag["mean_HSI"], lag["cpue"])
            rows.append({
                "region": region, "species": key, "n_years": n,
                "rho_meanHSI_CPUE": round(r_mean, 3), "p_meanHSI": p_mean,
                "rho_stress_CPUE": round(r_str, 3),
                "rho_meanHSI_CPUE_lag1": round(r_lag, 3), "n_lag": n_lag,
            })
            if region == "system":
                ts_store[key] = merged

    summ = pd.DataFrame(rows)
    proc = os.path.join(ROOT, "data", "processed"); os.makedirs(proc, exist_ok=True)
    summ.to_csv(os.path.join(proc, "modmon_annual_summary.csv"), index=False)

    fig, axes = plt.subplots(len(SPECIES), 1, figsize=(10, 2.5 * len(SPECIES)), squeeze=False, sharex=True)
    for ax, key in zip(axes[:, 0], SPECIES):
        d = ts_store[key]
        ax.plot(d["YEAR"], d["mean_HSI"], color="seagreen", marker="o", ms=3, label="mean HSI (ModMon)")
        ax.set_ylabel("mean HSI", color="seagreen"); ax.set_ylim(0, 1)
        ax2 = ax.twinx()
        ax2.plot(d["YEAR"], d["cpue"], color="#1f5fa6", marker="s", ms=3, label="CPUE (Program 195)")
        ax2.set_ylabel("CPUE", color="#1f5fa6")
        rho = summ[(summ.region == "system") & (summ.species == key)]["rho_meanHSI_CPUE"].iloc[0]
        ax.set_title(f"{species_all[key]['common_name']}  (system rho={rho:+.2f})")
    axes[-1, 0].set_xlabel("Year")
    fig.suptitle("Annual ModMon habitat suitability vs. Program 195 abundance (warm season)")
    fig.tight_layout()
    fig.savefig(os.path.join(proc, "modmon_annual_timeseries.png"), dpi=130)
    plt.close(fig)

    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("=== Annual habitat vs. abundance (Spearman) ===")
    print(summ.to_string(index=False))
    print(f"\nSaved: {os.path.join(proc, 'modmon_annual_summary.csv')}")
    print(f"Saved: {os.path.join(proc, 'modmon_annual_timeseries.png')}")
    print("\nNote: stress~CPUE is expected NEGATIVE (more stress -> less abundance); "
          "mean_HSI~CPUE expected positive. Same-year links are weak by nature "
          "(recruitment/fishing dominate); the lag-1 column probes a recruitment-style delay.")


if __name__ == "__main__":
    main()
