"""Degree-day phenology — when does the activity/spawning window open?

Degree-days predict TIMING (kept separate from the survival envelope). Panel A shows
the method on one high-resolution season (CMAST 2024): growing degree-days accumulate
above the oyster spawning base (20 C) and the window opens when water sustains >=20 C.
Panel B uses the continuous NOAA Beaufort record (2000-2025) to show the interannual
spawning-window opening date and whether it is trending earlier (warming).

Honest caveat: base temperatures are literature values; GDD-to-event TARGETS are not
NC-validated, so we report the thermal-threshold window opening (a robust phenology
proxy), not a precise spawning date. Degree-days are well-supported for pre-maturation
timing (Neuheimer & Taggart 2007).

Outputs (data/processed/): phenology_summary.csv, phenology.png
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import yaml

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from treestoseas.io.ty_oysterdata import load_env_site_file        # noqa: E402
from treestoseas.model.degree_days import growing_degree_days      # noqa: E402

BASE = 20.0  # eastern oyster spawning threshold (deg C)


def window_open_doy(daily_temp, base=BASE, win=7):
    """First day-of-year where the `win`-day rolling mean daily temp first reaches base."""
    roll = daily_temp.rolling(win, min_periods=win).mean()
    hit = roll[roll >= base]
    return int(hit.index[0].dayofyear) if len(hit) else np.nan


def main():
    species = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))
    base = species["eastern_oyster"]["degree_days"]["base_C"]

    # Panel A: method demo on CMAST 2024 daily temperature
    cm = load_env_site_file(os.path.join(ROOT, "data", "raw", "AverageCMASTtemp.csv"), site_fallback="CMAST")
    daily = cm.set_index("datetime")["temp_C"].resample("1D").mean()
    gdd = growing_degree_days(daily.values, base_C=base)
    open_doy_2024 = window_open_doy(daily, base)

    # Panel B: interannual window-opening from continuous NOAA Beaufort temp (2000-2025)
    rows = []
    npath = os.path.join(ROOT, "data", "raw", "noaa_beaufort_8656483_water_temp.csv")
    if os.path.exists(npath):
        nb = pd.read_csv(npath)
        nb["datetime"] = pd.to_datetime(nb["datetime"], errors="coerce")
        nb = nb.dropna(subset=["datetime", "temp_C"])
        for yr, g in nb.groupby(nb["datetime"].dt.year):
            d = g.set_index("datetime")["temp_C"].resample("1D").mean()
            doy = window_open_doy(d, base)
            if not np.isnan(doy) and d.notna().sum() > 200:   # require decent annual coverage
                rows.append({"year": int(yr), "open_doy": doy})
    pheno = pd.DataFrame(rows)

    proc = os.path.join(ROOT, "data", "processed"); os.makedirs(proc, exist_ok=True)
    pheno.to_csv(os.path.join(proc, "phenology_summary.csv"), index=False)

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11, 4.2))
    # Panel A
    axA.plot(daily.index, daily.values, color="#b06000", lw=1, label="daily temp")
    axA.axhline(base, color="red", ls=":", lw=1)
    axA.set_ylabel("temp (°C)", color="#b06000")
    axA2 = axA.twinx()
    axA2.plot(daily.index, gdd, color="seagreen", lw=1.6, label="accumulated GDD")
    axA2.set_ylabel("growing degree-days (base 20°C)", color="seagreen")
    if not np.isnan(open_doy_2024):
        od = daily.index[daily.index.dayofyear == open_doy_2024]
        if len(od):
            axA.axvline(od[0], color="navy", ls="--", lw=1)
            axA.annotate(f"window opens\nday {open_doy_2024}", (od[0], base + 1), color="navy", fontsize=8)
    axA.set_title("Method: GDD accumulation, CMAST 2024 (oyster, base 20°C)")

    # Panel B
    if len(pheno) >= 5:
        axB.scatter(pheno["year"], pheno["open_doy"], color="seagreen", zorder=5)
        m, b = np.polyfit(pheno["year"], pheno["open_doy"], 1)
        axB.plot(pheno["year"], m * pheno["year"] + b, color="navy", lw=1.5)
        axB.set_ylabel("day-of-year window opens (≥20°C)")
        axB.set_xlabel("year")
        axB.set_title(f"Interannual spawning-window opening, Beaufort 2000–2025\n"
                      f"trend {m*10:+.1f} days/decade (− = earlier)")
        slope = m * 10
    else:
        axB.text(0.5, 0.5, "insufficient NOAA coverage", ha="center")
        slope = np.nan
    fig.tight_layout(); fig.savefig(os.path.join(proc, "phenology.png"), dpi=140); plt.close(fig)

    print("=== Degree-day phenology (oyster spawning window, base 20°C) ===")
    print(f"CMAST 2024: window opens day-of-year {open_doy_2024}; season-total GDD {gdd[-1]:.0f}")
    if len(pheno) >= 5:
        print(f"Beaufort {pheno.year.min()}–{pheno.year.max()}: mean opening DOY "
              f"{pheno.open_doy.mean():.0f} (±{pheno.open_doy.std():.0f}); trend {slope:+.1f} days/decade")
    print("Saved: phenology_summary.csv, phenology.png")


if __name__ == "__main__":
    main()
