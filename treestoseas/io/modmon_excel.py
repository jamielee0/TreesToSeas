"""Loader for the UNC ModMon post-2021 sonde Excel files (provided by the Paerl Lab).

Files: 'ModMon NR Sonde Data 2022-2026.xlsx' (Neuse River) and the 'PS' (Pamlico Sound)
companion. Each 'Data' sheet has one row per cast-layer with an explicit
Depth = 'S' (surface) or 'B' (bottom) label, plus YSI sonde parameters. Qualifier-code
sentinels (-9999 below detection, -8888 not sampled, -7777 not analyzed, etc.) are
masked to NaN.

Returns the same canonical columns the rest of the pipeline uses, so the post-2021 data
concatenates with the ERDDAP ModMon record (1994-2021) into a continuous 1994-2026 series.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

_RENAME = {
    "YSI_Temp": "temp_C", "YSI_Salinity": "salinity_ppt", "YSI_DO": "DO_mgL",
    "YSI_pH": "pH", "YSI_Turbidity": "turbidity_NTU", "YSI_Chl": "chl",
    "YSI_DOsat": "DO_pct_sat", "YSI_Depth": "depth_m",
}


def load_modmon_excel(path, system):
    """Load one ModMon sonde Excel ('Data' sheet) into the canonical long format.

    Parameters
    ----------
    system : 'NR' (Neuse River) or 'PS' (Pamlico Sound).

    Returns columns: datetime, system, station, modmon (km/sort key), layer
    ('surface'/'bottom'), depth_m, temp_C, salinity_ppt, DO_mgL, pH, turbidity_NTU,
    chl, DO_pct_sat, year, month, season.
    """
    df = pd.read_excel(path, sheet_name="Data")
    out = pd.DataFrame()
    out["datetime"] = pd.to_datetime(df["Date"], errors="coerce")
    out["system"] = system
    out["station"] = df["Station"].astype(str)
    out["layer"] = df["Depth"].map({"S": "surface", "B": "bottom"})
    for src, dst in _RENAME.items():
        if src in df.columns:
            out[dst] = pd.to_numeric(df[src], errors="coerce")

    # mask qualifier-code sentinels (all are large negatives; no real sonde value < -100)
    for c in ("temp_C", "salinity_ppt", "DO_mgL", "pH", "turbidity_NTU", "chl",
              "DO_pct_sat", "depth_m"):
        if c in out.columns:
            out.loc[out[c] < -100, c] = np.nan

    if system == "NR":
        out["modmon"] = pd.to_numeric(df["Station"], errors="coerce")     # river-km (0..180)
    else:
        out["modmon"] = pd.to_numeric(df.get("Stn sort"), errors="coerce")
    out["year"] = out["datetime"].dt.year
    out["month"] = out["datetime"].dt.month
    out["season"] = df.get("Season")
    return out.dropna(subset=["datetime"]).reset_index(drop=True)
