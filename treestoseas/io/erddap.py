"""SECOORA ERDDAP loader for the UNC ModMon program -- the Neuse-Pamlico
GENERALIZATION target.

Verified live (June 2026): the ModMon datasets are public on SECOORA ERDDAP,
QARTOD-flagged, covering ~1994-01-24 to 2021-12-06 (Neuse mid-river stations) and
~2000-2021 (Pamlico Sound). No login or API key. This module talks to ERDDAP's
CSV endpoint directly via ``requests`` -- NO extra dependency required (``erddapy``
is optional and not needed).

Typical use:
    from treestoseas.io import erddap
    stations = erddap.list_modmon_datasets()           # auto-discover all station IDs
    df = erddap.load_modmon_station("neuse-river-at-marker-9-modmo",
                                    start="2010-06-01", end="2010-09-30")
    # -> tidy [datetime, site, temp_C, salinity_ppt, DO_mgL, pH, turbidity_NTU]
"""
from __future__ import annotations

import io
from urllib.parse import quote

import pandas as pd
import requests

DEFAULT_BASE = "https://erddap.secoora.org/erddap"

# ERDDAP/CF variable name -> canonical model name (units verified on ModMon).
CF_TO_CANONICAL = {
    "sea_water_temperature": "temp_C",                    # degree_Celsius
    "sea_water_practical_salinity": "salinity_ppt",       # 1e-3 (PSU ~ ppt)
    "mass_concentration_of_oxygen_in_sea_water": "DO_mgL",  # mg.L-1  (no conversion!)
    "sea_water_ph_reported_on_total_scale": "pH",         # dimensionless
    "sea_water_turbidity": "turbidity_NTU",               # NTU
}

# QARTOD aggregate flags: 1=good, 2=not_evaluated, 3=suspect, 4=fail, 9=missing.
_QC_BAD = {3, 4, 9}


def list_modmon_datasets(base=DEFAULT_BASE, search_for="ModMon", timeout=60):
    """Auto-discover ModMon station datasets. Returns [{'id', 'title'}, ...].

    No need to hard-code dataset IDs -- this enumerates them from ERDDAP so the
    pipeline keeps working if SECOORA adds/renames stations.
    """
    url = (f"{base}/search/index.json"
           f"?page=1&itemsPerPage=10000&searchFor={quote(search_for)}")
    r = requests.get(url, headers={"User-Agent": "trees-to-seas"}, timeout=timeout)
    r.raise_for_status()
    table = r.json()["table"]
    cols = table["columnNames"]
    td, ti = cols.index("tabledap"), cols.index("Title")
    out = []
    for row in table["rows"]:
        link = row[td] or ""
        ds = link.split("/tabledap/")[-1].replace(".html", "") if "/tabledap/" in link else None
        if ds:
            out.append({"id": ds, "title": row[ti]})
    return out


def _available_vars(base, dataset_id, timeout):
    """The set of variable names a dataset actually exposes (from its info table)."""
    r = requests.get(f"{base}/info/{dataset_id}/index.json",
                     headers={"User-Agent": "trees-to-seas"}, timeout=timeout)
    r.raise_for_status()
    t = r.json()["table"]
    cols = t["columnNames"]
    rt, vn = cols.index("Row Type"), cols.index("Variable Name")
    return {row[vn] for row in t["rows"] if row[rt] == "variable"}


def load_modmon_station(dataset_id, base=DEFAULT_BASE, start=None, end=None,
                        variables=None, apply_qc=True, timeout=120):
    """Fetch one ModMon station from ERDDAP as a tidy, canonical DataFrame.

    Parameters
    ----------
    dataset_id : str
        e.g. ``neuse-river-at-marker-9-modmo`` (ModMon 120) or
        ``neuse-river-at-marker-52-a-mo`` (ModMon 20).
    start, end : str, optional
        ISO dates/times, e.g. ``"2010-06-01"``.
    variables : list[str], optional
        CF variable names (defaults to the core water-quality set).
    apply_qc : bool
        If True, values whose QARTOD ``*_qc_agg`` flag is suspect/fail/missing
        are set to NaN (rather than dropped).

    Returns
    -------
    pandas.DataFrame
        [datetime, site, <canonical vars present>].
    """
    cf_vars = variables or list(CF_TO_CANONICAL.keys())

    def _fetch(cols):
        url = f"{base}/tabledap/{dataset_id}.csv?" + quote(",".join(cols), safe=",")
        for cons in ([f"time>={start}"] if start else []) + ([f"time<={end}"] if end else []):
            url += "&" + quote(cons, safe="<>=:-")
        return requests.get(url, headers={"User-Agent": "trees-to-seas"}, timeout=timeout)

    cols = ["time"] + cf_vars + ([f"{v}_qc_agg" for v in cf_vars] if apply_qc else [])
    r = _fetch(cols)
    if r.status_code == 400:
        # this station doesn't expose every requested variable — keep only what it has
        avail = _available_vars(base, dataset_id, timeout)
        cf_list = [v for v in cf_vars if v in avail]
        if not cf_list:
            raise ValueError(f"{dataset_id} exposes none of {cf_vars}")
        qc_list = [f"{v}_qc_agg" for v in cf_list if f"{v}_qc_agg" in avail] if apply_qc else []
        r = _fetch(["time"] + cf_list + qc_list)
    if r.status_code == 404:
        raise ValueError(f"ERDDAP returned no data for {dataset_id} in that window.")
    r.raise_for_status()

    raw = pd.read_csv(io.StringIO(r.text))
    raw = raw.iloc[1:].reset_index(drop=True)   # row 0 after header is units

    out = pd.DataFrame()
    out["datetime"] = pd.to_datetime(raw["time"], errors="coerce", utc=True).dt.tz_localize(None)
    out["site"] = dataset_id
    for cf, canon in CF_TO_CANONICAL.items():
        if cf in raw.columns:
            vals = pd.to_numeric(raw[cf], errors="coerce")
            qc_col = f"{cf}_qc_agg"
            if apply_qc and qc_col in raw.columns:
                flags = pd.to_numeric(raw[qc_col], errors="coerce")
                vals = vals.mask(flags.isin(_QC_BAD))
            out[canon] = vals
    return out.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)
