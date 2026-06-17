"""The four pipeline stages, mirroring The AI Scientist's experiment progress
manager (Lu et al., Nature 2026):

  Stage 1  Preliminary investigation / viability   (ingest, QC, naive baseline)
  Stage 2  Envelope tuning / calibration           (full HSI vs. baseline; pick combiner)
  Stage 3  Research execution                       (run across sites; headline figures)
  Stage 4  Ablation / sensitivity                   (drop each driver; rank contributions)

Each stage's ``run`` returns a list of journal nodes; ``transition`` decides whether
the stage's criterion (config/pipeline.yaml) is met. Every stage degrades gracefully:
on error it returns a 'buggy' node carrying the traceback, exactly as the paper marks
buggy tree nodes rather than crashing the pipeline.
"""
from __future__ import annotations

import os
import traceback
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from ..io import to_canonical_columns, qc_clip, resample_daily
from ..model import suitability_timeseries, validate_against_mortality, detect_stress_events


# --------------------------------------------------------------------------- #
# Context
# --------------------------------------------------------------------------- #
def build_context(pipeline_cfg, sources_cfg, species_all, bundle):
    """Assemble the shared context the stages operate on."""
    # pick the anchor species (eastern oyster) — the one with paired biology
    anchor_name, anchor_cfg = None, None
    for name, cfg in species_all.items():
        if cfg.get("anchor"):
            anchor_name, anchor_cfg = name, cfg
            break
    if anchor_cfg is None:
        anchor_name = "eastern_oyster"
        anchor_cfg = species_all.get(anchor_name, next(iter(species_all.values())))

    env = bundle.get("env")
    if env is not None and len(env):
        env = to_canonical_columns(env, sources_cfg.get("canonical_vars", {}))
        env = qc_clip(env)
        env_daily = resample_daily(env, datetime_col="datetime", site_col="site")
    else:
        env_daily = pd.DataFrame()

    return {
        "pipeline_cfg": pipeline_cfg,
        "sources_cfg": sources_cfg,
        "species_name": anchor_name,
        "species_cfg": anchor_cfg,
        "env_daily": env_daily,
        "mortality": bundle.get("mortality"),
        "growth": bundle.get("growth"),
        "carry": {},
        "run_dir": ".",
    }


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _reduced_cfg(species_cfg, keep, available_cols):
    sp = dict(species_cfg)
    sp["factors"] = {k: v for k, v in species_cfg["factors"].items()
                     if (keep is None or k in keep) and k in available_cols}
    return sp


def _hsi(ctx, keep, combiner):
    cols = list(ctx["env_daily"].columns)
    sp = _reduced_cfg(ctx["species_cfg"], keep, cols)
    if not sp["factors"]:
        raise ValueError(f"No usable factors among {keep} in columns {cols}")
    return suitability_timeseries(ctx["env_daily"], sp, combiner=combiner)


def _validate(ctx, hsi_df):
    mort = ctx.get("mortality")
    if mort is None or not len(mort):
        return {"spearman_abs": np.nan, "spearman_r": np.nan,
                "p_value": np.nan, "n_pairs": 0}
    res = validate_against_mortality(hsi_df, mort, response_col="MortalityRate",
                                     hsi_site_col="site", hsi_datetime_col="datetime")
    return {k: res[k] for k in ("spearman_abs", "spearman_r", "p_value", "n_pairs")}


def _coverage(env_daily):
    if not len(env_daily):
        return {}
    cov = {
        "n_days": int(env_daily["datetime"].nunique()),
        "sites": sorted(map(str, env_daily.get("site", pd.Series(["all"])).unique())),
        "date_min": str(env_daily["datetime"].min()),
        "date_max": str(env_daily["datetime"].max()),
    }
    for c in ("temp_C", "salinity_ppt", "DO_mgL", "pH"):
        if c in env_daily.columns:
            cov[f"missing_frac_{c}"] = round(float(env_daily[c].isna().mean()), 3)
    return cov


# --------------------------------------------------------------------------- #
# Stages
# --------------------------------------------------------------------------- #
def stage1_preliminary(ctx):
    try:
        env = ctx["env_daily"]
        if not len(env):
            return [{"stage": "s1_preliminary", "label": "viability",
                     "status": "buggy",
                     "error": "No environmental data in data/raw — run scripts/fetch_data.py.",
                     "plan": "Ingest + QC; compute coverage and a temperature-only baseline."}]
        cov = _coverage(env)
        # temperature-only suitability baseline
        base_hsi = _hsi(ctx, keep=["temp_C"], combiner="liebig_min")
        base = _validate(ctx, base_hsi)
        ctx["carry"]["baseline_spearman_abs"] = base.get("spearman_abs")
        return [{
            "stage": "s1_preliminary", "label": "coverage+baseline", "status": "ok",
            "plan": "Ingest Ty oyster env + mortality; QC; daily resample; "
                    "temperature-only suitability baseline vs observed mortality.",
            "config": {"combiner": "liebig_min", "factors": ["temp_C"]},
            "metrics": {**base, "coverage": cov},
        }]
    except Exception:
        return [{"stage": "s1_preliminary", "label": "viability", "status": "buggy",
                 "error": traceback.format_exc()}]


def stage2_tuning(ctx):
    nodes = []
    for combiner in ("geometric_mean", "liebig_min"):
        try:
            hsi = _hsi(ctx, keep=None, combiner=combiner)  # all available factors
            m = _validate(ctx, hsi)
            factors = [c.replace("suit_", "") for c in hsi.columns if c.startswith("suit_")]
            nodes.append({
                "stage": "s2_tuning", "label": f"full-HSI:{combiner}", "status": "ok",
                "plan": f"Full multi-factor HSI ({combiner}) vs observed mortality.",
                "config": {"combiner": combiner, "factors": factors},
                "metrics": m,
            })
        except Exception:
            nodes.append({"stage": "s2_tuning", "label": f"full-HSI:{combiner}",
                          "status": "buggy", "error": traceback.format_exc()})
    return nodes


def stage3_execution(ctx):
    try:
        combiner = ctx["carry"].get("best_combiner", "geometric_mean")
        hsi = _hsi(ctx, keep=None, combiner=combiner)
        pcfg = ctx["pipeline_cfg"]["hsi"]
        events = detect_stress_events(
            hsi, threshold=pcfg["stress_threshold"],
            min_consecutive=pcfg["stress_min_consecutive_days"])
        m = _validate(ctx, hsi)

        figures = []
        try:
            from ..viz import plot_hsi_heatmap, plot_stress_with_mortality, plot_factor_curves
            fig_dir = os.path.join(ctx["run_dir"], "figures")
            os.makedirs(fig_dir, exist_ok=True)
            figures.append(plot_factor_curves(
                ctx["species_cfg"], os.path.join(fig_dir, "factor_curves.png")))
            figures.append(plot_hsi_heatmap(
                hsi, os.path.join(fig_dir, "hsi_heatmap.png")))
            if ctx.get("mortality") is not None and len(ctx["mortality"]):
                figures.append(plot_stress_with_mortality(
                    hsi, ctx["mortality"], os.path.join(fig_dir, "stress_vs_mortality.png")))
        except Exception:
            # figures are best-effort; never fail the stage on a plotting error
            figures = [f for f in figures if f]

        return [{
            "stage": "s3_execution", "label": "full-run", "status": "ok",
            "plan": "Run best HSI across all sites; detect summer stress events; "
                    "produce headline figures.",
            "config": {"combiner": combiner,
                       "stress_threshold": pcfg["stress_threshold"]},
            "metrics": {**m, "n_stress_events": int(len(events))},
            "figures": [f for f in figures if f],
        }]
    except Exception:
        return [{"stage": "s3_execution", "label": "full-run", "status": "buggy",
                 "error": traceback.format_exc()}]


def stage4_ablation(ctx):
    try:
        combiner = ctx["carry"].get("best_combiner", "geometric_mean")
        full = _validate(ctx, _hsi(ctx, keep=None, combiner=combiner))
        full_metric = full.get("spearman_abs")
        present = [c for c in ("temp_C", "salinity_ppt", "DO_mgL", "pH")
                   if c in ctx["env_daily"].columns]
        ranking = []
        for drop in present:
            keep = [c for c in present if c != drop]
            try:
                m = _validate(ctx, _hsi(ctx, keep=keep, combiner=combiner))
                contribution = (full_metric - m.get("spearman_abs")
                                if full_metric is not None and m.get("spearman_abs") is not None
                                else None)
                ranking.append({"dropped": drop,
                                "spearman_abs_without": m.get("spearman_abs"),
                                "contribution": contribution})
            except Exception:
                ranking.append({"dropped": drop, "error": "failed"})
        ranking.sort(key=lambda r: (r.get("contribution") is None, -(r.get("contribution") or 0)))
        return [{
            "stage": "s4_ablation", "label": "leave-one-driver-out", "status": "ok",
            "plan": "Drop each environmental driver; rank by loss in validation skill.",
            "config": {"combiner": combiner, "drivers": present},
            "metrics": {"full_spearman_abs": full_metric, "ranking": ranking},
        }]
    except Exception:
        return [{"stage": "s4_ablation", "label": "ablation", "status": "buggy",
                 "error": traceback.format_exc()}]


# --------------------------------------------------------------------------- #
# Transition predicates
# --------------------------------------------------------------------------- #
def _t_s1(best, ctx):
    return (best is not None and best.get("status") == "ok",
            "pipeline ran end-to-end and recorded a baseline")


def _t_s2(best, ctx):
    if best is None or best.get("status") != "ok":
        return False, "no successful full-HSI node"
    r = best["metrics"].get("spearman_abs")
    base = ctx["carry"].get("baseline_spearman_abs")
    ctx["carry"]["best_combiner"] = best["config"].get("combiner", "geometric_mean")
    if r is None:
        return False, "no validation metric (need mortality data)"
    if base is None or np.isnan(base):
        return True, f"full HSI validated (|rho|={r:.2f}); no baseline to beat"
    ok = r >= base
    return ok, f"full |rho|={r:.2f} vs baseline {base:.2f}"


def _t_s3(best, ctx):
    return (best is not None and best.get("status") == "ok",
            "full run complete and figures produced")


def _t_s4(best, ctx):
    return (best is not None and best.get("status") == "ok",
            "driver contributions ranked")


@dataclass
class Stage:
    key: str
    title: str
    run: Callable
    transition: Callable


STAGES = [
    Stage("s1_preliminary", "Preliminary investigation / viability",
          stage1_preliminary, _t_s1),
    Stage("s2_tuning", "Envelope tuning / calibration", stage2_tuning, _t_s2),
    Stage("s3_execution", "Research execution", stage3_execution, _t_s3),
    Stage("s4_ablation", "Ablation / sensitivity", stage4_ablation, _t_s4),
]
