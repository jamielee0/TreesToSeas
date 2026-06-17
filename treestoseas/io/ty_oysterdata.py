"""Loaders for the Duke Bass Connections oyster team data (org: oystersdukebc).

Schemas (discovered from the repos):

  AverageCMASTtemp.csv / AverageDUMLtemp.csv  (2024-2025, wide, ~hourly)
      Time, TempC, DOmgL, Location, Site, Date, RunningAvg, MaxTemp, MinTemp
      -> temperature AND dissolved oxygen, by site (CMAST / DUML).

  environmental_data_{daily,hourly,5minute}.csv  (2024-2025, LONG)
      Measurement, rounded_time, date, Site, Type [, hour, minute]
      Type is the variable label, e.g. "Precipitation Accumulation (mm)".

  MortalityContinuous.csv / OysterMortalityData_Processed.csv  (per-bag census)
      Date, Strain, BagNumber, StartingDensity, Alive, Dead, Site, FlipFreq,
      Survivorship_*, MortalityRate, time_group, line, ...

  growth_rates.csv
      Group, growth_rate, lower/upper CI, r_squared, p_value, Type, site

  2025-2026 (XLSX): DOsensor_2024.xlsx (DateTime, DomgL, Temp_C), pH_2024.xlsx
      (DateTime, pH), Salinity_2024.xlsx (DateTime, Sal_ppt), and a Cleaned/
      folder with {SITE}_{DO|pH|Con}_Cleaned.xlsx.
"""
from __future__ import annotations

import os

import pandas as pd


def map_to_canonical(name, canonical_vars):
    """Map a raw column name or long-format ``Type`` label to a canonical variable.

    ``canonical_vars`` is the mapping from ``config/sources.yaml``
    (canonical -> list of raw aliases). Match is case-insensitive, exact first
    then substring. Returns the canonical name, or ``None`` if no match.
    """
    if name is None:
        return None
    s = str(name).strip().lower()
    for canon, aliases in canonical_vars.items():
        for alias in aliases:
            if s == str(alias).strip().lower():
                return canon
    for canon, aliases in canonical_vars.items():
        for alias in aliases:
            if str(alias).strip().lower() in s:
                return canon
    return None


def _parse_time(series):
    return pd.to_datetime(series, errors="coerce", format="mixed")


def load_env_site_file(path, site_fallback=None):
    """Load an ``Average{SITE}temp.csv`` file -> tidy wide [datetime, site, temp_C, DO_mgL]."""
    df = pd.read_csv(path)
    out = pd.DataFrame()
    out["datetime"] = _parse_time(df.get("Time", df.get("Date")))
    if "TempC" in df:
        out["temp_C"] = pd.to_numeric(df["TempC"], errors="coerce")
    if "DOmgL" in df:
        out["DO_mgL"] = pd.to_numeric(df["DOmgL"], errors="coerce")
    out["site"] = df["Site"] if "Site" in df else site_fallback
    return out.dropna(subset=["datetime"]).reset_index(drop=True)


def load_env_long_file(path, canonical_vars):
    """Load an ``environmental_data_*.csv`` (long) and pivot to wide canonical columns."""
    df = pd.read_csv(path)
    time_col = "rounded_time" if "rounded_time" in df else "date"
    df["datetime"] = _parse_time(df[time_col])
    df["site"] = df.get("Site", "").fillna("")
    df["canon"] = df["Type"].map(lambda t: map_to_canonical(t, canonical_vars))
    df = df.dropna(subset=["datetime", "canon"])
    df["Measurement"] = pd.to_numeric(df["Measurement"], errors="coerce")

    wide = df.pivot_table(index=["datetime", "site"], columns="canon",
                          values="Measurement", aggfunc="mean").reset_index()
    wide.columns.name = None
    return wide


def load_mortality(path):
    """Load a mortality census CSV into a standardized frame.

    Ensures ``Date`` is datetime and a numeric ``MortalityRate`` exists (derived
    from survivorship if the column is absent).
    """
    df = pd.read_csv(path)
    if "Date" in df:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", format="mixed")
    if "MortalityRate" not in df.columns:
        surv = None
        for c in ("Survivorship_StartingDensityBase",
                  "Survivorship_StartingDensityBase_Impute100"):
            if c in df.columns:
                surv = pd.to_numeric(df[c], errors="coerce")
                break
        if surv is not None:
            df["MortalityRate"] = 1.0 - surv
    else:
        df["MortalityRate"] = pd.to_numeric(df["MortalityRate"], errors="coerce")
    return df


def load_growth_rates(path):
    df = pd.read_csv(path)
    for c in ("growth_rate", "lower_growth_rate", "upper_growth_rate",
              "r_squared", "p_value"):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_cleaned_xlsx(path, value_aliases, canonical_name, datetime_col="DateTime"):
    """Load a 2025-2026 cleaned XLSX sensor file -> [datetime, site, <canonical_name>].

    ``value_aliases`` is a list of possible value column names (e.g. ['DomgL','Temp_C']).
    """
    df = pd.read_excel(path)
    out = pd.DataFrame()
    out["datetime"] = pd.to_datetime(df.get(datetime_col), errors="coerce", format="mixed")
    for alias in value_aliases:
        if alias in df.columns:
            out[canonical_name] = pd.to_numeric(df[alias], errors="coerce")
            break
    return out.dropna(subset=["datetime"]).reset_index(drop=True)


def load_oyster_bundle(raw_dir, sources_cfg):
    """Load every Ty file present in ``raw_dir`` into a dict of DataFrames.

    Missing files are skipped silently (the pipeline degrades gracefully). Returns
    keys among: ``env`` (concatenated wide environmental), ``mortality``,
    ``mortality_binned``, ``growth``.
    """
    ty = sources_cfg["ty_oyster"]
    canon = sources_cfg.get("canonical_vars", {})
    files = ty.get("files_2024_2025", {})
    bundle = {}
    env_frames = []

    for key, site in (("env_cmast", "CMAST"), ("env_duml", "DUML")):
        p = os.path.join(raw_dir, os.path.basename(files.get(key, "")))
        if files.get(key) and os.path.exists(p):
            env_frames.append(load_env_site_file(p, site_fallback=site))

    for key in ("env_long_daily",):  # long-format adds precip/salinity/pH where present
        rel = files.get(key)
        p = os.path.join(raw_dir, os.path.basename(rel)) if rel else None
        if p and os.path.exists(p):
            env_frames.append(load_env_long_file(p, canon))

    if env_frames:
        bundle["env"] = pd.concat(env_frames, ignore_index=True).sort_values("datetime")

    for key, out_key in (("mortality_continuous", "mortality"),
                         ("mortality_binned", "mortality_binned")):
        rel = files.get(key)
        p = os.path.join(raw_dir, os.path.basename(rel)) if rel else None
        if p and os.path.exists(p):
            bundle[out_key] = load_mortality(p)

    rel = files.get("growth_rates")
    p = os.path.join(raw_dir, os.path.basename(rel)) if rel else None
    if p and os.path.exists(p):
        bundle["growth"] = load_growth_rates(p)

    return bundle
