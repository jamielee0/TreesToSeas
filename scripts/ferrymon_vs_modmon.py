"""Cross-validate FerryMon underway *surface* readings against ModMon fixed-station
*surface* sonde data where the two overlap in space and time.

Why: FerryMon draws water through the ferry's engine-cooling intake, which can warm and
degas the sample, so its ABSOLUTE temperature / dissolved-oxygen may be biased. Before any
FerryMon hypoxia number is trusted, we check it against ModMon (a free-stream profiling
sonde at fixed stations) at the points where a ferry passes close to a ModMon station at
nearly the same time.

Geometry (from ERDDAP allDatasets station coordinates):
  * Neuse: ModMon "Marker 9" (ModMon 120) sits at 34.949 N, -76.815 W -- essentially ON the
    Cherry Branch-Minnesott ferry line. Compared against BOTH the ERDDAP record (2019-2021)
    and the Paerl-Lab sonde (2022-2024), matching the FerryMon Neuse window.
  * Pamlico Sound: stations PS3-PS9 fall inside the Cedar Island/Swan Quarter-Ocracoke ferry
    transect; compared against the sonde (2025-2026), matching the FerryMon PS window.

Matching: for each ModMon surface cast (station, time), take the mean of all FerryMon surface
readings within RADIUS_KM and +/- WINDOW_MIN of it -> ONE paired comparison per cast (no
pseudo-replication). Report bias (FerryMon - ModMon), RMSE, Pearson r.

Validated verdict (58 matched casts; robust across RADIUS in {1.5,3,5} km x WINDOW in
{30,60,90} min; bootstrap CIs; adversarially reviewed):
  * SALINITY -- reliable everywhere (|bias| < 0.3 ppt, r 0.91-0.97, CI includes 0). Use freely.
  * TEMPERATURE -- warm-biased (equilibration toward the warm intake/engine during the
    crossing): a near-constant ~+1 C on the short Neuse crossing, but larger and
    cold-water-amplified on the longer Pamlico crossing (~+3 C at 18 C rising to ~+5 C at
    5 C; slope -0.07 C/C). Excellent correlation (r 0.91-0.99) -> use as a relative/spatial
    field only, not an absolute value.
  * DISSOLVED OXYGEN -- do NOT use FerryMon absolute DO / hypoxia:
      - Neuse (2019-2024): erratic, not a correctable offset. Bias -2 to -4 mg/L,
        uncorrelated (r 0.08-0.40, sign test p<1e-6); the raw DO has year-clustered
        physically-impossible negatives (~5% in 2019/2020/2023, ~0% in 2021/2024) and even
        reads ABOVE ModMon in some pairs -- an intermittently faulty probe.
      - Pamlico Sound (2025-2026): agrees within +/-0.5 mg/L (bias -0.11), BUT only validated
        in cool (<20 C), well-oxygenated (>8 mg/L) water over ~5 survey days -- NOT validated
        for hypoxia or warm-season conditions. Do not quote it as a hypoxia detector.
  * pH -- excluded (probe-off sentinels + spurious highs); reported for transparency only.

Run:  python scripts/ferrymon_vs_modmon.py
Writes (data/processed/): ferrymon_vs_modmon_pairs.csv, ferrymon_vs_modmon_summary.csv,
ferrymon_vs_modmon.png
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

from treestoseas.io.ferrymon import load_ferrymon            # noqa: E402
from treestoseas.io.modmon_excel import load_modmon_excel    # noqa: E402

OUT = os.path.join(ROOT, "data", "processed")
# pH is reported for transparency only -- it is NOT usable: the FerryMon pH probe logs
# off-sentinels and spurious highs (see ferrymon_qc), so it is excluded from any
# reliability claim.
VARS = ["temp_C", "salinity_ppt", "DO_mgL", "pH"]
MAX_TEMP_DISAGREE = 10.0   # >10 C between co-located near-simultaneous surface casts = a
                           # physically-impossible pair (one sensor garbage) -> drop it

RADIUS_KM = 3.0      # a ferry pass within this distance of the station counts as co-located
WINDOW_MIN = 90      # +/- minutes: same station-visit, tolerating diel drift

# ModMon station coordinates (public; fetched from SECOORA ERDDAP allDatasets).
# Neuse sonde 'Station' is the ModMon number; the ERDDAP Marker-9 site is ModMon 120.
NR_MARKER9 = (34.94888, -76.81515)
ERDDAP_MARKER9_SITE = "neuse-river-at-marker-9-modmo"
PS_COORDS = {  # PS sonde 'Station' label -> (lat, lon)
    "PS1": (35.12010, -76.47653), "PS2": (35.15057, -76.42758),
    "PS3": (35.13125, -76.34330), "PS4": (35.11842, -76.26680),
    "PS5": (35.12250, -76.20060), "PS6": (35.08255, -76.24867),
    "PS7": (35.03205, -76.22947), "PS8": (35.02617, -76.30570),
    "PS9": (35.09987, -76.37275),
}


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance (km); lat2/lon2 may be arrays."""
    r = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlmb = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def modmon_surface_casts():
    """One row per ModMon SURFACE cast: station, datetime, lat, lon, source, + VARS."""
    frames = []

    # --- Neuse Marker 9: ERDDAP (surface = shallowest z per cast), 1994-2021 ---
    # CAVEAT: ERDDAP stamps every Marker-9 cast at a placeholder 12:00:00 (no real
    # time-of-day), so the +/-WINDOW_MIN match in the ERDDAP era is centered on a nominal
    # noon, not the true cast time. The diel DO swing near the station is <=0.7 mg/L, far
    # too small to fake the -4 mg/L deficit, but it inflates ERDDAP-era scatter -- lean on
    # the sonde era (real YSI_Time) for the Neuse DO verdict. ERDDAP DO used here is
    # QARTOD-checked PASS (flags verified out-of-band; the preprocessed CSV drops them).
    mm = pd.read_csv(os.path.join(ROOT, "data", "raw", "modmon_all_stations.csv"),
                     low_memory=False)
    m9 = mm[mm.site == ERDDAP_MARKER9_SITE].copy()
    m9["datetime"] = pd.to_datetime(m9["datetime"], errors="coerce")
    m9 = m9.dropna(subset=["datetime", "z"])
    surf = m9.loc[m9.groupby("datetime")["z"].idxmax()]        # max z = shallowest = surface
    surf = surf[surf["z"] >= -1.5]                              # only genuinely-surface bins
    frames.append(pd.DataFrame({
        "station": "NR-120 (Marker 9)", "datetime": surf["datetime"].values,
        "lat": NR_MARKER9[0], "lon": NR_MARKER9[1], "source": "ERDDAP",
        **{v: surf[v].values if v in surf else np.nan for v in VARS}}))

    # --- Neuse Marker 9: Paerl sonde (station '120', layer surface), 2022-2026 ---
    nr = load_modmon_excel(os.path.join(ROOT, "data", "raw", "modmon_NR_2022_2026.xlsx"), "NR")
    s120 = nr[(nr.station == "120") & (nr.layer == "surface")]
    frames.append(pd.DataFrame({
        "station": "NR-120 (Marker 9)", "datetime": s120["datetime"].values,
        "lat": NR_MARKER9[0], "lon": NR_MARKER9[1], "source": "sonde",
        **{v: s120[v].values if v in s120 else np.nan for v in VARS}}))

    # --- Pamlico Sound: sonde PS3-PS9 surface, 2022-2026 ---
    ps = load_modmon_excel(os.path.join(ROOT, "data", "raw", "modmon_PS_2022_2026.xlsx"), "PS")
    pss = ps[ps.layer == "surface"].copy()
    pss = pss[pss.station.isin(PS_COORDS)]
    pss["lat"] = pss.station.map(lambda s: PS_COORDS[s][0])
    pss["lon"] = pss.station.map(lambda s: PS_COORDS[s][1])
    frames.append(pd.DataFrame({
        "station": "PS-" + pss["station"].astype(str), "datetime": pss["datetime"].values,
        "lat": pss["lat"].values, "lon": pss["lon"].values, "source": "sonde",
        **{v: pss[v].values if v in pss else np.nan for v in VARS}}))

    out = pd.concat(frames, ignore_index=True)
    out["system"] = np.where(out.station.str.startswith("NR"), "NR", "PS")
    return out.dropna(subset=["datetime"]).reset_index(drop=True)


def match_ferry(casts, ferry, system):
    """For each cast, mean of FerryMon readings within RADIUS_KM and +/-WINDOW_MIN."""
    f = ferry.dropna(subset=["datetime", "lat", "lon"]).sort_values("datetime")
    ft = f["datetime"].values.astype("datetime64[ns]")
    flat, flon = f["lat"].values, f["lon"].values
    fv = {v: f[v].values for v in VARS}
    win = np.timedelta64(WINDOW_MIN, "m")

    rows = []
    for _, c in casts[casts.system == system].iterrows():
        t = np.datetime64(c["datetime"])
        lo, hi = np.searchsorted(ft, [t - win, t + win])
        if hi <= lo:
            continue
        d = haversine_km(c["lat"], c["lon"], flat[lo:hi], flon[lo:hi])
        near = d <= RADIUS_KM
        if not near.any():
            continue
        rec = {"station": c["station"], "system": system, "datetime": c["datetime"],
               "source": c["source"], "n_ferry": int(near.sum()),
               "min_dist_km": round(float(d[near].min()), 2)}
        for v in VARS:
            vals = fv[v][lo:hi][near]
            vals = vals[~np.isnan(vals)]
            rec[f"mm_{v}"] = c[v]
            rec[f"fm_{v}"] = vals.mean() if vals.size else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def _stats(pairs, v):
    d = pairs.dropna(subset=[f"mm_{v}", f"fm_{v}"])
    if len(d) < 3:
        return None
    mm, fm = d[f"mm_{v}"].values, d[f"fm_{v}"].values
    bias = fm - mm
    r = np.corrcoef(mm, fm)[0, 1]
    return {"var": v, "n": len(d), "mean_bias": round(bias.mean(), 3),
            "median_bias": round(float(np.median(bias)), 3),
            "rmse": round(float(np.sqrt((bias ** 2).mean())), 3),
            "pearson_r": round(float(r), 3),
            "mm_mean": round(mm.mean(), 2), "fm_mean": round(fm.mean(), 2)}


def main():
    os.makedirs(OUT, exist_ok=True)
    casts = modmon_surface_casts()
    print("ModMon surface casts: %d (NR %d, PS %d)" % (
        len(casts), (casts.system == "NR").sum(), (casts.system == "PS").sum()))

    fn = load_ferrymon(os.path.join(ROOT, "data", "raw", "ferrymon_NR_2019_2024.csv"),
                       route="neuse")
    fp = load_ferrymon(os.path.join(ROOT, "data", "raw", "ferrymon_PS_2025_2026.xlsx"))
    pairs = pd.concat([match_ferry(casts, fn, "NR"), match_ferry(casts, fp, "PS")],
                      ignore_index=True)
    # QC gate: drop physically-impossible pairs (a >10 C surface disagreement between
    # co-located, near-simultaneous casts means one sensor is garbage for that pass).
    dt = (pairs["fm_temp_C"] - pairs["mm_temp_C"]).abs()
    bad = dt > MAX_TEMP_DISAGREE
    if bad.any():
        print("QC gate: dropped %d impossible pair(s) (|temp diff|>%.0f C)" % (
            int(bad.sum()), MAX_TEMP_DISAGREE))
    pairs = pairs[~bad].reset_index(drop=True)
    pairs.to_csv(os.path.join(OUT, "ferrymon_vs_modmon_pairs.csv"), index=False)
    print("matched pairs: %d (NR %d, PS %d)  [radius %.1f km, +/-%d min]" % (
        len(pairs), (pairs.system == "NR").sum(), (pairs.system == "PS").sum(),
        RADIUS_KM, WINDOW_MIN))

    # bias stats overall + per system + per era (ERDDAP 2019-21 vs sonde 2022-26 for NR)
    summ = []
    groups = [("ALL", pairs), ("NR", pairs[pairs.system == "NR"]),
              ("NR-ERDDAP", pairs[(pairs.system == "NR") & (pairs.source == "ERDDAP")]),
              ("NR-sonde", pairs[(pairs.system == "NR") & (pairs.source == "sonde")]),
              ("PS", pairs[pairs.system == "PS"])]
    for label, sub in groups:
        for v in VARS:
            s = _stats(sub, v)
            if s:
                s = {"group": label, **s}
                summ.append(s)
                print("  %-3s %-13s n=%3d  bias=%+.2f  rmse=%.2f  r=%.2f  "
                      "(MM %.2f vs FM %.2f)" % (label, v, s["n"], s["mean_bias"],
                      s["rmse"], s["pearson_r"], s["mm_mean"], s["fm_mean"]))
    pd.DataFrame(summ).to_csv(os.path.join(OUT, "ferrymon_vs_modmon_summary.csv"), index=False)

    # warm-bias structure: the temp bias (FM-MM) GROWS in cold water (equilibration toward
    # the warm intake), so report the slope vs ModMon temp per system, not a pooled number.
    for sysn in ["NR", "PS"]:
        dt = pairs[pairs.system == sysn].dropna(subset=["mm_temp_C", "fm_temp_C"])
        if len(dt) > 5:
            tb = dt["fm_temp_C"] - dt["mm_temp_C"]
            sl = np.polyfit(dt["mm_temp_C"], tb, 1)[0]
            print("warm-bias %s: mean %+.2f C, slope %+.3f C/C vs ambient "
                  "(negative => larger bias in cold water)" % (sysn, tb.mean(), sl))
    print("NOTE: pH rows in the summary are NOT usable (broken FerryMon pH probe).")

    # figure: 1:1 scatter per variable
    fig, ax = plt.subplots(1, len(VARS), figsize=(4 * len(VARS), 4))
    for i, v in enumerate(VARS):
        for sysn, col in [("NR", "tab:blue"), ("PS", "tab:orange")]:
            d = pairs[(pairs.system == sysn)].dropna(subset=[f"mm_{v}", f"fm_{v}"])
            ax[i].scatter(d[f"mm_{v}"], d[f"fm_{v}"], s=10, alpha=0.5, color=col, label=sysn)
        lo = np.nanmin([pairs[f"mm_{v}"].min(), pairs[f"fm_{v}"].min()])
        hi = np.nanmax([pairs[f"mm_{v}"].max(), pairs[f"fm_{v}"].max()])
        ax[i].plot([lo, hi], [lo, hi], "k--", lw=1)
        ax[i].set(xlabel=f"ModMon {v}", ylabel=f"FerryMon {v}", title=v)
        ax[i].legend(fontsize=8)
    fig.suptitle("FerryMon (surface intake) vs ModMon (surface sonde) — co-located, +/-90 min")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "ferrymon_vs_modmon.png"), dpi=130)
    print("\nwrote ferrymon_vs_modmon_{pairs,summary}.csv + ferrymon_vs_modmon.png")


if __name__ == "__main__":
    main()
