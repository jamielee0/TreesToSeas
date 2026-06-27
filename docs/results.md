# Results — consolidated findings (with numbers)

This file records the actual numeric results, because `data/processed/` (figures + summary
CSVs) is git-ignored and regenerable. Each analysis lists its script, what it tests, the
result, and the honest interpretation. Re-run any script to regenerate its figure/CSV.

Last updated: 2026-06-27.

---

## 1. Headline validation — does suitability predict *where* species are caught?
**Scripts:** `catch_vs_suitability.py`, `program195_analysis.py` → `program195_validation_summary.csv`, `suitability_validation.png`

Per Program 195 tow, HSI from the tow's **own bottom T/S/DO** (literature envelopes, never
fit to catch) vs. CPUE, n = 4,312 tows (1987–2021):

| Species | pooled ρ (HSI~CPUE) | p | presence AUC | within-year median ρ | % years positive | June ρ | Sept ρ |
|---|---|---|---|---|---|---|---|
| Atlantic croaker | +0.20 | 4e-41 | 0.59 | 0.11 | 63% | ≈0 | +0.10 |
| Blue crab | +0.18 | 2e-31 | 0.56 | 0.075 | 58% | +0.04 | +0.13 |
| Southern flounder | +0.14 | 3e-20 | 0.55 | **0.15** | **89%** | +0.10 | +0.18 |

**Interpretation:** positive & highly significant for all three. Within-year (controls for
year trends), **flounder is robust**, croaker moderate/autumn-concentrated, **blue crab weak
— and that's expected** (see §7). Flounder, pinned to low-salinity fine sediment, behaves
exactly as the method intends.

## 2. Robustness to envelope uncertainty
**Script:** `sensitivity.py` → `sensitivity_summary.csv`, `sensitivity.png`

±15% Monte-Carlo perturbation of **every** breakpoint (300 draws), recompute ρ:

| Species | baseline ρ | perturbed median | 5–95% | fraction positive |
|---|---|---|---|---|
| Atlantic croaker | 0.20 | 0.21 | 0.19–0.23 | **1.00** |
| Blue crab | 0.18 | 0.17 | 0.13–0.19 | **1.00** |
| Southern flounder | 0.14 | 0.13 | 0.11–0.15 | **1.00** |

**The headline does not depend on the exact (often transferred) thresholds.**

## 3. The summer squeeze (depth-resolved ModMon, 1994–2021)
**Script:** `neuse_bottom_hypoxia.py` → `neuse_bottom_hypoxia_summary.csv`, `neuse_bottom_hypoxia.png`

Neuse profiles, surface (shallowest z) vs bottom (deepest z), fraction hypoxic (DO<2):

| Month | % surface hypoxic | % bottom hypoxic | median bottom DO | median croaker bottom HSI |
|---|---|---|---|---|
| Jun | 0.0 | 39.8 | 3.39 | 0.23 |
| Jul | 0.0 | 47.0 | 2.21 | 0.20 |
| Aug | 0.1 | **53.8** | **1.50** | **0.00** |
| Sep | 2.0 | 34.6 | 3.24 | 0.27 |

Warm-season: **bottom 44% hypoxic vs surface 0.5%.** Jul–Aug (51%) > survey months Jun+Sep
(37%). The surface looks pristine; the bottom — where demersal species live — suffocates,
worst in August, between the survey visits. Measured DO, no model assumptions.

## 4. The squeeze is current + trending (extended to 2026)
**Script:** `extend_modmon.py` → `modmon_extended_summary.csv`, `modmon_extended_trend.png`

ERDDAP (1994–2021) + new Paerl-Lab sonde (2022–2026) = 7,681 Neuse bottom casts.
Historical mean summer bottom-hypoxia = **43%**. Recent full summers:

| Year | n (summer bottom casts) | % hypoxic | median bottom DO |
|---|---|---|---|
| 2022 | 59 | 55.9 | 1.82 |
| 2023 | 88 | 40.9 | 2.85 |
| 2024 | 84 | 46.4 | 2.18 |
| 2025 | 77 | 46.8 | 2.32 |

**Trend 1994–2025: +6.9%/decade** (same-program monitoring, so not a method artifact).
2026 excluded from the trend (file ends 15 Jun, before the Jul–Aug peak).

## 5. Honest null #1 — annual habitat does NOT predict annual abundance
**Script:** `modmon_annual_comparison.py` → `modmon_annual_summary.csv`, `modmon_annual_timeseries.png`

Annual warm-season mean HSI vs Program 195 annual CPUE, ~28 years: **no positive
correlation** (system-wide slightly negative — a spatial-mismatch artifact; the better-matched
Pamlico subset pulls toward 0). **Spatial-yes / temporal-no:** year-to-year abundance is
dominated by recruitment and fishing, not that year's adult habitat.

## 6. Honest null #2 — oyster mortality NOT explained by T/DO suitability
**Script:** `oyster_validation.py` → `oyster_validation_summary.csv`, `oyster_validation.png`

Per-bag interval stress→mortality is **negative** pooled (ρ≈−0.20) — a **seasonal-confounding
artifact** (mortality high early/cool, stress high late/hot), not biology. The clean **site
contrast** (controls for time): the *more* O2-stressed site **DUML had higher survival**
(median 0.96 vs CMAST 0.80, Mann-Whitney p=6e-7). At these well-flushed farm sites the
tolerant oyster stayed in its adequate range; mortality is driven by other factors
(salinity/disease/handling — see the oyster-team email in `docs/outreach_emails.md`).
**Consequence:** the load-bearing validation is the Program 195 spatial occupancy (§1), not
oyster mortality.

## 7. Blue crab — weak within-year is EXPECTED (resolved via research workflow)
A dedicated research workflow verified: re-tuning won't help, because **97% of tows sit in
the crab salinity plateau and 82% in the DO plateau** (Pamlico is well-mixed, median bottom
DO 6.7 mg/L), so those axes are mathematically flat across the surveyed water; and adult
blue crab is euryhaline, mobile, sex-segregated, avoids hypoxic bottom water, and buries
<10 °C. Two NC-grounded realism refinements were applied (temp shoulder→10 °C; DO
shoulder→2.4–4 mg/L; Selberg 2001, Bell et al. 2003/2009, Cadman & Weinstein 1988). Kept as
a **tolerance layer, not an occurrence predictor**. Full rationale + citations in the
`blue_crab` `caveats` of `config/species.yaml`.

## 8. Snapshot gap (high-frequency oyster-site DO)
**Script:** `snapshot_gap.py` → `snapshot_gap_summary.json`, `snapshot_gap.png`

CMAST/DUML ~2-min sensors, 2024. Day/night DO swings are large (median **3.5 mg/L CMAST,
5.0 mg/L DUML**); daytime DO reads ~1–1.3 mg/L higher than the nighttime minimum (a daytime
survey over-reads O2). Site contrast: **DUML 21% of season < 4 mg/L vs CMAST 3%** (6×). For
the tolerant oyster, HSI stayed high (0.95–0.99) — so this site/species shows the *regime*
dynamics a snapshot misses, while the biological squeeze itself is clearest in the Neuse
bottom water (§3) for demersal species.

## 9. Phenology (degree-days)
**Script:** `phenology.py` → `phenology_summary.csv`, `phenology.png`

Oyster spawning window (base 20 °C) opened ~**day-of-year 140** at CMAST in 2024
(season GDD ≈ 1047). Across continuous NOAA Beaufort temp (2000–2025) the opening date
trends ~**−2.4 days/decade** (earlier; warming-consistent, modest).

## 10. When/where heatmap
**Script:** `suitability_heatmap.py` → `suitability_heatmap.png`

Neuse croaker HSI by station (upstream→downstream) × month, surface vs bottom. Surface stays
suitable year-round; **bottom collapses Jun–Sep** through the mid/lower estuary (Aug median
≈ 0). The dynamic "when/where" map of the squeeze.
