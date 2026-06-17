"""Loader for NC Program 195 (Pamlico Sound Survey) Abundance & Biomass extracts
from the SEAMAP-SA Data Portal.

The portal exports per-tow records (one row per species per tow, plus blank-species
rows for tows where none of the selected species were caught), Excel-text-qualified
(every text cell looks like ="VALUE"). This module strips that wrapper, coerces
numerics/dates, and builds a standard catch-per-unit-effort (CPUE) abundance index.

The CPUE index is the quantity to compare against modeled habitat suitability:
    index(species, year) = sum(NUMBERTOTAL for species) / sum(EFFORT over all tows)
so that tows where the species was absent still count in the effort denominator
(an unbiased relative-abundance index).

NOTE: SEAMAP-SA's terms forbid re-posting their raw data publicly — keep extracts in
data/raw/ (git-ignored). See docs/data_access.md.
"""
from __future__ import annotations

import re

import pandas as pd

_NUMERIC = [
    "NUMBERTOTAL", "SPECIESTOTALWEIGHT", "SPECIESSUBWEIGHT", "EFFORT",
    "CATCHWEIGHT", "CATCHSUBWEIGHT", "DURATION",
    "TEMPSURFACE", "TEMPBOTTOM", "SALINITYSURFACE", "SALINITYBOTTOM",
    "SDO", "BDO", "TEMPAIR", "LATITUDESTART", "LONGITUDESTART",
]

# Program 195 scientific name -> our species.yaml key
SPECIES_KEY = {
    "CALLINECTES SAPIDUS": "blue_crab",
    "PARALICHTHYS LETHOSTIGMA": "southern_flounder",
    "MICROPOGONIAS UNDULATUS": "atlantic_croaker",
}


def _strip_excel(s):
    """Remove the Excel text qualifier: ="value" -> value."""
    if isinstance(s, str):
        m = re.match(r'^="?(.*?)"?$', s)
        return m.group(1) if m else s
    return s


def load_program195(path):
    """Load and clean a Pamlico Sound Survey Abundance/Biomass CSV.

    Returns a per-tow-per-species DataFrame with cleaned types, plus ``YEAR`` and a
    ``species_key`` column mapped to species.yaml keys (NaN for non-target rows).
    Malformed trailing rows in the export are skipped.
    """
    df = pd.read_csv(path, engine="python", on_bad_lines="skip", dtype=str)
    df = df.map(_strip_excel)
    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce", format="%m-%d-%Y")
    df = df.dropna(subset=["DATE"]).copy()
    for c in _NUMERIC:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["YEAR"] = df["DATE"].dt.year
    df["MONTH"] = df["DATE"].dt.month
    df["species_key"] = df["SPECIESSCIENTIFICNAME"].map(SPECIES_KEY)
    return df


def annual_cpue_index(df, value="NUMBERTOTAL", tow_id="COLLECTIONNUMBER",
                      locations=None):
    """Annual CPUE relative-abundance index per species.

    index = sum(value for species in year) / sum(EFFORT over unique tows in year).
    Effort is summed over ALL tows (including zero-catch), so absence counts.

    Parameters
    ----------
    value : 'NUMBERTOTAL' (counts) or 'SPECIESTOTALWEIGHT' (biomass).
    locations : optional list of LOCATION values to restrict to (e.g. Neuse/Pamlico).

    Returns
    -------
    DataFrame [species_key, SPECIESSCIENTIFICNAME, YEAR, total, total_effort, cpue].
    """
    d = df
    if locations is not None:
        d = d[d["LOCATION"].isin(locations)]

    tows = d.drop_duplicates(subset=[tow_id])
    effort = tows.groupby("YEAR")["EFFORT"].sum().rename("total_effort")

    sp = d.dropna(subset=["species_key"])
    num = (sp.groupby(["species_key", "SPECIESSCIENTIFICNAME", "YEAR"])[value]
             .sum().rename("total").reset_index())
    out = num.merge(effort.reset_index(), on="YEAR")
    out["cpue"] = out["total"] / out["total_effort"]
    return out.sort_values(["species_key", "YEAR"]).reset_index(drop=True)
