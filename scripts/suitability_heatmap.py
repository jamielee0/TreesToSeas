"""Dynamic when/where suitability map (the proposal's Stage-3 headline figure).

Bottom- vs surface-water croaker Habitat Suitability Index across the Neuse River axis
(ModMon stations ordered upstream->downstream) by month-of-year (1994-2021 climatology).
This is the "when and where is a species inside vs. outside its survivable range" map:
the surface stays green year-round, but the bottom collapses (red) through the mid/lower
estuary in summer -- the squeeze, resolved in space and season.

Outputs (data/processed/): suitability_heatmap.png
"""
from __future__ import annotations

import os
import re
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


def main():
    mm = pd.read_csv(os.path.join(ROOT, "data", "raw", "modmon_all_stations.csv"), low_memory=False)
    mm = mm[mm["site"].str.startswith("neuse-river", na=False)].copy()
    mm["datetime"] = pd.to_datetime(mm["datetime"], errors="coerce")
    mm = mm.dropna(subset=["datetime", "z", "DO_mgL", "temp_C", "salinity_ppt"])
    mm["month"] = mm["datetime"].dt.month
    mm["modmon"] = mm["title"].str.extract(r"ModMon (\d+)").astype(float)
    mm = mm.dropna(subset=["modmon"])

    # surface = shallowest (max z); bottom = deepest (min z) per cast
    grp = mm.groupby(["site", "datetime"])
    surf = mm.loc[grp["z"].idxmax()].copy(); surf["layer"] = "surface"
    bott = mm.loc[grp["z"].idxmin()].copy(); bott["layer"] = "bottom"
    both = pd.concat([surf, bott], ignore_index=True)

    cr = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))["atlantic_croaker"]["factors"]
    sc = factor_suitability({"temp_C": both["temp_C"].to_numpy(), "salinity_ppt": both["salinity_ppt"].to_numpy(),
                             "DO_mgL": both["DO_mgL"].to_numpy()}, cr)
    both["HSI"] = combine_hsi(sc, "geometric_mean")
    both = both.dropna(subset=["HSI"])

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    im = None
    for ax, layer in zip(axes, ["surface", "bottom"]):
        sub = both[both["layer"] == layer]
        piv = sub.pivot_table(index="modmon", columns="month", values="HSI", aggfunc="median")
        piv = piv.reindex(columns=range(1, 13)).sort_index(ascending=True)
        im = ax.imshow(piv.values, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1,
                       interpolation="nearest")
        ax.set_xticks(range(12)); ax.set_xticklabels(list("JFMAMJJASOND"))
        ax.set_yticks(range(len(piv.index)))
        ax.set_yticklabels([f"MM{int(v)}" for v in piv.index], fontsize=7)
        ax.set_title(f"{layer.capitalize()} water")
        ax.set_xlabel("month")
    axes[0].set_ylabel("Neuse station (ModMon km: 0 upstream → 180 downstream)")
    fig.colorbar(im, ax=axes, label="croaker HSI (0 = unsuitable, 1 = optimal)", fraction=0.046, pad=0.04)
    fig.suptitle("When/where the bottom becomes unsuitable: Neuse croaker habitat suitability "
                 "(ModMon 1994–2021)\nSurface stays suitable; bottom collapses through the estuary in summer.")
    fig.savefig(os.path.join(ROOT, "data", "processed", "suitability_heatmap.png"), dpi=140,
                bbox_inches="tight")
    plt.close(fig)
    print("Saved: data/processed/suitability_heatmap.png")
    # quick numeric summary: bottom HSI by month (median across stations)
    bsum = (both[both.layer == "bottom"].groupby("month")["HSI"].median().round(2))
    print("Bottom croaker HSI by month (median):")
    print(bsum.to_string())


if __name__ == "__main__":
    main()
