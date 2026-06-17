"""Download all PUBLIC, no-login Neuse-Pamlico data sources into data/raw/.

  - ModMon water quality (SECOORA ERDDAP)  -> data/raw/modmon/<station>.csv + combined
  - USGS Neuse discharge at Fort Barnwell   -> data/raw/usgs_neuse_fort_barnwell_discharge.csv
  - NOAA CO-OPS water temp at Beaufort       -> data/raw/noaa_beaufort_8656483_water_temp.csv

None require an API key or login. Re-running overwrites. Each source is wrapped so
one failure doesn't abort the others. (Ty's oyster data and Program 195 are fetched
separately — see scripts/fetch_data.py and docs/data_access.md.)
"""
from __future__ import annotations

import datetime
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from treestoseas.io import erddap, usgs, noaa_coops  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw")


def fetch_modmon():
    out = os.path.join(RAW, "modmon")
    os.makedirs(out, exist_ok=True)
    print("[ModMon] discovering stations...")
    try:
        stations = erddap.list_modmon_datasets()
    except Exception as e:
        print(f"[ModMon] discovery FAILED: {e}")
        return
    print(f"[ModMon] {len(stations)} stations")
    combined = []
    for d in stations:
        try:
            df = erddap.load_modmon_station(d["id"])
            df.to_csv(os.path.join(out, d["id"] + ".csv"), index=False)
            combined.append(df.assign(title=d["title"]))
            print(f"  ok   {d['id']:34s} {len(df):6d} rows")
        except Exception as e:
            print(f"  FAIL {d['id']:34s} {e}")
    if combined:
        allc = pd.concat(combined, ignore_index=True)
        allc.to_csv(os.path.join(RAW, "modmon_all_stations.csv"), index=False)
        rng = (allc["datetime"].min(), allc["datetime"].max())
        print(f"[ModMon] combined {len(allc)} rows ({rng[0]} .. {rng[1]}) "
              f"-> modmon_all_stations.csv")


def fetch_usgs():
    print("[USGS] Fort Barnwell discharge (02091814)...")
    try:
        df = usgs.load_discharge()
        path = os.path.join(RAW, "usgs_neuse_fort_barnwell_discharge.csv")
        df.to_csv(path, index=False)
        print(f"[USGS] {len(df)} daily rows "
              f"({df['datetime'].min().date()} .. {df['datetime'].max().date()})")
    except Exception as e:
        print(f"[USGS] FAILED: {e}")


def fetch_noaa():
    print("[NOAA] Beaufort water temperature (8656483), per year...")
    frames = []
    this_year = datetime.date.today().year
    for yr in range(2000, this_year + 1):
        try:
            d = noaa_coops.load_water_temperature(begin_date=f"{yr}0101",
                                                  end_date=f"{yr}1231")
            if len(d):
                frames.append(d)
                print(f"  {yr}: {len(d)} rows")
        except Exception as e:
            print(f"  {yr}: skip ({e})")
    if frames:
        allc = pd.concat(frames, ignore_index=True)
        path = os.path.join(RAW, "noaa_beaufort_8656483_water_temp.csv")
        allc.to_csv(path, index=False)
        print(f"[NOAA] {len(allc)} hourly rows -> {os.path.basename(path)}")
    else:
        print("[NOAA] no data returned for the requested years")


if __name__ == "__main__":
    fetch_modmon()
    fetch_usgs()
    fetch_noaa()
    print("\nDone. Public data in data/raw/ (git-ignored).")
