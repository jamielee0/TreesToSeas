"""QC / EDA report for the raw FerryMon files, and a check of the cleaned load.

Reads the raw files with *no* cleaning and prints the evidence behind every rule in
``treestoseas/io/ferrymon.py`` (route mixing, DO sentinels, pH-off sentinel, dead
optical_do column, negative turbidity/chl, depth_m disagreement). Then loads through
``load_ferrymon`` and reports what survived, so the cleaning is auditable rather than
silent.

Run:  python scripts/ferrymon_qc.py
Writes: data/processed/ferrymon_qc_summary.csv
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from treestoseas.io.ferrymon import load_ferrymon, _ROUTES  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "processed")
FILES = [
    ("NR 2019-2024", os.path.join(RAW, "ferrymon_NR_2019_2024.csv")),
    ("PS 2025-2026", os.path.join(RAW, "ferrymon_PS_2025_2026.xlsx")),
]


def _read_raw(path):
    if path.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(path, sheet_name="Data")
    return pd.read_csv(path, low_memory=False)


def qc_raw(label, path):
    print(f"\n{'='*70}\nRAW  {label}\n{'='*70}")
    df = _read_raw(path)
    n = len(df)
    print(f"rows={n:,}  cols={list(df.columns)}")

    num = {c: pd.to_numeric(df[c], errors="coerce")
           for c in ["tempc", "spcond", "salppt", "dissolved_o2", "optical_do",
                     "depth_m", "turbid", "chl", "ph"]}
    lat = pd.to_numeric(df["LAT"], errors="coerce")
    lon = pd.to_numeric(df["LONG"], errors="coerce")

    do = num["dissolved_o2"]
    print(f"DO_mgL : range [{do.min():.2f}, {do.max():.2f}]  "
          f"neg[-1,0): {int(((do>=-1)&(do<0)).sum()):,}  "
          f"neg<-1: {int((do<-1).sum()):,}  >20: {int((do>20).sum()):,}")
    ph = num["ph"]
    print(f"pH     : range [{ph.min():.2f}, {ph.max():.2f}]  "
          f"==0: {int((ph==0).sum()):,} ({100*(ph==0).mean():.1f}%)  "
          f"outside[3,11]: {int(((ph<3)|(ph>11)).sum()):,}")
    print(f"optical_do: unique={sorted(pd.unique(num['optical_do'].dropna()))[:6]} "
          f"(dead column -> dropped)")
    print(f"turbidity: neg {int((num['turbid']<0).sum()):,}   "
          f"chl: neg {int((num['chl']<0).sum()):,}   (impossible -> masked)")
    print(f"depth_m: median {num['depth_m'].median():.2f}  "
          f"range [{num['depth_m'].min():.2f}, {num['depth_m'].max():.2f}]  "
          f"(intake vs sounder differs by file)")
    print(f"bad GPS fixes (lat/lon 0 or blank): "
          f"{int((lat.eq(0)|lon.eq(0)|lat.isna()|lon.isna()).sum()):,}")

    print("routes present (by GPS bounding box):")
    for name, (syslabel, (a, b, c, d)) in _ROUTES.items():
        hit = int((lat.between(a, b) & lon.between(c, d)).sum())
        if hit:
            print(f"   {name:14s} [{syslabel}] : {hit:,} rows ({100*hit/n:.1f}%)")
    return n


def qc_clean(label, path):
    df = load_ferrymon(path)
    print(f"\nCLEAN {label}: {len(df):,} rows kept  "
          f"[{df['datetime'].min()} -> {df['datetime'].max()}]")
    rows = []
    for (sysl, route), g in df.groupby(["system", "route"]):
        rec = {"file": label, "system": sysl, "route": route, "rows": len(g)}
        for v in ["temp_C", "salinity_ppt", "DO_mgL", "pH"]:
            rec[f"{v}_valid_pct"] = round(100 * g[v].notna().mean(), 1)
            rec[f"{v}_median"] = round(float(g[v].median()), 2)
        valid_do = g["DO_mgL"].notna()
        rec["DO_hypoxic_pct"] = round(
            100 * (g.loc[valid_do, "DO_mgL"] < 2).mean(), 1)   # among valid-DO rows
        rows.append(rec)
        print(f"   {sysl}/{route:14s}: {len(g):>7,} rows | "
              f"T={rec['temp_C_median']} S={rec['salinity_ppt_median']} "
              f"DO={rec['DO_mgL_median']} (hypoxic {rec['DO_hypoxic_pct']}%) "
              f"pH valid {rec['pH_valid_pct']}%")
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    summary = []
    for label, path in FILES:
        if not os.path.exists(path):
            print(f"MISSING: {path}")
            continue
        qc_raw(label, path)
        summary += qc_clean(label, path)
    if summary:
        out_csv = os.path.join(OUT, "ferrymon_qc_summary.csv")
        pd.DataFrame(summary).to_csv(out_csv, index=False)
        print(f"\nwrote {out_csv}")


if __name__ == "__main__":
    main()
