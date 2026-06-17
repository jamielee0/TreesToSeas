"""Experimental journal -- a structured, machine-readable record of every run.

Mirrors the Experimental Journal Structure of The AI Scientist (Lu et al.,
Nature 2026, SI A.2.4): each tree node records its plan/config, results/metrics,
runtime feedback (errors), an automated review (our analogue of the VLM/LLM-judge
commentary), and a stage-transition signal. This gives reproducibility and
auditability, and connects all stages of the pipeline.

Artifacts written per run directory:
    journal.jsonl     - one JSON object per node (append-only log)
    final_info.json   - condensed summary (best node per stage, headline metrics)
    notes.txt         - human-readable narrative (figure descriptions, decisions)
    best_node.json    - the single best node carried forward
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _jsonable(obj):
    """Best-effort conversion of numpy / pandas scalars to JSON-safe types."""
    try:
        import numpy as np
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
    except Exception:
        pass
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj


class ExperimentJournal:
    def __init__(self, run_dir):
        self.run_dir = run_dir
        os.makedirs(run_dir, exist_ok=True)
        self.jsonl_path = os.path.join(run_dir, "journal.jsonl")
        self.notes_path = os.path.join(run_dir, "notes.txt")
        self.nodes = []
        self._counter = 0

    def add_node(self, node):
        """Register a node. Required keys: stage, label, status ('ok'|'buggy').

        Optional: plan, config, metrics, figures, error, review. A ``node_id`` and
        ``timestamp`` are assigned here.
        """
        self._counter += 1
        node = dict(node)
        node.setdefault("plan", "")
        node.setdefault("config", {})
        node.setdefault("metrics", {})
        node.setdefault("figures", [])
        node.setdefault("error", None)
        node.setdefault("review", None)
        node.setdefault("is_best", False)
        node["node_id"] = self._counter
        node["timestamp"] = _now()
        self.nodes.append(node)
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(_jsonable(node)) + "\n")
        return node

    def write_note(self, text):
        with open(self.notes_path, "a", encoding="utf-8") as f:
            f.write(f"[{_now()}] {text}\n")

    def save_best(self, node):
        with open(os.path.join(self.run_dir, "best_node.json"), "w",
                  encoding="utf-8") as f:
            json.dump(_jsonable(node), f, indent=2)

    def save_final_info(self, info):
        with open(os.path.join(self.run_dir, "final_info.json"), "w",
                  encoding="utf-8") as f:
            json.dump(_jsonable(info), f, indent=2)
