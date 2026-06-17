"""Single driver that orchestrates the staged pipeline.

Like the AI Scientist's driver process: it runs each stage, journals every node,
runs the automated review, selects the best node to carry forward, and checks the
stage-transition criterion before advancing. Buggy nodes are recorded, not fatal.
"""
from __future__ import annotations

import os
from datetime import datetime

from .journal import ExperimentJournal
from .review import review_node
from .stages import STAGES, build_context


def _best_metric(node):
    m = node.get("metrics", {}) or {}
    v = m.get("spearman_abs")
    return v if isinstance(v, (int, float)) and v == v else -1.0  # NaN -> -1


class Pipeline:
    def __init__(self, pipeline_cfg, sources_cfg, species_all, runs_root="runs"):
        self.pipeline_cfg = pipeline_cfg
        self.sources_cfg = sources_cfg
        self.species_all = species_all
        self.runs_root = runs_root

    def run(self, bundle, run_name=None):
        run_name = run_name or datetime.now().strftime("run_%Y%m%d_%H%M%S")
        run_dir = os.path.join(self.runs_root, run_name)
        journal = ExperimentJournal(run_dir)

        ctx = build_context(self.pipeline_cfg, self.sources_cfg,
                            self.species_all, bundle)
        ctx["run_dir"] = run_dir
        ctx["journal"] = journal

        rev_cfg = self.pipeline_cfg.get("review", {})
        min_obs = rev_cfg.get("min_observations", 20)
        min_pass = rev_cfg.get("min_overall_to_pass", 3.0)

        journal.write_note(
            f"Trees to Seas pipeline | species={ctx['species_name']} | "
            f"env rows={len(ctx['env_daily'])} | "
            f"mortality rows={0 if ctx.get('mortality') is None else len(ctx['mortality'])}")

        final = {"run_dir": run_dir, "species": ctx["species_name"], "stages": []}

        for stage in STAGES:
            baseline = ctx["carry"].get("baseline_spearman_abs")
            nodes = stage.run(ctx)
            reviewed = []
            for node in nodes:
                node = journal.add_node(node)
                node["review"] = review_node(
                    node, min_observations=min_obs, baseline_metric=baseline)
                reviewed.append(node)

            # pick best: prefer passing nodes, then review score, then metric
            ok_nodes = [n for n in reviewed if n.get("status") == "ok"]
            pool = ok_nodes or reviewed
            best = max(pool, key=lambda n: (n["review"]["overall"], _best_metric(n)))
            best["is_best"] = True
            journal.save_best(best)

            passed, reason = stage.transition(best, ctx)
            journal.write_note(
                f"[{stage.key}] best=node#{best['node_id']} "
                f"review={best['review']['overall']} "
                f"decision={best['review']['decision']} | "
                f"transition={'PASS' if passed else 'HOLD'} ({reason})")

            final["stages"].append({
                "stage": stage.key, "title": stage.title,
                "best_node_id": best["node_id"],
                "status": best.get("status"),
                "review_overall": best["review"]["overall"],
                "metrics": best.get("metrics", {}),
                "transition_passed": bool(passed),
                "transition_reason": reason,
            })

            if best["review"]["overall"] < min_pass and best.get("status") == "ok":
                journal.write_note(
                    f"[{stage.key}] review below pass threshold ({min_pass}); "
                    f"continuing but flagging for revision.")

        journal.save_final_info(final)
        journal.write_note(f"Done. Artifacts in {run_dir}")
        return final
