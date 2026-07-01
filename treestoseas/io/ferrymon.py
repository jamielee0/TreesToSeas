"""Loader for FerryMon underway (ferry-of-opportunity) water-quality data.

FerryMon draws water from a ferry's engine-cooling *intake* and logs YSI-sonde
parameters every ~30 s along the crossing, so each file is a dense stream of
**surface** measurements resolved in space (lat/lon) rather than depth. This is the
piece the fixed-station ModMon record and the twice-yearly Program 195 trawl cannot
give: *where across the estuary* the surface is inside vs. outside a tolerance
envelope, at sub-daily cadence.

Two files were delivered by Tony Whipple (2026-06):
  * ``ferrymon_NR_2019_2024.csv``    Neuse-labeled, 2019-2024
  * ``ferrymon_PS_2025_2026.xlsx``   Pamlico Sound, 2025-04 -> 2026-06

Both share one raw schema:
    cast date, sample_time, tempc, spcond, salppt, dissolved_o2, optical_do,
    depth_m, turbid, chl, ph, LAT, LONG

Cleaning rules encoded below were derived from a full QC pass over the raw files
(see ``scripts/ferrymon_qc.py``). The load-bearing ones:

  * **The "NR" file is not one route.** It bundles three ferry crossings that must
    not be pooled: the Neuse (Cherry Branch-Minnesott, ~88 %), the Cape Fear
    (Southport-Fort Fisher, ~7 %), and the Pamlico River (Bayview-Aurora, ~5 %).
    ``load_ferrymon`` labels every row with a ``route``/``system`` from its GPS fix
    so a caller can keep the Neuse water separate from Cape Fear water.
  * **Negative DO is masked, not clamped.** A negative reading is non-physical. The
    small negatives were originally clamped to 0 (read as near-anoxia), but they
    cluster in cool months and in specific years -- the signature of sensor
    drift/offset, not summer anoxia -- so clamping them to 0 manufactures hypoxia.
    We therefore mask all DO < 0 (and impossible DO > 20) to NaN; genuine anoxia
    survives as the small *positive* values it actually produces.

  * **Absolute DO/temperature are intake values -- validated against ModMon (see
    `scripts/ferrymon_vs_modmon.py`).** Verdict: **salinity is reliable**; **temperature
    is warm-biased** (~+1 C Neuse, up to ~+4-5 C Pamlico) but well-correlated, so usable
    only as a relative/spatial field; **do NOT use FerryMon absolute DO / surface hypoxia**
    -- the Neuse DO probe is erratic (bias -2 to -4 mg/L, uncorrelated, physically-impossible
    negatives in 2019/2020/2023), and the Pamlico DO agrees with ModMon only in the cool,
    well-oxygenated water it was tested in (never validated for hypoxia). pH is unusable.
  * **pH sentinels.** The PS sonde logs pH == 0 when the probe is off (~35 % of PS
    rows); those and out-of-range pH are masked.
  * **``optical_do`` is a dead column** (constant 0 in NR, 1 in PS) and is dropped.
  * **``depth_m`` is not comparable between files** (~0.1 m intake depth in NR but a
    sounder/bottom depth, median ~8.5 m, in PS), so it is kept only as untrusted
    metadata; the sampled water is surface in both, hence ``layer == 'surface'``.

Returns the canonical column names the rest of the pipeline uses (``temp_C``,
``salinity_ppt``, ``DO_mgL``, ``pH`` ...) so FerryMon slots alongside ModMon.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# raw header -> canonical name (optical_do intentionally omitted -> dropped)
_RENAME = {
    "tempc": "temp_C", "salppt": "salinity_ppt", "dissolved_o2": "DO_mgL",
    "ph": "pH", "turbid": "turbidity_NTU", "chl": "chl", "spcond": "spcond_mScm",
    "depth_m": "depth_m", "LAT": "lat", "LONG": "lon",
}

# Physical plausibility windows (values outside -> NaN). DO handled separately.
_QC_RANGES = {
    "temp_C": (-2.0, 45.0),
    "salinity_ppt": (0.0, 45.0),
    "spcond_mScm": (0.0, 80.0),
    "pH": (3.0, 11.0),      # PS logs pH == 0 when the probe is off -> also masked
    "turbidity_NTU": (0.0, np.inf),
    "chl": (0.0, np.inf),
    "depth_m": (-1.0, 60.0),
}

_DO_HARD_MAX = 20.0      # mg/L; negatives and values above this are sensor faults -> NaN

# Ferry routes bundled across the two files, keyed by a GPS bounding box
# (lat_lo, lat_hi, lon_lo, lon_hi). Derived from the QC cluster centroids.
_ROUTES = {
    # system, (lat_lo, lat_hi, lon_lo, lon_hi)
    "neuse":         ("NR", (34.90, 35.02, -76.85, -76.76)),  # Cherry Branch-Minnesott
    "cape_fear":     ("CF", (33.85, 34.05, -78.05, -77.85)),  # Southport-Fort Fisher
    "pamlico_river": ("PR", (35.30, 35.46, -76.82, -76.66)),  # Bayview-Aurora
    "pamlico_sound": ("PS", (34.95, 35.45, -76.45, -75.90)),  # Cedar Is/Swan Q-Ocracoke
}


def _season(month):
    """Meteorological season from month number (NaN-safe)."""
    lut = {12: "winter", 1: "winter", 2: "winter",
           3: "spring", 4: "spring", 5: "spring",
           6: "summer", 7: "summer", 8: "summer",
           9: "fall", 10: "fall", 11: "fall"}
    return month.map(lut)


def _combine_datetime(cast_date, sample_time):
    """cast date (day) + sample_time (time-of-day) -> full timestamp.

    Handles the string form ('6/17/2019', '13:34:04') from the CSV and the
    Timestamp + ``datetime.time`` form the Excel reader returns. Anything that does
    not parse to a valid day and time-of-day becomes NaT and is dropped by the caller.
    """
    day = pd.to_datetime(cast_date, errors="coerce").dt.normalize()
    # sample_time is a time-of-day ('13:34:04'); parse straight to a timedelta so a
    # 1M-row file does not fall back to per-element dateutil parsing. An unparseable
    # time yields NaT (not a silent midnight), so the row is dropped downstream rather
    # than given a fabricated timestamp.
    tod = pd.to_timedelta(sample_time.astype(str), errors="coerce")
    return day + tod


def _assign_routes(lat, lon):
    """Vectorized route label from a GPS fix; unmatched/blank fixes -> 'other'."""
    route = pd.Series("other", index=lat.index, dtype=object)
    system = pd.Series("other", index=lat.index, dtype=object)
    for name, (sys_label, (a, b, c, d)) in _ROUTES.items():
        hit = lat.between(a, b) & lon.between(c, d) & route.eq("other")
        route = route.mask(hit, name)
        system = system.mask(hit, sys_label)
    return route, system


def load_ferrymon(path, route=None, system=None, drop_no_fix=True):
    """Load a FerryMon file (``.csv`` or ``.xlsx``) into canonical long format.

    Parameters
    ----------
    path : str
        Path to ``ferrymon_*.csv`` (Neuse) or ``ferrymon_*.xlsx`` (Pamlico Sound).
    route : str or list of str, optional
        Keep only these route keys (e.g. ``'neuse'`` to drop the Cape Fear and
        Pamlico-River records that ride along in the NR file). See ``_ROUTES``.
    system : str or list of str, optional
        Keep only these system labels (``'NR'``, ``'PS'``, ``'CF'``, ``'PR'``).
    drop_no_fix : bool, default True
        Drop rows whose GPS fix is missing/zero (they cannot be placed on a route).
        NOTE: ~618 of these (across both files) carry valid T/S/DO with a good
        timestamp -- position-only attrition. For a *spatial* analysis the default is
        right; for a pure time-series/aggregate use, pass ``drop_no_fix=False`` so
        those measurements still count (their route/lat/lon stay NaN).

    Returns
    -------
    DataFrame with columns: datetime, system, route, layer ('surface'), lat, lon,
    temp_C, salinity_ppt, DO_mgL, pH, turbidity_NTU, chl, spcond_mScm, depth_m,
    year, month, season. Rows with an unparseable datetime are dropped.
    """
    if str(path).lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(path, sheet_name="Data")
    else:
        # engine='python' + coercion below tolerates the handful of Excel-mangled cells
        df = pd.read_csv(path, low_memory=False)

    out = pd.DataFrame(index=df.index)
    out["datetime"] = _combine_datetime(df["cast date"], df["sample_time"])
    # cast to float64 (not int64) so every measurement column is uniformly NaN-able,
    # regardless of whether a given file's raw column happens to be all-integer.
    for src, dst in _RENAME.items():
        if src in df.columns:
            out[dst] = pd.to_numeric(df[src], errors="coerce").astype("float64")

    # --- dissolved oxygen: negatives are non-physical (drift/offset, not anoxia) and
    # so are impossible highs -> NaN. Genuine anoxia survives as small positives. ---
    do = out["DO_mgL"]
    out["DO_mgL"] = do.mask((do < 0.0) | (do > _DO_HARD_MAX))

    # --- other variables: mask outside physical windows (pH==0 sentinel falls out) ---
    for col, (lo, hi) in _QC_RANGES.items():
        if col in out.columns:
            out.loc[(out[col] < lo) | (out[col] > hi), col] = np.nan

    # --- geography: mask blank/zero fixes, then label the ferry route ---
    bad_fix = out["lat"].isna() | out["lon"].isna() | out["lat"].eq(0) | out["lon"].eq(0)
    out.loc[bad_fix, ["lat", "lon"]] = np.nan
    out["route"], out["system"] = _assign_routes(out["lat"], out["lon"])

    out["layer"] = "surface"
    out["year"] = out["datetime"].dt.year
    out["month"] = out["datetime"].dt.month
    out["season"] = _season(out["month"])

    out = out.dropna(subset=["datetime"]).reset_index(drop=True)
    if drop_no_fix:
        out = out[out["lat"].notna()].reset_index(drop=True)
    if route is not None:
        keep = [route] if isinstance(route, str) else list(route)
        out = out[out["route"].isin(keep)].reset_index(drop=True)
    if system is not None:
        keep = [system] if isinstance(system, str) else list(system)
        out = out[out["system"].isin(keep)].reset_index(drop=True)

    cols = ["datetime", "system", "route", "layer", "lat", "lon", "temp_C",
            "salinity_ppt", "DO_mgL", "pH", "turbidity_NTU", "chl", "spcond_mScm",
            "depth_m", "year", "month", "season"]
    return out[[c for c in cols if c in out.columns]]
