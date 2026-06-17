# Trees to Seas 🌲🌊🦪

**A dynamic physiological-suitability engine for North Carolina coastal fisheries.**

NC fisheries are among the most heavily managed in the US, yet several stocks keep
declining — echoing the Great Lakes collapse. The core idea of this project: stop
treating estuarine water as a static backdrop. Every commercially and ecologically
important species has known temperature, salinity, and dissolved-oxygen tolerances.
Drive those tolerance **envelopes** with high-frequency water-quality time series and
you get a continuous, predictive map of **when and where** each species is inside vs.
outside its survivable range — the sub-seasonal "squeeze" windows that a twice-a-year
trawl survey structurally cannot resolve.

The **proof-of-concept** validates the engine on the **eastern oyster** using the Duke
Bass Connections oyster team's paired dataset (environmental sensors **and** observed
oyster mortality/growth), then generalizes to the data-rich Neuse–Pamlico system.

> Full scientific rationale and the 8-week plan are in the proposal document
> (`Trees_to_Seas_Proposal.docx`). The research workflow is modeled on *The AI
> Scientist* (Lu et al., *Nature* 2026) — see [`docs/methodology.md`](docs/methodology.md).

## Quickstart

```bash
python -m venv .venv && . .venv/Scripts/activate     # Windows; or source .venv/bin/activate
pip install -r requirements.txt

python scripts/fetch_data.py        # download Ty's 2024-2025 oyster data -> data/raw/
python scripts/run_pipeline.py      # run the staged pipeline -> runs/<timestamp>/

pytest                              # run the unit tests (no data needed)
```

The pipeline degrades gracefully: with no data downloaded it still runs and journals
a "buggy" viability node telling you exactly what's missing.

## What the pipeline does (staged, journaled, auto-reviewed)

| Stage | Goal | Output |
|---|---|---|
| **1 Preliminary** | Ingest + QC; coverage report; temperature-only **baseline** | baseline validation metric |
| **2 Tuning** | Full T×S×DO(+pH) **HSI**; pick combiner; must beat baseline | best combiner |
| **3 Execution** | Run across sites; detect summer stress events; figures | `figures/`, stress events |
| **4 Ablation** | Drop each driver; rank contributions | driver-importance ranking |

Every run writes a journal (`journal.jsonl`), a condensed `final_info.json`, a
`best_node.json`, human-readable `notes.txt`, and figures — mirroring The AI Scientist's
experiment journal so results are reproducible and auditable.

## Layout

```
config/        species.yaml (tolerance envelopes), sources.yaml (data), pipeline.yaml
treestoseas/
  io/          Ty oyster loaders + SECOORA ERDDAP / USGS / NOAA CO-OPS (generalization)
  model/       envelopes (HSI), degree_days, suitability, validate (vs. observed biology)
  pipeline/    journal, review (automated reviewer), stages (1-4), driver
  viz/         factor curves, HSI heatmap, stress-vs-mortality overlay
scripts/       fetch_data.py, run_pipeline.py
tests/         envelope + degree-day unit tests
docs/          methodology.md (AI-Scientist mapping), corrected_facts.md
```

## Data sources

- **Primary (in hand):** Duke Bass Connections oyster team — `github.com/oystersdukebc`
  (env sensors: temp, DO, salinity, pH, precip at CMAST, DUML, Stump Sound, Ward Creek;
  response: oyster mortality + growth). Loaded by `treestoseas/io/ty_oysterdata.py`.
- **Generalization:** SECOORA ERDDAP (ModMon, Neuse River Estuary), USGS discharge
  (Fort Barnwell 02091814), NOAA CO-OPS (Beaufort 8656483).

## Status

v0.2 — runnable end-to-end. The tolerance envelopes in `config/species.yaml` are now
**literature-calibrated and adversarially fact-checked**, with per-factor `tags`
(NC-specific vs. transferred), `citations`, and `caveats` (see
[`docs/tolerance_table.md`](docs/tolerance_table.md)). Several values — especially for
blue crab — remain **transferred** from Chesapeake/Gulf/lab studies and should be
revisited with NC-specific data. The SECOORA ERDDAP loader is wired and verified live
(24 ModMon stations, 1994–2021); see [`docs/data_access.md`](docs/data_access.md) for
what's automated vs. what needs a one-time email request.
