"""FerryMon surface-salinity transect maps -- the spatial layer FerryMon can legitimately add.

The FerryMon-vs-ModMon cross-validation (scripts/ferrymon_vs_modmon.py) certified exactly one
FerryMon variable as reliable in absolute terms: SALINITY (bias <0.3 ppt, r 0.91-0.97). DO is
unusable and temperature is only a relative field. So this script maps the *surface salinity
field* the ferry resolves -- across the estuary width (along-transect position) and through the
season -- and translates it into each species' salinity-tolerance suitability, WITHOUT touching
DO or absolute temperature.

For each crossing (Neuse Cherry Branch-Minnesott; Pamlico Sound Cedar Island/Swan Quarter-
Ocracoke) it produces:
  * salinity(ppt) as an along-transect x month climatology (the field), and
  * each species' salinity-only suitability vs along-transect position (warm season) -- i.e.
    WHERE across the estuary a species' salinity envelope is met, at a resolution the twice-yearly
    trawl and the fixed ModMon stations cannot give.

Along-transect distance is the projection of each GPS fix onto the crossing's principal axis (PCA),
in km from one terminal. Salinity suitability uses the trapezoidal envelopes in config/species.yaml
(the same model as the rest of the project), single-factor (salinity only).

Run:  python scripts/ferrymon_transect.py
Writes (data/processed/): ferrymon_transect.png, ferrymon_transect_summary.csv
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

from treestoseas.io.ferrymon import load_ferrymon        # noqa: E402
from treestoseas.model.envelopes import trapezoid        # noqa: E402

OUT = os.path.join(ROOT, "data", "processed")
WARM = [6, 7, 8, 9]
SPECIES = {  # display name -> species.yaml key
    "croaker": "atlantic_croaker", "flounder": "southern_flounder",
    "blue crab": "blue_crab", "oyster": "eastern_oyster",
}
SYSTEMS = [  # (label, loader kwargs, n along-transect bins)
    ("Neuse (Cherry Branch-Minnesott)",
     dict(path="ferrymon_NR_2019_2024.csv", route="neuse"), 12),
    ("Pamlico Sound (Cedar Is/Swan Q-Ocracoke)",
     dict(path="ferrymon_PS_2025_2026.xlsx"), 16),
]


def along_transect_km(lat, lon):
    """Distance (km) along the crossing's principal axis, from one terminal."""
    mlat = np.radians(lat.mean())
    y = (lat - lat.mean()) * 111.0                  # km north
    x = (lon - lon.mean()) * 111.0 * np.cos(mlat)   # km east
    xc, yc = x - x.mean(), y - y.mean()
    # principal axis = leading eigenvector of the 2x2 covariance (small + stable);
    # project with an explicit dot (avoids a spurious matmul SIMD FP warning on big arrays)
    w, v = np.linalg.eigh(np.cov(np.vstack([xc, yc])))
    pc = v[:, int(np.argmax(w))]
    d = xc * pc[0] + yc * pc[1]
    return d - d.min()


def salinity_breakpoints():
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))
    return {disp: cfg[key]["factors"]["salinity_ppt"] for disp, key in SPECIES.items()}


def main():
    os.makedirs(OUT, exist_ok=True)
    sal_bp = salinity_breakpoints()

    fig, axes = plt.subplots(len(SYSTEMS), 2, figsize=(13, 4.2 * len(SYSTEMS)))
    summ = []
    for r, (label, kw, nbins) in enumerate(SYSTEMS):
        df = load_ferrymon(os.path.join(ROOT, "data", "raw", kw["path"]),
                           **{k: v for k, v in kw.items() if k != "path"})
        df = df.dropna(subset=["salinity_ppt", "lat", "lon"]).copy()
        df["dkm"] = along_transect_km(df["lat"].to_numpy(), df["lon"].to_numpy())
        edges = np.linspace(0, df["dkm"].max(), nbins + 1)
        df["dbin"] = np.clip(np.digitize(df["dkm"], edges) - 1, 0, nbins - 1)
        centers = (edges[:-1] + edges[1:]) / 2

        # --- Panel A: salinity(ppt) as along-transect x month climatology ---
        grid = (df.groupby(["dbin", "month"])["salinity_ppt"].mean()
                  .reindex(pd.MultiIndex.from_product([range(nbins), range(1, 13)]))
                  .unstack())
        ax = axes[r, 0]
        im = ax.imshow(grid.values, aspect="auto", origin="lower", cmap="viridis",
                       extent=[0.5, 12.5, centers[0], centers[-1]])
        ax.set(xlabel="month", ylabel="along-transect km", title=f"{label}\nsurface salinity (ppt)")
        ax.set_xticks(range(1, 13))
        fig.colorbar(im, ax=ax, label="ppt")

        # --- Panel B: warm-season salinity-suitability vs along-transect position ---
        warm = df[df["month"].isin(WARM)]
        by = warm.groupby("dbin")["salinity_ppt"].mean().reindex(range(nbins))
        ax2 = axes[r, 1]
        for disp, bp in sal_bp.items():
            hsi = trapezoid(by.values, bp)
            ax2.plot(centers, hsi, marker="o", ms=3, label=disp)
        ax2.set(xlabel="along-transect km", ylabel="salinity suitability (0-1)",
                ylim=(-0.03, 1.03),
                title=f"{label}\nwarm-season (Jun-Sep) salinity habitat by position")
        ax2.legend(fontsize=8, ncol=2)
        ax2.grid(alpha=0.3)

        # summary: per species, fraction of transect bins with salinity-HSI >= 0.5 (warm season)
        for disp, bp in sal_bp.items():
            hsi = trapezoid(by.values, bp)
            valid = ~np.isnan(hsi)
            summ.append({"system": label.split(" (")[0], "species": disp,
                         "warm_sal_min": round(float(np.nanmin(by.values)), 1),
                         "warm_sal_max": round(float(np.nanmax(by.values)), 1),
                         "frac_transect_suitable_ge0.5": round(
                             float(np.mean(hsi[valid] >= 0.5)), 2),
                         "mean_sal_HSI": round(float(np.nanmean(hsi)), 2)})

    fig.suptitle("FerryMon surface SALINITY transects (the cross-validated variable) — "
                 "DO/absolute-temp excluded", y=1.005, fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "ferrymon_transect.png"), dpi=130, bbox_inches="tight")
    pd.DataFrame(summ).to_csv(os.path.join(OUT, "ferrymon_transect_summary.csv"), index=False)
    print(pd.DataFrame(summ).to_string(index=False))
    print("\nwrote ferrymon_transect.png + ferrymon_transect_summary.csv")


if __name__ == "__main__":
    main()
