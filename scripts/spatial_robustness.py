"""Spatial-robustness pass for the Program 195 headline (complete-oxygen tows).

The proposal's revised headline (docs/results.md s1a) reports a per-tow Spearman rho on the
2,692 tows that measured all three factors. Reviewers flagged that the p<1e-19 is an n-artifact:
4,300 tows are not 4,300 independent observations -- they are spatially clustered (grid strata,
neighbouring tows) and temporally clustered (year). This script converts the proposal's promised
"mixed-effects / block-bootstrap treatment of spatial non-independence" from an IOU into a result.

Two complementary treatments, per species, on the complete-oxygen set:

1. CLUSTER BLOCK-BOOTSTRAP of rho(HSI, CPUE) under four resampling schemes, so the headline
   carries an honest CI instead of a misleading p-value:
     - naive  (resample tows i.i.d.)              -> what the tiny p-value implicitly assumes
     - year   (resample the 26 survey years)      -> temporal pseudoreplication
     - tile   (resample ~0.1deg lat/lon blocks)   -> spatial non-independence
     - grid x year (survey strata x year blocks)  -> spatiotemporal
   NOTE: raw STATIONCODE is near-unique (1,028 codes / 2,692 tows), so it cannot serve as the
   spatial cluster; the survey's ACCSPGRIDCODE strata + lat/lon tiles are the meaningful units.

2. MIXED-EFFECTS LOGISTIC GLMM  presence ~ HSI + (1|tile) + (1|year)  (Bayesian variational fit),
   giving the HSI fixed-effect log-odds with a 95% credible interval that accounts for spatial
   and temporal clustering. (tile is the spatial random intercept, since station codes are
   near-unique; year is the temporal random intercept.)

Output (data/processed/, git-ignored per SEAMAP terms):
    spatial_robustness_summary.csv , spatial_robustness.png
Run: python scripts/spatial_robustness.py
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from treestoseas.io import load_program195                                   # noqa: E402
from treestoseas.model.envelopes import combine_hsi, factor_suitability      # noqa: E402

SPECIES = ["southern_flounder", "atlantic_croaker", "blue_crab"]  # lead with the clean case
N_BOOT = 2000
RNG = np.random.default_rng(20260627)


def block_bootstrap_rho(x, y, groups, n_boot=N_BOOT):
    """95% percentile CI for Spearman rho via cluster resampling of `groups`.

    Resamples whole clusters with replacement (the cluster bootstrap), so within-cluster
    correlation inflates the CI exactly as it should. groups=None -> naive i.i.d. bootstrap.
    """
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = len(x)
    if groups is None:
        rhos = np.empty(n_boot)
        for b in range(n_boot):
            idx = RNG.integers(0, n, n)
            rhos[b] = spearmanr(x[idx], y[idx]).statistic
        return np.nanpercentile(rhos, [2.5, 97.5])
    groups = np.asarray(groups)
    uniq = pd.unique(groups)
    # precompute row indices per cluster
    members = {g: np.where(groups == g)[0] for g in uniq}
    k = len(uniq)
    rhos = np.empty(n_boot)
    for b in range(n_boot):
        pick = uniq[RNG.integers(0, k, k)]
        idx = np.concatenate([members[g] for g in pick])
        rhos[b] = spearmanr(x[idx], y[idx]).statistic
    return np.nanpercentile(rhos, [2.5, 97.5])


def find_extract():
    hits = glob.glob(os.path.join(ROOT, "data", "raw", "*Pamlico Sound Survey*ABUNDANCEBIOMASS*.csv"))
    if not hits:
        sys.exit("No Program 195 extract found in data/raw/.")
    return max(hits, key=os.path.getmtime)


def main():
    df = load_program195(find_extract())
    cfg = yaml.safe_load(open(os.path.join(ROOT, "config", "species.yaml"), encoding="utf-8"))

    latcol = next((c for c in df.columns if "LATITUDE" in c.upper()), None)
    loncol = next((c for c in df.columns if "LONGITUDE" in c.upper()), None)
    keep = ["COLLECTIONNUMBER", "YEAR", "EFFORT", "TEMPBOTTOM", "SALINITYBOTTOM", "BDO",
            "ACCSPGRIDCODE"] + [c for c in (latcol, loncol) if c]
    base = df.drop_duplicates("COLLECTIONNUMBER")[keep].copy()
    base = base[(base.EFFORT > 0) & base.BDO.notna() & base.TEMPBOTTOM.notna()]  # n=2,692 (matches s1a)

    # spatial tile ~0.1 deg
    if latcol and loncol:
        base["tile"] = (base[latcol].round(1).astype(str) + "_" + base[loncol].round(1).astype(str))
    elif latcol:
        base["tile"] = base[latcol].round(1).astype(str)
    else:
        base["tile"] = base["ACCSPGRIDCODE"].astype(str)
    base["gridyear"] = base["ACCSPGRIDCODE"].astype(str) + "_" + base["YEAR"].astype(str)
    print(f"complete-oxygen tows: {len(base)}  | tiles: {base.tile.nunique()} | "
          f"grid strata: {base.ACCSPGRIDCODE.nunique()} | years: {base.YEAR.nunique()} | "
          f"grid*year blocks: {base.gridyear.nunique()}")

    rows = []
    for key in SPECIES:
        caught = df[df["species_key"] == key].groupby("COLLECTIONNUMBER")["NUMBERTOTAL"].sum()
        t = base.copy()
        t["NUMBER"] = t["COLLECTIONNUMBER"].map(caught).fillna(0.0)
        t["cpue"] = t["NUMBER"] / t["EFFORT"]
        t["presence"] = (t["NUMBER"] > 0).astype(int)
        vals = {"temp_C": t["TEMPBOTTOM"].to_numpy(),
                "salinity_ppt": t["SALINITYBOTTOM"].to_numpy(),
                "DO_mgL": t["BDO"].to_numpy()}
        t["HSI"] = combine_hsi(factor_suitability(vals, cfg[key]["factors"]), method="geometric_mean")
        t = t.dropna(subset=["HSI", "cpue"])

        rho = spearmanr(t["HSI"], t["cpue"]).statistic
        ci = {name: block_bootstrap_rho(t["HSI"], t["cpue"], grp)
              for name, grp in [("naive", None), ("year", t["YEAR"].to_numpy()),
                                ("tile", t["tile"].to_numpy()), ("gridyear", t["gridyear"].to_numpy())]}

        # GLMM: presence ~ HSI + (1|tile) + (1|year)
        glmm_coef = glmm_lo = glmm_hi = np.nan
        glmm_note = "ok"
        try:
            from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
            d = t[["presence", "HSI", "tile", "YEAR"]].copy()
            d["year"] = d["YEAR"].astype("category")
            d["tile"] = d["tile"].astype("category")
            m = BinomialBayesMixedGLM.from_formula(
                "presence ~ HSI", {"tile": "0 + C(tile)", "year": "0 + C(year)"}, d)
            r = m.fit_vb()
            # fixed effects order: [Intercept, HSI]
            glmm_coef = float(r.fe_mean[1]); sd = float(r.fe_sd[1])
            glmm_lo, glmm_hi = glmm_coef - 1.96 * sd, glmm_coef + 1.96 * sd
        except Exception as e:  # pragma: no cover
            glmm_note = f"GLMM failed: {type(e).__name__}: {e}"

        excl = (ci["gridyear"][0] > 0)  # CI under the most conservative (spatiotemporal) scheme
        rows.append(dict(species=key, n=len(t), presence_rate=round(t["presence"].mean(), 3),
                         rho=round(rho, 3),
                         ci_naive=f"[{ci['naive'][0]:+.3f},{ci['naive'][1]:+.3f}]",
                         ci_year=f"[{ci['year'][0]:+.3f},{ci['year'][1]:+.3f}]",
                         ci_tile=f"[{ci['tile'][0]:+.3f},{ci['tile'][1]:+.3f}]",
                         ci_gridyear=f"[{ci['gridyear'][0]:+.3f},{ci['gridyear'][1]:+.3f}]",
                         rho_ci_excludes_0_clustered=bool(excl),
                         glmm_HSI_logodds=round(glmm_coef, 3) if np.isfinite(glmm_coef) else None,
                         glmm_HSI_95CI=(f"[{glmm_lo:+.3f},{glmm_hi:+.3f}]" if np.isfinite(glmm_coef) else None),
                         glmm_excludes_0=(bool(glmm_lo > 0 or glmm_hi < 0) if np.isfinite(glmm_coef) else None),
                         glmm_note=glmm_note))
        # stash CIs for plotting
        rows[-1]["_ci"] = ci; rows[-1]["_rho"] = rho

    summ = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows])
    print("\n=== Spatial-robustness: rho(HSI,CPUE) with cluster-bootstrap 95% CIs ===")
    with pd.option_context("display.width", 200, "display.max_columns", 50):
        print(summ.to_string(index=False))

    # ---- forest plot ----
    schemes = ["naive", "year", "tile", "gridyear"]
    colors = {"naive": "#999999", "year": "#4F8A4A", "tile": "#2E5E8C", "gridyear": "#B4503C"}
    fig, axes = plt.subplots(1, len(rows), figsize=(4.4 * len(rows), 3.4), squeeze=False, sharex=True)
    for ax, r in zip(axes[0], rows):
        for i, sc in enumerate(schemes):
            lo, hi = r["_ci"][sc]
            ax.plot([lo, hi], [i, i], color=colors[sc], lw=3, solid_capstyle="round")
            ax.plot([(lo + hi) / 2], [i], "o", color=colors[sc], ms=4)
        ax.axvline(0, color="k", lw=0.8, ls="--")
        ax.plot([r["_rho"]], [len(schemes)], "D", color="k", ms=6)
        ax.set_yticks(list(range(len(schemes))) + [len(schemes)])
        ax.set_yticklabels(schemes + ["point rho"])
        ax.set_title(f"{cfg[r['species']]['common_name']}\nrho={r['_rho']:+.3f} (n={r['n']})")
        ax.set_xlabel("Spearman rho (HSI ~ CPUE), 95% CI")
    fig.suptitle("Headline robustness to spatial/temporal clustering (complete-oxygen tows)")
    fig.tight_layout()
    proc = os.path.join(ROOT, "data", "processed")
    os.makedirs(proc, exist_ok=True)
    figp = os.path.join(proc, "spatial_robustness.png")
    fig.savefig(figp, dpi=130); plt.close(fig)
    summ.to_csv(os.path.join(proc, "spatial_robustness_summary.csv"), index=False)
    print(f"\nSaved: {os.path.join(proc, 'spatial_robustness_summary.csv')}")
    print(f"Saved: {figp}")


if __name__ == "__main__":
    main()
