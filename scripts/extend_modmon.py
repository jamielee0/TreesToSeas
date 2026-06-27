"""Extend the flagship Neuse bottom-hypoxia result to 2026 using the new ModMon sonde data.

Combines the public ERDDAP ModMon record (1994-2021; bottom = deepest z per cast) with
the Paerl-Lab post-2021 sonde files (2022-2026; explicit 'B' = bottom label) into a
continuous 32-year Neuse bottom-water DO series, then:
  - tests whether the summer bottom-water hypoxia persists in the most recent years;
  - fits a 1994-2026 trend in summer (Jun-Sep) bottom-hypoxia frequency;
  - compares the historical (1994-2021) vs recent (2022-2026) monthly climatology.

Outputs (data/processed/): modmon_extended_summary.csv, modmon_extended_trend.png
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from treestoseas.io.modmon_excel import load_modmon_excel  # noqa: E402

HYPOXIA = 2.0
WARM = [6, 7, 8, 9]


def historical_neuse_bottom():
    """Neuse bottom-water DO per cast from the ERDDAP record (1994-2021)."""
    mm = pd.read_csv(os.path.join(ROOT, "data", "raw", "modmon_all_stations.csv"), low_memory=False)
    mm = mm[mm["site"].str.startswith("neuse-river", na=False)].copy()
    mm["datetime"] = pd.to_datetime(mm["datetime"], errors="coerce")
    mm = mm.dropna(subset=["datetime", "z", "DO_mgL"])
    bott = mm.loc[mm.groupby(["site", "datetime"])["z"].idxmin()]   # deepest = bottom
    return pd.DataFrame({"year": bott["datetime"].dt.year, "month": bott["datetime"].dt.month,
                         "DO_mgL": bott["DO_mgL"].to_numpy(), "source": "ERDDAP 1994-2021"})


def recent_neuse_bottom():
    """Neuse bottom-water DO per cast from the new sonde Excel (2022-2026)."""
    nr = load_modmon_excel(os.path.join(ROOT, "data", "raw", "modmon_NR_2022_2026.xlsx"), "NR")
    b = nr[(nr["layer"] == "bottom")].dropna(subset=["DO_mgL"])
    return pd.DataFrame({"year": b["year"], "month": b["month"],
                         "DO_mgL": b["DO_mgL"].to_numpy(), "source": "Sonde 2022-2026"})


def main():
    allb = pd.concat([historical_neuse_bottom(), recent_neuse_bottom()], ignore_index=True)
    allb["hypoxic"] = (allb["DO_mgL"] < HYPOXIA).astype(float)
    warm = allb[allb["month"].isin(WARM)]

    # annual summer bottom-hypoxia fraction (require Jul & Aug coverage + >=10 casts,
    # so partial years like 2026-through-June don't enter the full-summer trend)
    g = warm.groupby("year")
    months_by_year = warm.groupby("year")["month"].agg(lambda s: set(s))
    ann = g.agg(n=("hypoxic", "size"), pct_hypoxic=("hypoxic", "mean"),
                median_DO=("DO_mgL", "median")).reset_index()
    ann["full_summer"] = ann["year"].map(lambda y: {7, 8} <= months_by_year.get(y, set()))
    ann = ann[(ann["n"] >= 10) & ann["full_summer"]].drop(columns="full_summer")
    ann["pct_hypoxic"] *= 100

    # trend over the well-sampled years
    m, b = np.polyfit(ann["year"], ann["pct_hypoxic"], 1)

    # monthly climatology: historical vs recent
    def monthly(src):
        s = allb[(allb["source"] == src) & (allb["month"].isin(WARM))]
        return s.groupby("month")["hypoxic"].mean().reindex(WARM) * 100
    hist = monthly("ERDDAP 1994-2021"); rec = monthly("Sonde 2022-2026")

    proc = os.path.join(ROOT, "data", "processed"); os.makedirs(proc, exist_ok=True)
    ann.to_csv(os.path.join(proc, "modmon_extended_summary.csv"), index=False)

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12, 4.4))
    col = np.where(ann["year"] <= 2021, "#0d3b66", "#c0392b")
    axA.scatter(ann["year"], ann["pct_hypoxic"], c=col, zorder=5)
    axA.plot(ann["year"], m * ann["year"] + b, color="gray", lw=1.5)
    axA.set_ylabel("% of summer Neuse bottom casts hypoxic (DO<2)")
    axA.set_xlabel("year")
    axA.set_title(f"Summer Neuse bottom hypoxia, 1994–2026 (red = new sonde data)\n"
                  f"trend {m*10:+.1f} %/decade")
    x = np.arange(len(WARM)); w = 0.38
    axB.bar(x - w/2, hist.values, w, label="1994–2021", color="#0d3b66")
    axB.bar(x + w/2, rec.values, w, label="2022–2026", color="#c0392b")
    axB.set_xticks(x); axB.set_xticklabels(["Jun", "Jul", "Aug", "Sep"])
    axB.set_ylabel("% bottom casts hypoxic"); axB.legend()
    axB.set_title("Monthly bottom hypoxia: historical vs recent")
    fig.tight_layout(); fig.savefig(os.path.join(proc, "modmon_extended_trend.png"), dpi=140); plt.close(fig)

    recent_years = ann[ann["year"] >= 2022]
    print("=== Neuse summer bottom hypoxia extended to 2026 ===")
    print(f"Coverage: {int(allb.year.min())}–{int(allb.year.max())}; "
          f"{len(allb)} bottom casts ({len(recent_neuse_bottom())} new).")
    print(f"Historical (<=2021) mean summer hypoxia: {ann[ann.year<=2021]['pct_hypoxic'].mean():.0f}%")
    print(f"Recent (2022-2026) summer hypoxia by year:")
    print(recent_years[["year", "n", "pct_hypoxic", "median_DO"]].to_string(index=False))
    print(f"Trend 1994-2026: {m*10:+.1f} %/decade")
    print(f"\nSaved: modmon_extended_summary.csv, modmon_extended_trend.png")


if __name__ == "__main__":
    main()
