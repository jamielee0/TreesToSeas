# Research workflow — modeled on *The AI Scientist*

This project borrows its **process methodology** (not its AI content) from:

> Lu, C., Lu, C., Lange, R. T., Yamada, Y., Hu, S., Foerster, J., Ha, D., & Clune, J.
> (2026). *Towards end-to-end automation of AI research.* **Nature**, 651, 914–919.
> https://doi.org/10.1038/s41586-026-10265-5  (a.k.a. "The AI Scientist")

The AI Scientist runs research as a **single automated driver** advancing through
discrete stages, where each experiment is a journaled "node" that is automatically
reviewed before the best one is carried forward. We adopt that scaffold because it
gives a small project the same three things it gives an autonomous agent:
**reproducibility, auditability, and disciplined go/no-go gates.**

## Mapping: their pipeline → our oyster-suitability pipeline

| The AI Scientist (Lu et al. 2026) | Trees to Seas implementation |
|---|---|
| 4-stage experiment progress manager | `treestoseas/pipeline/stages.py` — Stage 1–4 |
| **Stage 1** preliminary investigation (viability) | Ingest + QC Ty's data; coverage report; temperature-only suitability **baseline** |
| **Stage 2** hyperparameter tuning | Tune the envelopes / pick the HSI **combiner** (geometric-mean vs. Liebig-min); must beat the Stage-1 baseline |
| **Stage 3** research-agenda execution | Run the best HSI across all sites/years; detect summer stress events; headline figures |
| **Stage 4** ablation studies | Leave-one-driver-out: drop T, S, DO, pH in turn; rank each driver's contribution |
| Stage transition on **pre-defined criteria** | `Stage.transition()` predicates (`config/pipeline.yaml`) |
| Each node is a typed object (code, metrics, plots, feedback) | `ExperimentJournal` nodes → `journal.jsonl` |
| `final_info.json`, `all_results.pkl`, `notes.txt` | `final_info.json`, `best_node.json`, `notes.txt` |
| LLM judge selects the **best node** to seed the next stage | `Pipeline.run()` selects best node by review score, carries `best_combiner` forward |
| **Automated Reviewer** (LLM ensemble, NeurIPS rubric) | `review.review_node()` — deterministic 5-dimension rubric (swap in an LLM later) |
| VLM critique of figures | (placeholder) figure QC hook in Stage 3 |
| Buggy nodes recorded, not fatal | every stage `try/except` → 'buggy' node with traceback |

## Why this is the right amount of structure

The paper notes its looser, stage-guided structure "guides the entire empirical
research cycle while maintaining coherence across iterative stages." For a 1–2 month
proof-of-concept that is exactly what we want: enough rigor that every result is
reproducible and gated by an explicit criterion, without the overhead of a rigid
workflow graph. The honest analogue of their automated review here is a transparent
rubric (`review.py`); it can be upgraded to an LLM reviewer with a structured-output
prompt without changing the rest of the architecture.

## What we deliberately did **not** copy

- **No autonomous code generation.** The science (envelope shapes, base temperatures,
  validation design) is human-specified and citable — interpretability is the point.
- **No tree search over thousands of nodes.** Our "tree" is a handful of principled
  configurations (combiners, factor subsets), not an open-ended search.
