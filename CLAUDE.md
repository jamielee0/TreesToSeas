# CLAUDE.md — Trees to Seas (project onboarding)

Read this first. It is the map of the whole project for a fresh session. Deeper detail
lives in `docs/` and in each script's module docstring; the consolidated numeric results
are in **`docs/results.md`** (important, because `data/processed/` outputs are git-ignored).

Last updated: 2026-06-27.

---

## 1. What this project is

A **dynamic physiological habitat-suitability engine** for North Carolina estuarine
fisheries (the Neuse–Pamlico system). Core idea: stop treating estuarine water as a static
backdrop. Each species has known temperature / salinity / dissolved-oxygen tolerances;
drive those tolerance **envelopes** with high-frequency water-quality time series to map
**when and where** a species is inside vs. outside its survivable range — the sub-seasonal,
bottom-water "squeeze" that a twice-a-year trawl survey cannot resolve.

The project is a **proof-of-concept proposal + working code**, not a production system. The
research *process* is modeled on *The AI Scientist* (Lu et al., Nature 2026) — staged,
journaled, auto-reviewed (see `docs/methodology.md`).

People: the user is **Jamie** (student). Collaborators: **Mihir** (student of Dr. **Dan
Rittschof**, Duke Marine Lab, the PI). Data via **Ty** / the Duke Bass Connections oyster
team (`oystersdukebc` on GitHub) and the **UNC Paerl Lab** (ModMon/FerryMon).

## 2. The model (3 layers)

1. **Suitability envelopes** (`treestoseas/model/envelopes.py`): each factor (temp_C,
   salinity_ppt, DO_mgL, pH) → [0,1] via a **trapezoidal** curve with 4 breakpoints
   `[lo_zero, lo_one, hi_one, hi_zero]`. Combined into one **HSI** by **geometric mean**
   (so any single lethal factor → 0; this captures a true squeeze). DO/pH are modeled
   one-sided (more-is-better) with huge upper breakpoints. Envelope values + citations +
   `NC-specific`/`transferred` tags live in **`config/species.yaml`**; full table in
   `docs/tolerance_table.md`.
2. **Degree-days** (`model/degree_days.py`): a *separate* phenology/timing layer (GDD =
   Σ max(0, T−base)). Kept apart from survival because a plain GDD sum breaks down at
   thermal extremes.
3. **Validation** (`model/validate.py` + analysis scripts): the envelopes were calibrated
   from *literature* (never fit to catch data), then tested against independent biology.

Species: **eastern oyster** (anchor — has paired mortality/growth biology) and the three
Program 195 trawl species **blue crab, southern flounder, Atlantic croaker**.

## 3. The headline findings (honest)

Full numbers + interpretation in **`docs/results.md`**. The short version:

- **VALIDATED & ROBUST (the load-bearing result):** suitability from each Program 195 tow's
  own bottom T/S/DO predicts *where* the three species are caught (4,312 tows, 1987–2021):
  croaker ρ=+0.20, crab +0.18, flounder +0.14 (all p<1e-19). Survives ±15% perturbation of
  every threshold in **100%** of 300 draws.
- **THE SQUEEZE IS REAL, SEVERE, AND CURRENT:** depth-resolved ModMon shows Neuse **bottom**
  water hypoxic (DO<2) in **~44% of warm-season profiles vs 0.5% at the surface**, peaking
  in August (croaker bottom-HSI → 0), worst in Jul–Aug **between** the June/September survey
  visits. With the new 2022–2026 sonde data it **persists** (2022–25: 56/41/46/47%) and
  **trends +6.9%/decade** over 1994–2025.
- **HONEST NULLS (these define the scope, don't bury them):**
  - *Annual* abundance is **not** predicted by annual mean habitat (recruitment/fishing
    dominate). Spatial-yes / temporal-no.
  - *Oyster mortality* at the well-flushed CMAST/DUML farm sites is **not** explained by
    T/DO suitability — the more O2-stressed site (DUML) had *higher* survival. The tolerant
    oyster stayed in its adequate range; mortality there is driven by other factors.
  - *Blue crab* within-year occurrence is weakly predicted **by design** (97%/82% of tows
    sit in its salinity/DO plateaus; it's mobile, sex-segregated, avoids hypoxia, buries
    <10 °C). Kept as a tolerance layer, not an occurrence predictor (see species.yaml caveat).

**One-line scope:** this is a *spatial & sub-seasonal habitat-stress lens* — validated for
where mobile species occur and for the bottom-water squeeze — **not** a stock-abundance or
oyster-mortality predictor.

## 4. Repo layout

```
config/        species.yaml (envelopes+citations) · sources.yaml · pipeline.yaml
treestoseas/   importable package (works from repo root; or pip install -e .)
  io/          ty_oysterdata, program195, erddap, usgs, noaa_coops, modmon_excel, harmonize
  model/       envelopes (HSI), degree_days, suitability, validate
  pipeline/    journal, review, stages (1-4), driver  (AI-Scientist-style staged engine)
  viz/         plots
scripts/       fetch_*, run_pipeline, + one script per analysis (see §6)
tests/         14 unit tests (envelopes, degree-days, program195 loader)
docs/          methodology, results, corrected_facts, data_access, tolerance_table, outreach_emails
proposal/      gen.js (the docx generator) + README (how to build the proposal)
data/          raw/ + processed/  — BOTH GIT-IGNORED (see §5)
Trees_to_Seas_Proposal.docx / .pdf   — the committed deliverable
```

## 5. Data (what's in hand, where, status)

`data/raw/` and `data/processed/` are **git-ignored** — a fresh clone has no data. Re-fetch
the public sources with `python scripts/fetch_public_data.py` and `scripts/fetch_data.py`;
the non-public files (Program 195 extract, ModMon 2022–26 Excel) must be re-obtained (see
`docs/data_access.md`). Inventory:

| Dataset | File(s) in data/raw | Coverage | Source / status |
|---|---|---|---|
| Oyster env (high-freq sensors) | `AverageCMASTtemp.csv`, `AverageDUMLtemp.csv` | 2024 season (~2-min) | Ty / oystersdukebc (public GitHub) |
| Oyster mortality / growth | `MortalityContinuous.csv`, `MortalityBySiteBinned.csv`, `growth_rates.csv` | 2024 | same |
| Program 195 catch (Pamlico Sound Survey) | `jmlee.Pamlico Sound Survey.ABUNDANCEBIOMASS.*.csv` | 1987–2021, 3 species | SEAMAP-SA portal (Jamie's account; **don't redistribute**) |
| ModMon (public) | `modmon_all_stations.csv` + `modmon/` (24 stations) | 1994–2021, depth-resolved | SECOORA ERDDAP (public) |
| **ModMon (post-2021, NEW)** | `modmon_NR_2022_2026.xlsx`, `modmon_PS_2022_2026.xlsx` | 2022–2026, S/B labeled | **Paerl Lab (Jack Cheshire)** — emailed |
| USGS discharge | `usgs_neuse_fort_barnwell_discharge.csv` | 1996–2026 | USGS NWIS (public) |
| NOAA water temp (Beaufort) | `noaa_beaufort_8656483_water_temp.csv` | 2000–2026 hourly | NOAA CO-OPS (public) |
| FerryMon | — | **pending** | Tony Whipple (Neuse 2019–24; Pamlico 2025–present) — awaiting delivery |

Loaders for each are in `treestoseas/io/` (one module per source).

## 6. Scripts (each writes to `data/processed/`)

| Script | What it does | Key result |
|---|---|---|
| `fetch_data.py` | download Ty oyster data | — |
| `fetch_public_data.py` | download ModMon(ERDDAP)+USGS+NOAA | — |
| `run_pipeline.py` | the staged AI-Scientist-style pipeline on oyster data | journaled `runs/` |
| `catch_vs_suitability.py` | per-tow HSI vs Program 195 catch | the headline validation |
| `program195_analysis.py` | sharpened: AUC, within-year, seasonal split | Fig `suitability_validation.png` |
| `headline_decomposition.py` | DO-missingness + complete-case + temp-baseline of the headline ρ | flounder clean (multi-axis); croaker/crab thermal |
| `sensitivity.py` | ±15% envelope perturbation robustness | 100% positive |
| `neuse_bottom_hypoxia.py` | surface vs bottom hypoxia by month (ModMon depth) | 44% bottom squeeze |
| `extend_modmon.py` | merge ERDDAP + new sonde → 1994–2026 trend | squeeze persists, +6.9%/decade |
| `oyster_validation.py` | stress→mortality + site contrast | NULL (DUML survives better) |
| `modmon_annual_comparison.py` | annual habitat vs Program 195 abundance | NULL (temporal) |
| `snapshot_gap.py` | high-freq oyster-site DO dynamics vs twice-yearly cadence | diel swings, site contrast |
| `phenology.py` | GDD spawning window + interannual trend | window ~day 140; −2.4 d/decade |
| `suitability_heatmap.py` | Neuse croaker HSI station×month, surface vs bottom | bottom collapses Jun–Sep |

## 7. How to run

```bash
pip install -r requirements.txt
python scripts/fetch_public_data.py     # ModMon(ERDDAP) + USGS + NOAA  (public, no login)
python scripts/fetch_data.py            # Ty oyster data (public GitHub)
# Program 195 + ModMon 2022-26 are not public — see docs/data_access.md
python scripts/catch_vs_suitability.py  # ... and any other analysis script
pytest                                  # 14 tests, no data needed
```

Environment: **Windows**. Use **`PYTHONUTF8=1`** when running scripts that print °C/ρ etc.
PowerShell has **no heredocs** — use the Bash tool for `python - <<'PY'`. The package
imports from repo root via `conftest.py` (no install needed) or `pip install -e .`.

## 8. The proposal (`Trees_to_Seas_Proposal.docx/.pdf`)

Generated by **`proposal/gen.js`** (docx-js / Node). It embeds figures from
`data/processed/` (so run the analyses first) and a SEAMAP data citation. Build steps and
the Word→PDF conversion are in **`proposal/README.md`**. NOTE: the original build ran in a
temp dir; `proposal/gen.js` is the preserved copy — keep it in sync if you regenerate.

## 9. Gotchas

- `data/` and `runs/` are git-ignored; **results are captured in `docs/results.md`** so they
  survive. Figures/summaries in `data/processed/` are regenerable by re-running scripts.
- SEAMAP-SA Program 195 data must **not** be re-posted publicly (their IP protocol).
- ModMon DO is mg/L; ERDDAP `z` is negative-down; the new Excel uses explicit `S`/`B` depth
  labels and qualifier sentinels (−9999/−8888/−7777 → masked to NaN by `modmon_excel.py`).
- `config/species.yaml` is the single source of truth for envelopes; the blue-crab caveat
  there is load-bearing (read it before "fixing" the weak blue-crab signal — it's expected).
- `bluecrab_amd2.pdf` in root is a reference (NC DMF Blue Crab FMP Amendment 2), not output.

## 10. Open items / next steps

- **Pipeline status (academic-research-skills 10-stage):** completed Stage 2.5 INTEGRITY
  (PASS-WITH-WARNINGS) + Stage 3 REVIEW (MINOR_REVISION, 74/100) + Stage 4 REVISE (P0+P1) on
  2026-06-27 — see `docs/stage2.5_integrity_and_stage3_review.md`. The proposal headline was
  corrected (pooled ρ inflated by 39% DO-missingness → lead with flounder/within-year; see
  `headline_decomposition.py` + `docs/results.md` §1a). **Next:** Stage 4.5 FINAL INTEGRITY →
  Stage 5 FINALIZE → Stage 6 PROCESS SUMMARY. **P2 cleanups still open:** stale `species.yaml`
  blue-crab caveat numbers, regenerate `modmon_annual_summary.csv`, `tolerance_table.md`
  blue-crab breakpoints, Cadman & Weinstein p.208, APNEP year/URL, fill `[your name]` + bump
  proposal version.
- ~~Fold the "squeeze still happening + trending up (1994–2026)" finding into the proposal.~~
  **Done** (proposal §5.6 + new Figure 3; +6.9%/decade, p=0.002).
- **FerryMon** (pending from Tony Whipple): adds ferry-transect *spatial* coverage.
- Bring the **Pamlico Sound 2022–26** data + the heatmap fully current (PS data is loaded).
- Longer-term: a **sex-/life-stage-/season-structured blue-crab** model (the correct fix).
- Advisor sign-offs still open (proposal §10): scope, species list, HSI combiner, validation bar.
