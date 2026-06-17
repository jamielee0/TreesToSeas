"""#2 - Rigorous oyster validation (anchor species, paired biology).

Does environmental stress BETWEEN censuses predict oyster mortality between censuses?

For each per-bag census interval (prev census -> this census) at a site, we summarize the
high-frequency sensor record (CMAST / DUML, ~2-min temperature + DO) into stress metrics,
then rank-correlate each against the observed interval MortalityRate. Pooled across
4 strains x 2 sites x ~biweekly censuses (2024 season).

Honest expectation: the eastern oyster is tolerant and these sites were generally well-
oxygenated, so T/DO stress may explain only part of mortality (disease, salinity, handling,
cumulative effects also matter). We report whatever the data shows.

Outputs (data/processed/): oyster_validation_summary.csv, oyster_validation.png
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr, mannwhitneyu

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from treestoseas.io.ty_oysterdata import load_env_site_file, load_mortality  # noqa: E402
from treestoseas.model.envelopes import factor_suitability, combine_hsi      # noqa: E402

SITES = {"CMAST": "AverageCMASTtemp.csv", "DUML": "AverageDUMLtemp.csv"}


def site_env(site, fn, oy):
    df = load_env_site_file(os.path.join(ROOT, "data", "raw", fn), site_fallback=site)
    sc = factor_suitability({"temp_C": df.temp_C.to_numpy(), "DO_mgL": df.DO_mgL.to_numpy()}, oy["factors"])
    df["HSI"] = combine_hsi(sc, "geometric_mean")
    df = df.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)
    return {
        "t": df["datetime"].to_numpy().astype("datetime64[ns]"),
        "HSI": df["HSI"].to_numpy(), "temp": df["temp_C"].to_numpy(), "DO": df["DO_mgL"].to_numpy(),
    }


def interval_metrics(env, t0, t1):
    t = env["t"]
    i0, i1 = np.searchsorted(t, np.datetime64(t0)), np.searchsorted(t, np.datetime64(t1), side="right")
    if i1 - i0 < 5:
        return None
    hsi, temp, do = env["HSI"][i0:i1], env["temp"][i0:i1], env["DO"][i0:i1]
    return {
        "n_env": int(i1 - i0),
        "mean_1mHSI": float(np.nanmean(1 - hsi)),
        "min_HSI": float(np.nanmin(hsi)),
        "frac_DO_lt2": float(np.nanmean(do < 2)),
        "frac_DO_lt4": float(np.nanmean(do < 4)),
        "min_DO": float(np.nanmin(do)),
        "mean_temp": float(np.nanmean(temp)),
        "max_temp": float(np.nanmax(temp)),
        "heat_excess_gt30": float(np.nanmean(np.clip(temp - 30, 0, None))),
    }


def main():
    oy = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))["eastern_oyster"]
    envs = {s: site_env(s, fn, oy) for s, fn in SITES.items()
            if os.path.exists(os.path.join(ROOT, "data", "raw", fn))}

    m = load_mortality(os.path.join(ROOT, "data", "raw", "MortalityContinuous.csv"))
    m = m[m["Site"].isin(envs)].copy()
    m["MortalityRate"] = pd.to_numeric(m["MortalityRate"], errors="coerce")
    m = m.sort_values(["Site", "BagNumber", "Date"])
    m["prev_date"] = m.groupby(["Site", "BagNumber"])["Date"].shift(1)

    rows = []
    for _, r in m.iterrows():
        if pd.isna(r["prev_date"]) or pd.isna(r["MortalityRate"]):
            continue
        met = interval_metrics(envs[r["Site"]], r["prev_date"], r["Date"])
        if met is None:
            continue
        met.update(site=r["Site"], strain=r["Strain"], mortality=float(r["MortalityRate"]))
        rows.append(met)
    d = pd.DataFrame(rows)

    predictors = ["mean_1mHSI", "min_HSI", "frac_DO_lt2", "frac_DO_lt4", "min_DO",
                  "mean_temp", "max_temp", "heat_excess_gt30"]
    res = []
    for p in predictors:
        r, pv, n = _spear(d[p], d["mortality"])
        res.append({"predictor": p, "rho_vs_mortality": round(r, 3), "p": pv, "n": n})
    summ = pd.DataFrame(res).sort_values("rho_vs_mortality", key=lambda s: s.abs(), ascending=False)

    proc = os.path.join(ROOT, "data", "processed"); os.makedirs(proc, exist_ok=True)
    summ.to_csv(os.path.join(proc, "oyster_validation_summary.csv"), index=False)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.barh(summ["predictor"], summ["rho_vs_mortality"], color="#2E7D46")
    ax1.axvline(0, color="k", lw=0.8); ax1.set_xlabel("Spearman rho vs interval mortality")
    ax1.set_title(f"Oyster mortality predictors (n={len(d)} bag-intervals)")
    top = summ.iloc[0]["predictor"]
    dd = d.copy(); dd["bin"] = pd.qcut(dd[top], 6, duplicates="drop")
    binned = dd.groupby("bin", observed=True)["mortality"].mean()
    ax2.bar(range(len(binned)), binned.values, color="#1f5fa6")
    ax2.set_xticks(range(len(binned))); ax2.set_xticklabels([f"{iv.mid:.2g}" for iv in binned.index], rotation=45, fontsize=8)
    ax2.set_xlabel(f"{top} (binned)"); ax2.set_ylabel("mean interval mortality")
    ax2.set_title(f"Mortality vs strongest predictor ({top})")
    fig.tight_layout(); fig.savefig(os.path.join(proc, "oyster_validation.png"), dpi=140); plt.close(fig)

    pd.set_option("display.width", 160)
    print(f"=== Oyster validation: stress between censuses vs mortality (n={len(d)} bag-intervals) ===")
    print(summ.to_string(index=False))
    # within-site quick check
    print("\nNOTE: pooled interval correlations are confounded by season (mortality high "
          "early/cool, stress high late/hot) -> spurious NEGATIVE. The cleaner test is the "
          "site contrast at matched time below.")

    # --- cleaner test: more-stressed site (DUML) vs CMAST, controlling for time & strain ---
    print("\n=== Site contrast (controls for the seasonal trend) ===")
    surv_col = "Survivorship_StartingDensityBase_Impute100"
    mm = m.copy()
    mm[surv_col] = pd.to_numeric(mm[surv_col], errors="coerce")
    mm["MortalityRate"] = pd.to_numeric(mm["MortalityRate"], errors="coerce")
    # end-of-season cumulative survivorship per bag
    last = mm.sort_values("Date").groupby(["Site", "BagNumber"]).tail(1)
    by_site = last.groupby("Site")[surv_col].median()
    print("  Median end-of-season survivorship:  " +
          "  ".join(f"{s}={v:.2f}" for s, v in by_site.items()))
    if last["Site"].nunique() == 2:
        a = last[last.Site == "CMAST"][surv_col].dropna()
        b = last[last.Site == "DUML"][surv_col].dropna()
        if len(a) and len(b):
            u, pu = mannwhitneyu(a, b, alternative="two-sided")
            print(f"  CMAST (n={len(a)}) vs DUML (n={len(b)}) end survivorship: Mann-Whitney p={pu:.3g} "
                  f"(more-stressed DUML {'LOWER' if b.median() < a.median() else 'NOT lower'})")
    # within-time_group: is DUML mortality > CMAST in matched periods?
    piv = (mm.dropna(subset=["time_group"]).groupby(["time_group", "Site"])["MortalityRate"]
             .mean().unstack("Site"))
    if {"CMAST", "DUML"}.issubset(piv.columns):
        piv = piv.dropna()
        diff = piv["DUML"] - piv["CMAST"]
        print(f"  Across {len(diff)} matched census periods: DUML mortality > CMAST in "
              f"{int((diff > 0).sum())}/{len(diff)} (mean diff {diff.mean():+.3f})")
    print(f"\nSaved: oyster_validation_summary.csv, oyster_validation.png")


def _spear(a, b):
    a, b = pd.to_numeric(a, errors="coerce"), pd.to_numeric(b, errors="coerce")
    mask = a.notna() & b.notna()
    if mask.sum() < 5:
        return np.nan, np.nan, int(mask.sum())
    r, p = spearmanr(a[mask], b[mask])
    return float(r), float(p), int(mask.sum())


if __name__ == "__main__":
    main()
