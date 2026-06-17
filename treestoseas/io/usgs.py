"""USGS NWIS loader -- Neuse River discharge at Fort Barnwell (02091814).

Discharge is the freshwater-forcing covariate for salinity/stratification in the
Neuse-Pamlico generalization. Continuous daily record begins Oct 1996. Public, no
login. Dependency-free: talks to the NWIS REST service directly via ``requests``
(the optional ``dataretrieval`` package is NOT required).
"""
from __future__ import annotations

import io

import pandas as pd
import requests

_DV = "https://waterservices.usgs.gov/nwis/dv/"


def load_discharge(site="02091814", start="1996-10-01", end=None,
                   parameter_cd="00060", timeout=120):
    """Daily mean discharge (cfs, parameter 00060) for a USGS gauge -> tidy DataFrame.

    Returns columns [datetime, discharge_cfs, site_no]. Parses the NWIS RDB
    (tab-delimited) response, skipping its comment and format-spec lines.
    """
    params = {"format": "rdb", "sites": site, "parameterCd": parameter_cd,
              "statCd": "00003", "startDT": start}
    if end:
        params["endDT"] = end
    r = requests.get(_DV, params=params, headers={"User-Agent": "trees-to-seas"},
                     timeout=timeout)
    r.raise_for_status()

    lines = [ln for ln in r.text.splitlines() if not ln.startswith("#") and ln.strip()]
    if len(lines) < 3:
        return pd.DataFrame(columns=["datetime", "discharge_cfs", "site_no"])
    header = lines[0].split("\t")
    data_lines = lines[2:]  # lines[1] is the RDB format spec (e.g. 5s, 15s, 20d)
    raw = pd.read_csv(io.StringIO("\n".join([("\t".join(header))] + data_lines)),
                      sep="\t", dtype=str)

    disch_col = next((c for c in raw.columns if "00060" in c and not c.endswith("_cd")), None)
    out = pd.DataFrame()
    out["datetime"] = pd.to_datetime(raw.get("datetime"), errors="coerce")
    out["discharge_cfs"] = pd.to_numeric(raw[disch_col], errors="coerce") if disch_col else pd.NA
    out["site_no"] = raw.get("site_no", site)
    return out.dropna(subset=["datetime"]).reset_index(drop=True)
