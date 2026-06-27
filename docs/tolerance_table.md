# Tolerance-parameter table (literature-calibrated, fact-checked)

Breakpoints are `[lo_zero, lo_one, hi_one, hi_zero]` per factor (see `config/species.yaml`). DO and pH are one-sided (more-is-better). Adversarially verified; see per-species `caveats` in the YAML for soft endpoints and life-stage notes.

# Physiological tolerance envelopes (trapezoidal suitability breakpoints)

Each factor is a trapezoidal membership function `[lo_zero, lo_one, hi_one, hi_zero]`: suitability = 0 at/below `lo_zero`, ramps to 1 by `lo_one`, holds 1 to `hi_one`, ramps back to 0 by `hi_zero`. DO and pH are modeled one-sided ("more is better"): `hi_one = 100`/`1000` and `hi_zero = 200`/`2000` keep suitability at 1 across all observed high values. Units: temp_C = degrees C; salinity_ppt = practical-salinity / parts per thousand; DO_mgL = mg O2/L; pH = pH units.

| Species | Factor | Breakpoints [lo_zero, lo_one, hi_one, hi_zero] | NC-specific? | Source |
|---|---|---|---|---|
| Eastern oyster (*Crassostrea virginica*) **[ANCHOR]** | temp_C | [-2, 20, 30, 36] | Transferred | NC CHPP 2005 (growing 10-30 C, NC); opt 20-30 C LA HSI / Pattillo et al. 1995 (Gulf); upper ~36 C Marshall et al. 2021 J. Thermal Biol. 100:103072 (low-salinity LD50, Gulf) |
| Eastern oyster | salinity_ppt | [2, 14, 30, 40] | NC-specific | NC CHPP 2005 (opt 14-30 ppt, Castagna & Chanley 1973); adult range 2-40 ppt LA HSI |
| Eastern oyster | DO_mgL | [1, 4, 1000, 2000] | NC-specific (lethal); transferred (saturating) | Lethal ~1 mg/L NC CHPP 2005; saturating ~4 mg/L lab rule-of-thumb (Keppel et al. 2016) |
| Eastern oyster | pH | [7.5, 8.0, 100, 200] | Transferred | Waldbusser et al. 2011 Estuaries & Coasts 34:221-231 (Chesapeake/lab) |
| Blue crab (*Callinectes sapidus*) | temp_C | [10, 20, 30, 36] | Transferred (NC-grounded lower shoulder) | Active-occurrence envelope: lower shoulder ~10 C = growth cessation + sediment burial/dormancy (Cadman & Weinstein 1988 JEMBE 121:193-208; Epifanio 2019); opt ~15-30 C; upper ~36 C conservative sustained limit (Tagatz 1969) |
| Blue crab | salinity_ppt | [0, 3, 30, 60] | Transferred | Rome et al. 2005 (opt ~3-15 psu); Sci. Total Environ. 2024 (CTmin 0 / CTmax 62.4 psu) |
| Blue crab | DO_mgL | [2.4, 4, 1000, 2000] | Transferred (NC-grounded avoidance shoulder) | Behavioral-avoidance shoulder ~2.4-4 mg/L (Selberg et al. 2001 NC Neuse; Bell et al. 2003/2009); resting-adult Pcrit far lower ~1.3-1.6 (Das & Stickle 1993; Brill et al. 2015) |
| Blue crab | pH | [7.3, 7.9, 100, 200] | Transferred | Tankersley/Miller et al. 2018 PLOS ONE 13:e0208629 (larval; control 7.91-7.94) |
| Southern flounder (*Paralichthys lethostigma*) | temp_C | [2, 18, 25, 35] | NC-specific (lower/opt); transferred (upper) | Taylor et al. 2000 JWAS 31(1):69-72 + Williams & Deubler 1968 (NC, 2-4 C); FishBase / Luckenbach et al. 2007 (opt 23-25 C, NC); upper ~35 C occurrence-derived |
| Southern flounder | salinity_ppt | [0, 5, 15, 36] | NC-specific (lower/opt); transferred (upper) | Flowers et al. 2019 NC DMF (thrive 5-15 ppt); Smith et al. 1999 (0-10 ppt ~100% survival); upper ~36 ppt occurrence/culture |
| Southern flounder | DO_mgL | [2, 6, 1000, 2000] | NC-specific | Taylor & Miller 2001 JEMBE 258:195-214; Del Toro-Silva et al. 2008 JEMBE 358:113-123 (NC; growth-limited to ~6 mg/L) |
| Southern flounder | pH | [7.0, 7.5, 100, 200] | Transferred (placeholder) | No species-specific value exists (Flowers et al. 2019 gives none); generic estuarine-fish bound |
| Atlantic croaker (*Micropogonias undulatus*) | temp_C | [1, 25, 28, 38] | Transferred | SRAC Pub. 7208 (juvenile 1-38 C); EDIS FA148 / FishBase / JEMBE 2018 (opt 25-28 C) — *original 0.6 C corrected to 1 C* |
| Atlantic croaker | salinity_ppt | [0, 5, 20, 75] | Transferred | SRAC Pub. 7208 (field 0.2-75 g/L; best growth ~5 ppt, opt 5-20 ppt) |
| Atlantic croaker | DO_mgL | [2, 4, 1000, 2000] | NC-specific (avoidance ~2); transferred (saturating ~4 est.) | Eby & Crowder 2002 CJFAS 59:952-965 (Neuse River NC, avoidance ~2.3 mg/L); saturating ~4 mg/L unsupported estimate |
| Atlantic croaker | pH | [6.0, 6.5, 100, 200] | Transferred (interpretive) | SRAC Pub. 7208 (cultured pH 6.0-9.3 with little effect; 6.0 actually tolerated — placeholder) |

**Degree-days**

| Species | base_C | Event | Note |
|---|---|---|---|
| Eastern oyster | 20.0 | spawning_onset | Spawning >~20 C, mass spawning >~25 C (EOBRT 2007; Stanley & Sellers 1986) — transferred |
| Blue crab | 10.8 | molt_growth_onset | Growth-torpor temperature (Tmin); Brylawski & Miller 2006 Can. J. Fish. Aquat. Sci. 63(6):1298-1308 — value verified |
| Southern flounder | 10.0 | juvenile_growth | Placeholder — no published degree-day base for this species |
| Atlantic croaker | 10.0 | juvenile_growth | Placeholder — no published degree-day base for this species |

**Key caveats**

- **Anchor:** eastern oyster is the primary POC species (paired mortality + growth data).
- **Citation fixes applied:** Marshall et al. 2021 = *J. Thermal Biology* 100:103072 (oyster temp); Brylawski & Miller 2006 = *Can. J. Fish. Aquat. Sci.* 63(6):1298-1308 (crab degree-days); flounder cold-tolerance = Taylor, W.E., Tomasso, Kempton & Smith 2000 *JWAS* 31(1):69-72.
- **Soft/uncertain endpoints (conservative choices):** oyster upper-lethal 36 C is salinity-dependent (low-salinity acute LD50; rises to 40-44 C at 20 ppt); crab upper-lethal 36 C is a sustained-field limit, not acute CTmax (~40 C); oyster DO saturating 4 mg/L and croaker DO saturating 4 mg/L are weakly-sourced/estimated; croaker lower-lethal corrected from an unsourced 0.6 C to 1 C; croaker pH 6.0/6.5 and flounder pH/degree-days are placeholders, not measured thresholds.
- **DO and pH are one-sided** (more-is-better); pH lower-bounded for the calcifying oyster, near-irrelevant for the finfish/crab.
- **Life-stage:** larvae/spat/eggs are consistently more sensitive (narrower salinity, higher hypoxia/acidification sensitivity) than adults across all four species; envelopes here are weighted to the stage each dataset best covers.
