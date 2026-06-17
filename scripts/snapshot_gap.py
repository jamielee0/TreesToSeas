"""#1 - Quantify what a twice-yearly survey misses (temporal-resolution gap).

NC's fishery-independent surveys sample at a twice-yearly cadence (Program 195: June &
September). High-frequency in-situ monitoring shows how much of the habitat's dynamics
that cadence cannot resolve.

Honest framing (what the data actually supports): at these well-flushed oyster sites in
2024 the *tolerant* eastern oyster rarely entered acute suitability stress -- so this is
NOT "oysters dying in a squeeze." The real, defensible point is that the OXYGEN REGIME is
highly dynamic -- episodic crashes toward anoxia, large day/night swings, and strong
site-to-site differences -- and two daytime snapshots resolve almost none of it. That
matters most for DO-sensitive species (flounder/croaker avoid DO<2-3 mg/L) and for the
documented Neuse bottom-water hypoxia (a Phase-2, depth-resolved ModMon target).

Data: CMAST & DUML oyster-site sensors, ~2-min cadence, 2024 warm season.

Outputs (data/processed/): snapshot_gap_summary.json, snapshot_gap.png
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import yaml

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from treestoseas.io.ty_oysterdata import load_env_site_file              # noqa: E402
from treestoseas.model.envelopes import factor_suitability, combine_hsi  # noqa: E402

SURVEY_MONTHS = [6, 9]
GAP_MONTHS = [7, 8]
HYPOXIA = 2.0     # mg/L
LOW_DO = 4.0      # mg/L (oyster suitability starts declining below ~4)


def events(mask, times, min_hours=0.5):
    """Count runs where mask is True lasting >= min_hours. Returns (n, total_h, longest_h, pct_in_gap)."""
    mask = mask.to_numpy(); times = pd.to_datetime(times).reset_index(drop=True)
    if not mask.any():
        return 0, 0.0, 0.0, np.nan
    grp = np.cumsum(np.concatenate([[True], mask[1:] != mask[:-1]]))
    n = 0; total = 0.0; longest = 0.0; gap_h = 0.0
    for g in np.unique(grp[mask]):
        idx = np.where((grp == g) & mask)[0]
        span = (times[idx[-1]] - times[idx[0]]).total_seconds() / 3600
        if span >= min_hours:
            n += 1; total += span; longest = max(longest, span)
            if times[idx[len(idx)//2]].month in GAP_MONTHS:
                gap_h += span
    return n, round(total, 1), round(longest, 1), (round(100*gap_h/total, 1) if total else np.nan)


def site_metrics(df, oy):
    sc = factor_suitability({"temp_C": df.temp_C.to_numpy(), "DO_mgL": df.DO_mgL.to_numpy()}, oy["factors"])
    df = df.copy(); df["HSI"] = combine_hsi(sc, "geometric_mean")
    df = df.dropna(subset=["HSI", "DO_mgL"]).sort_values("datetime").reset_index(drop=True)
    df["month"] = df.datetime.dt.month; df["hour"] = df.datetime.dt.hour
    daily = df.set_index("datetime")
    diel_do = daily["DO_mgL"].resample("1D").agg(lambda s: s.max()-s.min() if len(s) else np.nan)
    n_ev, tot_h, long_h, gap_pct = events(df["DO_mgL"] < HYPOXIA, df["datetime"])
    day = df[df.hour.between(10, 16)]; night = df[(df.hour >= 22) | (df.hour <= 4)]
    in_survey = df.month.isin(SURVEY_MONTHS)
    return df, {
        "span": f"{df.datetime.min().date()}..{df.datetime.max().date()}",
        "n_readings": int(len(df)),
        "pct_DO_lt4": round(100*float((df.DO_mgL < LOW_DO).mean()), 1),
        "pct_DO_lt2_hypoxia": round(100*float((df.DO_mgL < HYPOXIA).mean()), 1),
        "DO_min": round(float(df.DO_mgL.min()), 2),
        "hypoxia_events": n_ev, "hypoxia_hours_total": tot_h, "hypoxia_longest_event_h": long_h,
        "pct_hypoxia_hours_in_JulAug": gap_pct,
        "median_diel_DO_swing_mgL": round(float(diel_do.median()), 2),
        "daytime_median_DO": round(float(day.DO_mgL.median()), 2),
        "nighttime_median_DO": round(float(night.DO_mgL.median()), 2),
        "mean_HSI": round(float(df.HSI.mean()), 3),
        "min_daily_HSI": round(float(daily["HSI"].resample("1D").mean().min()), 3),
        "mean_HSI_JunSep_snapshot": round(float(df.loc[in_survey, "HSI"].mean()), 3),
        "mean_HSI_JulAug_gap": round(float(df.loc[df.month.isin(GAP_MONTHS), "HSI"].mean()), 3),
    }


def main():
    oy = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))["eastern_oyster"]
    out = {}
    frames = {}
    for site, fn in [("CMAST", "AverageCMASTtemp.csv"), ("DUML", "AverageDUMLtemp.csv")]:
        p = os.path.join(ROOT, "data", "raw", fn)
        if not os.path.exists(p):
            continue
        df = load_env_site_file(p, site_fallback=site)
        frames[site], out[site] = site_metrics(df, oy)

    proc = os.path.join(ROOT, "data", "processed"); os.makedirs(proc, exist_ok=True)
    json.dump(out, open(os.path.join(proc, "snapshot_gap_summary.json"), "w"), indent=2)

    hero = "DUML" if "DUML" in frames else next(iter(frames))
    df = frames[hero]; yr = df.datetime.min().year
    fig, (axA, axB) = plt.subplots(2, 1, figsize=(11, 6.6))

    # Panel A: daily DO envelope (min-max band + daily min line) vs the two survey windows
    g = df.set_index("datetime")["DO_mgL"].resample("1D")
    dmin, dmax, dmean = g.min(), g.max(), g.mean()
    axA.fill_between(dmin.index, dmin.values, dmax.values, color="#1f5fa6", alpha=0.18, label="daily DO range")
    axA.plot(dmin.index, dmin.values, color="#0d3b66", lw=1.2, label="daily MIN DO")
    axA.axhline(HYPOXIA, color="red", ls="--", lw=1, label="hypoxia (2 mg/L)")
    for m in SURVEY_MONTHS:
        axA.axvspan(pd.Timestamp(yr, m, 1), pd.Timestamp(yr, m, 28), color="orange", alpha=0.22)
    axA.set_ylabel("DO (mg/L)"); axA.set_ylim(bottom=0)
    axA.set_title(f"{hero} 2024: continuous dissolved oxygen vs. a twice-yearly survey "
                  f"(orange = Jun & Sep). {out[hero]['pct_DO_lt4']}% of the season < 4 mg/L; "
                  f"{out[hero]['hypoxia_events']} hypoxia events; "
                  f"{out[hero]['pct_hypoxia_hours_in_JulAug']}% of hypoxia in Jul-Aug.")
    axA.legend(loc="upper right", fontsize=8, ncol=2)

    # Panel B: one representative summer week at native ~2-min resolution (diel cycling)
    worst = dmin.idxmin(); wk0 = worst - pd.Timedelta(days=3)
    wk = df[(df.datetime >= wk0) & (df.datetime < wk0 + pd.Timedelta(days=7))]
    axB.plot(wk.datetime, wk["DO_mgL"], color="#0d3b66", lw=0.6)
    axB.axhline(HYPOXIA, color="red", ls="--", lw=1)
    axB.set_ylabel("DO (mg/L)"); axB.set_ylim(bottom=0)
    axB.set_title(f"One week around the worst day ({worst.date()}): day/night swings "
                  f"(median {out[hero]['median_diel_DO_swing_mgL']} mg/L) that a single daytime tow can't see "
                  f"(daytime median {out[hero]['daytime_median_DO']} vs night {out[hero]['nighttime_median_DO']} mg/L).")
    fig.tight_layout()
    fig.savefig(os.path.join(proc, "snapshot_gap.png"), dpi=140); plt.close(fig)

    print("=== What a twice-yearly survey misses (oyster-site high-frequency DO) ===")
    for site, m in out.items():
        print(f"\n[{site}] {m['span']}  n={m['n_readings']}")
        for k, v in m.items():
            if k not in ("span", "n_readings"):
                print(f"    {k}: {v}")
    print(f"\nSaved: {os.path.join(proc, 'snapshot_gap.png')} and snapshot_gap_summary.json")


if __name__ == "__main__":
    main()
