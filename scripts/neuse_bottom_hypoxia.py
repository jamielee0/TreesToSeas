"""Neuse bottom-water hypoxia (depth-resolved ModMon) -- the survey-matched squeeze.

ModMon casts are vertical profiles, so we can separate SURFACE (shallowest z) from
BOTTOM (deepest z) per cast. Demersal/benthic species (flounder, croaker, crab, oyster)
live in the bottom water, where summer stratification drives hypoxia that the surface --
and a twice-yearly daytime survey -- does not see.

This is the public, survey-matched (Neuse-Pamlico) evidence for the proposal's central
"squeeze" claim, using ModMon 1994-2021.

Outputs (data/processed/): neuse_bottom_hypoxia_summary.csv, neuse_bottom_hypoxia.png
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

from treestoseas.model.envelopes import factor_suitability, combine_hsi  # noqa: E402

HYPOXIA = 2.0
WARM = [6, 7, 8, 9]
SURVEY = [6, 9]


def main():
    mm = pd.read_csv(os.path.join(ROOT, "data", "raw", "modmon_all_stations.csv"), low_memory=False)
    mm = mm[mm["site"].str.startswith("neuse-river", na=False)].copy()
    mm["datetime"] = pd.to_datetime(mm["datetime"], errors="coerce")
    mm = mm.dropna(subset=["datetime", "z", "DO_mgL"])
    mm["month"] = mm["datetime"].dt.month

    # surface = shallowest (max z, since z is negative); bottom = deepest (min z)
    grp = mm.groupby(["site", "datetime"])
    surf = mm.loc[grp["z"].idxmax()].add_prefix("surf_")
    bott = mm.loc[grp["z"].idxmin()].add_prefix("bot_")
    cast = pd.concat([surf.reset_index(drop=True), bott.reset_index(drop=True)], axis=1)
    cast["month"] = cast["surf_month"]
    cast["bot_depth_m"] = -cast["bot_z"]

    species = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))
    cr = species["atlantic_croaker"]["factors"]
    for layer in ("surf", "bot"):
        sc = factor_suitability({"temp_C": cast[f"{layer}_temp_C"].to_numpy(),
                                 "salinity_ppt": cast[f"{layer}_salinity_ppt"].to_numpy(),
                                 "DO_mgL": cast[f"{layer}_DO_mgL"].to_numpy()}, cr)
        cast[f"{layer}_HSI_croaker"] = combine_hsi(sc, "geometric_mean")

    warm = cast[cast["month"].isin(WARM)]
    rows = []
    for m in WARM:
        c = cast[cast["month"] == m]
        rows.append({"month": m, "n_casts": len(c),
                     "pct_surface_hypoxic": round(100 * float((c["surf_DO_mgL"] < HYPOXIA).mean()), 1),
                     "pct_bottom_hypoxic": round(100 * float((c["bot_DO_mgL"] < HYPOXIA).mean()), 1),
                     "median_bottom_DO": round(float(c["bot_DO_mgL"].median()), 2),
                     "median_croaker_bottom_HSI": round(float(c["bot_HSI_croaker"].median()), 2)})
    summ = pd.DataFrame(rows)

    proc = os.path.join(ROOT, "data", "processed"); os.makedirs(proc, exist_ok=True)
    summ.to_csv(os.path.join(proc, "neuse_bottom_hypoxia_summary.csv"), index=False)

    # headline stats
    surv = cast[cast["month"].isin(SURVEY)]; gap = cast[cast["month"].isin([7, 8])]
    pct_bot_warm = 100 * float((warm["bot_DO_mgL"] < HYPOXIA).mean())
    pct_surf_warm = 100 * float((warm["surf_DO_mgL"] < HYPOXIA).mean())
    pct_bot_survey = 100 * float((surv["bot_DO_mgL"] < HYPOXIA).mean())
    pct_bot_gap = 100 * float((gap["bot_DO_mgL"] < HYPOXIA).mean())

    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = np.arange(len(summ)); w = 0.38
    ax.bar(x - w/2, summ["pct_surface_hypoxic"], w, label="surface", color="#7fb3d5")
    ax.bar(x + w/2, summ["pct_bottom_hypoxic"], w, label="bottom", color="#0d3b66")
    ax.set_xticks(x); ax.set_xticklabels(["Jun", "Jul", "Aug", "Sep"])
    for i, m in enumerate(summ["month"]):
        if m in SURVEY:
            ax.annotate("survey", (i, -6), ha="center", color="darkorange", fontsize=8, annotation_clip=False)
    ax.set_ylabel("% of Neuse profiles hypoxic (DO < 2 mg/L)")
    ax.set_title(f"Neuse bottom-water hypoxia peaks in Jul-Aug, between the survey visits\n"
                 f"warm-season bottom {pct_bot_warm:.0f}% vs surface {pct_surf_warm:.0f}%; "
                 f"Jul-Aug bottom {pct_bot_gap:.0f}% vs survey-months {pct_bot_survey:.0f}%")
    ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(proc, "neuse_bottom_hypoxia.png"), dpi=140); plt.close(fig)

    print("=== Neuse bottom vs surface hypoxia (depth-resolved ModMon, 1994-2021) ===")
    print(summ.to_string(index=False))
    print(f"\nWarm-season hypoxia (DO<2): BOTTOM {pct_bot_warm:.1f}% of profiles vs SURFACE {pct_surf_warm:.1f}%.")
    print(f"Bottom hypoxia in Jul-Aug (between surveys) {pct_bot_gap:.1f}% vs survey months Jun+Sep {pct_bot_survey:.1f}%.")
    print(f"\nSaved: neuse_bottom_hypoxia_summary.csv, neuse_bottom_hypoxia.png")


if __name__ == "__main__":
    main()
