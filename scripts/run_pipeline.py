"""Run the full staged Trees to Seas pipeline on whatever data is in data/raw/.

Usage:
    python scripts/fetch_data.py        # first, download the data
    python scripts/run_pipeline.py      # then run the pipeline

Writes journaled artifacts to runs/<timestamp>/ (journal.jsonl, final_info.json,
notes.txt, best_node.json, figures/). The pipeline degrades gracefully: with no
data it still runs and journals a 'buggy' viability node telling you what is missing.
"""
from __future__ import annotations

import json
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from treestoseas.io import load_oyster_bundle           # noqa: E402
from treestoseas.pipeline import Pipeline               # noqa: E402


def _load_yaml(name):
    with open(os.path.join(ROOT, "config", name), encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    pipeline_cfg = _load_yaml("pipeline.yaml")
    sources_cfg = _load_yaml("sources.yaml")
    species_all = _load_yaml("species.yaml")

    raw_dir = os.path.join(ROOT, pipeline_cfg["paths"]["data_raw"])
    bundle = load_oyster_bundle(raw_dir, sources_cfg)
    print(f"Loaded bundle keys: {list(bundle.keys())}")

    pipe = Pipeline(pipeline_cfg, sources_cfg, species_all,
                    runs_root=os.path.join(ROOT, pipeline_cfg["paths"]["runs"]))
    final = pipe.run(bundle)

    print("\n=== Stage summary ===")
    for s in final["stages"]:
        print(f"  {s['stage']:<16} review={s['review_overall']:<4} "
              f"transition={'PASS' if s['transition_passed'] else 'HOLD'}  "
              f"({s['transition_reason']})")
    print(f"\nArtifacts: {final['run_dir']}")
    print(json.dumps(final["stages"][-1].get("metrics", {}), indent=2, default=str))


if __name__ == "__main__":
    main()
