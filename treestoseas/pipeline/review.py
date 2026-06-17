"""Automated output review -- a rule-based analogue of The AI Scientist's
Automated Reviewer (Lu et al., Nature 2026, SI A.3).

The paper uses an LLM ensemble (NeurIPS-style rubric) to score generated papers
and gate which results advance. Here we use a deterministic rubric tailored to a
habitat-suitability modeling result, so the scaffold runs with no API key. Each
node is scored 1-5 on five dimensions; the mean is the overall score, and a
decision (pass / revise / fail) gates whether the node can be carried forward.

Swap-in point: replace ``review_node`` with an LLM call (e.g. a structured-output
prompt) if you want the richer free-text critique the paper uses.
"""
from __future__ import annotations


def _clip(x, lo=1.0, hi=5.0):
    return max(lo, min(hi, x))


def review_node(node, *, min_observations=20, baseline_metric=None):
    """Score a node 1-5 on five dimensions and return a structured review.

    Dimensions: data_sufficiency, validation_strength, overfit_risk (higher = safer),
    figure_clarity, reproducibility.
    """
    metrics = node.get("metrics", {}) or {}
    strengths, weaknesses = [], []

    # --- data sufficiency ---
    n = metrics.get("n_pairs", metrics.get("n_obs", 0)) or 0
    data_suff = _clip(1.0 + 4.0 * min(n / max(min_observations, 1), 1.0))
    if n >= min_observations:
        strengths.append(f"{n} paired observations (>= {min_observations}).")
    else:
        weaknesses.append(f"Only {n} paired observations (< {min_observations}).")

    # --- validation strength ---
    r = metrics.get("spearman_abs")
    p = metrics.get("p_value")
    if r is None:
        val = 2.0
        weaknesses.append("No validation correlation computed.")
    else:
        val = _clip(1.0 + 4.0 * min(r / 0.6, 1.0))  # |r|>=0.6 saturates
        if p is not None and p < 0.05:
            strengths.append(f"Validation |rho|={r:.2f}, p={p:.3g} (significant).")
        else:
            weaknesses.append(f"Validation |rho|={r:.2f} not significant (p={p}).")
        if baseline_metric is not None and r is not None:
            if r > baseline_metric:
                strengths.append(
                    f"Beats baseline ({r:.2f} > {baseline_metric:.2f}).")
            else:
                weaknesses.append(
                    f"Does not beat baseline ({r:.2f} <= {baseline_metric:.2f}).")

    # --- overfit risk (higher score = safer) ---
    if r is not None and n:
        overfit = 5.0 if n >= 30 else (3.0 if n >= min_observations else 2.0)
        if r > 0.9 and n < min_observations:
            overfit = 1.5
            weaknesses.append("Very high correlation on very few points (overfit risk).")
    else:
        overfit = 3.0

    # --- figure clarity ---
    figs = node.get("figures", []) or []
    fig_clarity = 4.5 if figs else 2.5
    if figs:
        strengths.append(f"{len(figs)} figure(s) produced.")

    # --- reproducibility ---
    repro = 4.5 if (node.get("config") and not node.get("error")) else 2.0
    if node.get("error"):
        weaknesses.append(f"Run errored: {node['error']}")

    scores = {
        "data_sufficiency": round(data_suff, 2),
        "validation_strength": round(val, 2),
        "overfit_risk": round(overfit, 2),
        "figure_clarity": round(fig_clarity, 2),
        "reproducibility": round(repro, 2),
    }
    overall = round(sum(scores.values()) / len(scores), 2)
    decision = "pass" if overall >= 3.0 else ("revise" if overall >= 2.0 else "fail")

    return {
        "scores": scores,
        "overall": overall,
        "decision": decision,
        "strengths": strengths,
        "weaknesses": weaknesses,
    }
