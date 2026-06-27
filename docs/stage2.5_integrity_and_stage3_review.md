# Trees to Seas — Stage 2.5 Integrity + Stage 3 Review

*Date: 2026-06-27 · Methodology: academic-research-skills 10-stage pipeline, Stages 2.5 (INTEGRITY gate) + 3 (REVIEW). Scope: proof-of-concept advisor proposal (Dr. Daniel Rittschof, Duke Marine Lab) — judged for significance, soundness of preliminary results, validation design, honesty of stated scope/nulls, and feasibility — not as a finished journal manuscript.*

---

## 1. Executive summary

The integrity gate returns **PASS-WITH-WARNINGS** (no blockers): the citation audit is CLEAR (zero hallucinated/fabricated references across 22 verified items), the data/stats audit is CLEAR on Mode 1 and Mode 3 (every load-bearing number reproduced to the decimal from re-run scripts), and all 7 failure modes are CLEAR. The Stage 3 panel decision is **MINOR_REVISION** at a **consensus score of 74/100** (raw reviewer scores 79/62/78/78/71) — strong, unusually honest work that is **not yet ready to send as-is** because the front-matter claims over-promise relative to the back-matter caveats. The single biggest action: **re-report the headline validation honestly** — lead with the artifact-immune within-year numbers, disclose the 39% structurally-missing bottom-DO that inflates the pooled ρ (croaker collapses +0.20→+0.071, crab +0.18→+0.051 on complete cases; flounder is stable +0.140→+0.153), and state that the multi-factor envelope beats a thermometer only for flounder. This is a re-report-what-you-already-have fix (a focused day), not new analysis or redesign.

---

## 2. Stage 2.5 — INTEGRITY gate

**Gate rule:** BLOCK iff any audit returns a blocker — a Mode-2 hallucinated citation (Total Fabrication / Author-Conference spoof / Mashup / DOI Misdirection), a Mode-1/3 unreproducible or invented headline number, or any of the 7 modes SUSPECTED/FAIL. **None present.** → **PASS-WITH-WARNINGS.**

### 2.1 Citation audit — CLEAR (Mode 2 CLEAR)

**Verdict: CLEAR.** No hallucinated, nonexistent, or wrong-attribution citations. All 22 verified items (5 proposal References + 11 load-bearing `config/species.yaml`/tolerance-table envelope sources + 6 Appendix A / section-2 factual assertions) are real, correctly attributed, and genuinely support the claims made of them. Zero Total Fabrication, zero Plausible-Author/Conference spoofing, zero Mashup/Partial hallucination, zero DOI Misdirection; the DOIs that appear (Nature, Brylawski & Miller f06-011) resolve to the correct papers.

**Load-bearing items verified exactly:**
- **Lu et al. 2026, Nature 651:914–919** — all 8 authors, ordering, volume/issue/pages, DOI 10.1038/s41586-026-10265-5 confirmed; the "Lu, C., Lu, C." correctly distinguishes two separate first authors (Chris Lu, Cong Lu), not a duplication error.
- **Neuheimer & Taggart 2007, CJFAS 64(2):375–385** — the ">92% variance, nine species" claim reproduced verbatim from the abstract; no overclaim (this resolves the data-verifier's UNVERIFIABLE flag).
- **SEAMAP-SA Program 195** — dataset exists exactly as described (stratified-random, June/September since 1987, records T/S/DO/secchi/precip), validating the proposal's central reframed premise.
- **APNEP "2nd-largest estuarine complex in the lower 48"** — verbatim on APNEP's site.
- **NC DEQ 2017 poultry "~3× N, ~6× P" vs swine** — exact.
- Blue-crab envelope shoulders (Selberg 2001, Bell et al. 2003, Cadman & Weinstein 1988, Eby & Crowder 2002) and the flagged citation-corrections (Marshall et al. 2021 J. Thermal Biol. 100:103072; Taylor/Tomasso/Kempton/Smith 2000 JWAS 31:69–72; Brylawski & Miller 2006 with the exact 536 degree-day value) — all real and correctly re-attributed; the project's self-applied corrections are sound.
- Great Lakes / background facts all SUPPORTED: 26 extirpated / 4 globally extinct (DFO Cudmore-Vokey & Crossman 2000, verbatim); alewife 1967 Lake Michigan/Chicago (USGS/EPA); NC #3 hog inventory behind Iowa & Minnesota (USDA NASS 2025); Pamlico "largest embayed estuary in the world" (Britannica).

**Minor citation issues (4, none blocking):**
1. Cadman & Weinstein 1988 JEMBE — pages cited 193-207; authoritative range is 193-**208** (off-by-one trailing page).
2. Taylor & Miller 2001 JEMBE 258:195-214 — authors/species/year/journal/topic confirmed as a real, distinct paper (correctly separated from the 2000 cold-tolerance paper); exact vol:page string not independently displayed on a single publisher page.
3. APNEP CCMP reference entry lacks year/URL (under-specified bibliographic entry; org + claim confirmed).
4. Lake sturgeon "1880s" start-bound marks the harvest peak rather than the collapse proper (sharp decline post-1900); defensible as the exploitation-to-collapse window, not contradicted.

### 2.2 Data / statistics audit — CLEAR (Mode 1 CLEAR, Mode 3 CLEAR)

All non-public input data (Program 195 extract, ModMon 2022–26 Excel) plus public sources were present in `data/raw/`, so every key script was re-runnable. **7 analysis scripts were independently re-run; all exited 0 with no warnings.** Every load-bearing quantitative claim is reproducible from the committed pipeline.

**Scripts re-run and reproduction status:**

| Script | Status | Key outputs (reproduced) |
|---|---|---|
| `program195_analysis.py` | RERAN_OK | n=4312; croaker ρ=0.202 p=4.2e-41 AUC=0.593 within-yr 0.112/63%; crab 0.177 p=1.6e-31 AUC=0.558 within-yr 0.075/58%; flounder 0.140 p=3.0e-20 AUC=0.551 within-yr 0.145/89% — identical to committed CSV |
| `catch_vs_suitability.py` | RERAN_OK | per-tow Spearman croaker +0.202, crab +0.177, flounder +0.140 — matches headline |
| `sensitivity.py` | RERAN_OK | 300 draws, ±15%; frac_positive=1.0 all three; perturbed medians croaker 0.209/crab 0.173/flounder 0.134 (== committed) |
| `neuse_bottom_hypoxia.py` | RERAN_OK | warm-season bottom 44.0% vs surface 0.5%; Aug 53.8% / median DO 1.50 / croaker HSI 0.00; Jul–Aug 50.6% vs Jun+Sep 37.2% |
| `oyster_validation.py` | RERAN_OK | CMAST median survivorship 0.80 vs DUML 0.96, Mann-Whitney p=5.8e-07 |
| `extend_modmon.py` | RERAN_OK | 7681 bottom casts (883 new), hist mean 43%, 2022–25 = 55.9/40.9/46.4/46.8%, trend +6.9%/decade |
| `modmon_annual_comparison.py` | RERAN_OK | system-wide all-negative (croaker −0.100, flounder −0.168, crab −0.341), n=28 — supports "no positive correlation" null |
| (ad hoc) blue-crab plateau recompute | RERAN_OK | 97.2% salinity plateau [3,30]; 82.1% DO≥5; median bottom DO 6.60 — confirms the 97%/82% claim no committed script emits |

**Mode 1 (implementation bug): CLEAR** — re-runs match committed CSVs to the decimal; no suspiciously-round leaks (frac_positive=1.00 is genuine across 300 draws with realistic spread 0.13–0.23); sentinel masking in `modmon_excel.py` is load-bearing and works (raw NR file genuinely contains −8888/−5555 codes in DO across 37 rows; loader masks all <−100 so post-load min DO=0.21 — had they leaked, the squeeze metric would be inflated). 14/14 unit tests pass.

**Mode 3 (hallucinated result): CLEAR** — every prose number maps to a regenerated output; no number was invented.

**Three non-blocking provenance/staleness observations:**
- The 97%/82% blue-crab plateau figures are NOT emitted by any committed script (results.md attributes them to a "dedicated research workflow"); recomputed directly from raw tows and they hold (97.2%/82.1%).
- `config/species.yaml`'s blue-crab caveat carries STALE numbers for the same quantities (ρ +0.16 vs current +0.177; within-year 0.02/57% vs current 0.075/58%) — a config/proposal inconsistency; the PROPOSAL uses the correct current values.
- The committed `modmon_annual_summary.csv` predates the 2022–26 ModMon integration, so the Pamlico blue-crab annual ρ drifts on re-run (+0.138→+0.345); the script is deterministic (input-driven drift, not a bug) and the proposal's only annual claim (system-wide "no positive correlation") is unaffected.

### 2.3 Seven-mode failure checklist

| Mode | Name | Status | Note |
|---|---|---|---|
| 1 | Implementation bug passing self-review | **CLEAR** | Edge-case execution of `envelopes.py` correct; NaN handling, CPUE definition, Spearman/AUC all sound; sentinel masking works; 14/14 tests pass |
| 2 | Hallucinated citation | **CLEAR** | Deferred to citation auditor → CLEAR; species.yaml carries per-factor citations with NC-specific/transferred tags and self-documented corrections |
| 3 | Hallucinated result | **CLEAR** | Every prose number reproduced from a real run |
| 4 | Shortcut reliance | **CLEAR** (closest call) | Actively cleared, not assumed — see below |
| 5 | Bug-as-insight | **CLEAR** | Oyster null rests on an independent, reproducible empirical fact; negative pooled ρ correctly labeled a seasonal artifact and discounted, not inflated |
| 6 | Methodology fabrication | **CLEAR** | Proposal method statements match code exactly; git history shows envelopes never fit to catch (one biology-justified edit that barely moved ρ) |
| 7 | Frame-lock | **CLEAR** | Early commitments honestly revised: Neuse-first pivot openly stated, blue crab demoted to a labeled tolerance layer, spatial-yes/temporal-no stated as a contribution |

**Mode 4 — the most scrutinized, cleared with controls.** For blue crab and croaker the per-tow HSI is effectively a temperature-only axis (salinity/DO suitabilities are ~zero-variance across the well-mixed surveyed water — the project's own plateau-saturation caveat, empirically true). The obvious shortcuts were ruled out by explicit controls: the signal survives **depth-zone stratification** (rules out a depth/offshore gradient: croaker DEEP 0.243 / SHALLOW 0.235; crab DEEP 0.202), survives **partialling raw bottom temperature** (+0.145–0.146 — the envelope *shape* adds signal beyond a thermometer), and survives **partialling season** (+0.20). Flounder is the clean mechanistic case (Sept salinity-suitability ρ +0.213 vs temp +0.044). The project does not over-claim: crab demoted, croaker flagged autumn-concentrated, flounder elevated.

### 2.4 Integrity gate verdict

**PASS-WITH-WARNINGS.** No CONTRADICTED items, zero hallucinated/fabricated citations, all headline numbers reproduce, `block_decision = CLEAR`. Remaining items are minor (bibliographic precision, config staleness) plus one advisor-facing interpretive caveat — none affect a load-bearing claim.

**Single most important pre-advisor action from the integrity gate:** surface the "thermal-axis" honesty point in the cover note, not just the buried caveat — the headline ρ≈0.2 for blue crab and croaker leans predominantly on the temperature envelope; flounder is the only clean multi-axis mechanistic validation. (This is folded into Stage 3 P0-1.)

---

## 3. Stage 3 — REVIEW (peer panel)

Five reviewers; raw scores **79 / 62 / 78 / 78 / 71**. All five rate the honest-nulls discipline, the squeeze finding's soundness, the geometric-mean combiner, and the literature-not-catch calibration as unanimous strengths.

### 3.1 Editor-in-Chief — 79/100, MINOR_REVISION (confidence: high)

Judged as an advisor proposal, this is strong work: timely framing (sub-seasonal bottom-water squeeze invisible to a twice-yearly trawl), and it already carries genuine preliminary validation that the EIC re-ran and reproduced (rho, AUC 0.55–0.59, 44%/0.5% squeeze, +6.9%/decade trend). The standout virtue is intellectual honesty — two nulls reported plainly and used to bound scope. Core weaknesses are contribution-framing, not soundness:
- **P1** — central-hypothesis / results coherence defect: §1 promises the index will "better explain mortality and habitat loss," which §5.5/§5.6 explicitly retract (both are nulls).
- **P1** — the proposal omits its own strongest, most current evidence (squeeze persists 2022–2026, trends +6.9%/decade); still describes ModMon as "1994–2021."
- **P2** — AUC 0.55–0.59 is a weak absolute classifier; the emphatic "very significantly predicts" lets p-values (an n=4,312 artifact) carry weight that effect size cannot.
- **P2** — stale internal cross-references (v0.1 vs repo v0.2; species.yaml blue-crab caveat at 0.02/57% vs proposal 0.075/58%).

### 3.2 Peer Reviewer 1 — Methodology & Statistics — 62/100, MAJOR_REVISION (confidence: high)

Largely sound design and exemplary honest-nulls posture, but a re-run surfaced a **load-bearing statistical flaw**:
- **P0** — the headline pooled ρ depends on inconsistent, non-random missing-data handling. Bottom DO is missing for 1,725/4,417 tows (~39%), structurally missing for ALL of 1987–1995; `combine_hsi()` silently drops the NaN DO factor, so ~1,637 "validation" tows get a 2-factor (T+S) HSI, not the 3-factor index the proposal describes. Splitting by DO availability: croaker ρ=+0.385 in the DO-missing early subset vs +0.074 in the DO-present subset — a Simpson's-style blend. Complete-case collapses croaker +0.20→+0.07, crab +0.18→+0.05; only flounder stable (+0.14→+0.15).
- **P1** — possible single-dominant-gradient confound: flounder's signal is essentially the salinity axis; partial Spearman controlling raw drivers drops crab to +0.020 (n.s.) and croaker to +0.073. Run the leave-one-driver-out ablation the proposal already commits to in §6.
- **P1** — sensitivity and AUC inherit the same pooled dataset, so they propagate rather than test the missingness/confound threats.
- **P2** — no CIs, no multiplicity correction; AUC 0.55–0.59 over-sold; p<1e-19 is an n artifact.

R1's recommendation: elevate the within-year medians (already computed, artifact-immune) as the headline.

### 3.3 Peer Reviewer 2 — Domain expert (estuarine ecology, NC Neuse–Pamlico) — 78/100, MINOR_REVISION (confidence: high)

Re-ran the analyses; every headline number reproduces. Two domain-critical interpretations hold: the bottom-water squeeze is physically real (bottom casts genuinely deeper, ~4 m vs 0.3 m), and the dramatic August croaker bottom-HSI→0 is driven solely by DO at the well-supported NC-specific ~2 mg/L avoidance threshold (Eby & Crowder 2002), not by the weakest parameter. Principal concerns:
- **P1** — repeated factual overstatement that Program 195 samples "June and September only": the extract contains 253 March, 87 July, 41 August, 142 October, 172 December tows (~128 mid-summer tows inside the claimed gap). Squeeze survives, but the absolute phrasing is inaccurate.
- **P1** — p<1e-19 inflated by spatial/temporal pseudoreplication (never acknowledged); the honest signal is the modest effect size; croaker HSI correlates ρ=0.56 with raw bottom temperature.
- **P2** — "anchor" framing inconsistent: oyster is the designated anchor but its validation was null; deliverable bullet 5 still lists "observed oyster mortality overlaid" as a headline figure.

### 3.4 Peer Reviewer 3 — Reader / structure-and-clarity (coastal-management practitioner) — 78/100, MINOR_REVISION (confidence: high)

As a document to win an advisor's sign-off, unusually well-built: logically ordered, visually navigable, leads with hedged validated results. Numbers match the CSVs. Reader-side weaknesses:
- **P1** — framing/evidence mismatch: architected around "validate on oyster sites, then generalize," but the load-bearing result is the Program 195 spatial test while the oyster validation came back null; a skimming reader carries away the wrong mental model.
- **P1** — abstract over-promises: §1 pitches "validated against real biology / predicts oyster survival" with no signal that this test failed; the reader doesn't learn until §5.3/§5.6.
- **P2** — §6 "AI Scientist" workflow section reads as methodology cosplay to a marine-biology advisor; demote to a paragraph.
- **P2** — proposal stale vs its own repo (ModMon "1994–2021"; omits the 2022–2026 persistence + "+6.9%/decade").

### 3.5 Devil's Advocate — adversarial stress-test — 71/100, MINOR_REVISION (confidence: high)

**Strongest counter-argument:** the load-bearing result is "a temperature index wearing a physiology costume." Decomposition: croaker HSI~raw-bottom-temp ρ=+0.555, and HSI~CPUE (+0.20) barely exceeds raw-temp~CPUE (+0.15); for crab, salinity/DO axes contribute almost nothing. A one-line "warmer bottom = more catch" baseline reproduces most of the croaker/crab result. The honest exception is flounder, where salinity-suitability flips the sign of raw salinity (raw −0.144 vs suitability +0.149) — a real mechanism the raw covariate misses.
- **P1** — shortcut/confounding: croaker/crab "validation" is largely a temperature relabeling; the proposal generalizes "validated for where mobile species occur" from essentially one clean case (flounder).
- **P1** — effect oversold: ρ²=2–4% of variance, AUC 0.55–0.59 (barely above chance), framed as "very significantly predicts."
- **P1** — §1 leads with "validated against real biology" anchored to the oyster data, but that test returned null.
- **P2** — "June/September only" imprecise (~13% off-season tows).

**Two a-priori attacks FAILED on inspection (reported in the authors' favor):** (1) the +6.9%/decade trend is NOT a splice artifact — it is +9.0%/decade (p=0.001, R²=0.33) within the homogeneous 1994–2021 ERDDAP record alone, the new sonde reads slightly *lower* not higher, +11.9%/decade restricted to 3–5 m casts (not depth-drift), +8.6%/decade on the consistent early-station panel; (2) the ±15% sensitivity and the 44% vs 0.5% squeeze reproduce and are sound.

### 3.6 Editorial decision

**Decision: MINOR_REVISION** — ready to send to Dr. Rittschof after one focused revision pass (~3–5 days), not before. **Consensus score: 74/100** (severity-weighted, not a mean).

**Rationale.** Four of five reviewers and the integrity gate (PASS-WITH-WARNINGS, no blockers) land at Minor. The lone dissent (R1, MAJOR) rests on a real, independently-reproduced defect — the headline ρ inflated by silent, structurally non-random DO-missingness — that is **fixable by re-reporting existing numbers, not by new data or redesign**. The honest within-year numbers (flounder 0.15/89%, croaker 0.11, crab 0.075) are already computed and immune to the pooling artifact. A defect curable by reframing existing results is Minor-with-a-mandatory-P0, not Major. The piece is **not yet ready to send as-is**: shipping the current §5.5 headline would expose Jamie to exactly the decomposition R1 and the Devil's Advocate performed.

**Disagreement resolution:**
- **SPLIT-1 (decides the verdict): severity of the DO-missingness / pooled-ρ inflation.** R1 → P0/MAJOR; EIC, R2, R3, DA → P1 within Minor; integrity → Mode-4 CLEAR. *Resolved:* R1's *finding* is upheld as a must-fix P0 (reproduced to the digit: pooled +0.202/+0.177 vs complete-case +0.071/+0.051). R1's *MAJOR label* is moderated — MAJOR is reserved for defects needing re-analysis/redesign/new data; this needs none. The integrity Mode-4 CLEAR is not in conflict: it asserts the *direction* survives controls (true), orthogonal to R1's claim that the *magnitude* is inflated (also true). Both hold; R1's substance wins, R1's label does not.
- **SPLIT-2: is the §6 "AI Scientist" framing an asset or a liability?** R3 → reader liability; methodology/EIC → neutral/positive. *Resolved:* perspective difference; defer to R3 (the cross-disciplinary reader is the advisor's vantage). P2 optional — demote, don't delete.

No other conflicts; everything else is corroboration or silence (not opposition).

---

## 4. Consolidated revision roadmap

| ID | Priority | Item | Raised by | Fix type |
|---|---|---|---|---|
| **P0-1** | P0 | Re-report the headline validation honestly: lead with within-year/complete-case numbers, disclose ~39% DO-missingness + the nanmean-drops-NaN combiner, add a raw-temperature baseline + partial correlation per species, and state the multi-factor envelope beats a thermometer **only for flounder** — reposition flounder as load-bearing, croaker/crab as consistency checks | R1 P0; R2 P1; DA P1; integrity Mode-4 | Re-report existing numbers + disclosure (no new analysis) |
| **P0-2** | P0 | Fix the central-hypothesis / Project-Summary over-claim that the results retract (§1 promises "explain mortality and habitat loss" + "predicts oyster survival"; both are nulls). Rewrite hypothesis to match what is validated; add one clause so §1 is self-consistent with §5.6 | EIC P1; R2 P2; R3 P1×2; DA P1 | Wording |
| **P1-3** | P1 | Fold in the squeeze persistence 2022–2026 (56/41/46/47%) + +6.9%/decade trend (with p/R²); defend the ERDDAP-CTD→Paerl-sonde transition as same-program; swap/supplement Fig 2 with `modmon_extended_trend.png` | EIC P1; R3 P2 | Add paragraph + figure (data in hand) |
| **P1-4** | P1 | Correct the "June and September only" overstatement → "predominantly June and September, with sparse opportunistic July–August coverage (n≈128 in 1987–2021)"; restate gap as "no *systematic* Jul–Aug sampling" | R2 P1; DA P2 | Wording |
| **P1-5** | P1 | Decouple significance from magnitude: state variance explained (2–4%), call AUC 0.55–0.59 "weak but consistent discrimination," replace "predicts where" with "occurrence rises modestly and consistently with modeled suitability," add bootstrap CIs, acknowledge spatial non-independence + flag mixed-effects/block-bootstrap as planned work | EIC P2; R1 P2; R2 P1; DA P1 | Wording + light stats |
| **P1-6** | P1 | Reconcile the "anchor" framing with the oyster null (keep oyster as methodological/high-frequency demonstrator; demote claim that paired oyster biology *is* the validation; update deliverable bullet 5) | R2 P2; R3 P1 | Wording (§4.1/§4.2/Objective 5/§8) |
| **P2-7** | P2 | Reconcile cross-document number drift: species.yaml blue-crab caveat 0.02/57%→0.075/58%; regenerate stale `modmon_annual_summary.csv` and `docs/tolerance_table.md` blue-crab breakpoints *(repo files — author's revision pass, outside this review's no-edit scope)* | EIC P2; R2/R3/DA minor; integrity #6/#7 | Repo cleanup |
| **P2-8** | P2 | Bibliographic precision: Cadman & Weinstein pages 193-**208**; confirm Taylor & Miller 2001 pagination; add year+URL to APNEP CCMP entry; surface load-bearing primary sources (Eby & Crowder 2002, NC CHPP 2005, Flowers et al. 2019) into the thin 5-entry reference list | integrity #1–3; R2 minor | Citations |
| **P2-9** | P2 | Fill `[your name]` placeholder; bump version/date (v0.1/17 Jun → repo current 27 Jun) | EIC; R3 | Cosmetic (mandatory before sending) |
| **P2-10** | P2 | Demote the §6 "AI Scientist" workflow section to a short paragraph; reclaim space for the trend figure | R3 P2 | Wording |
| **P2-11** | P2 | Minor clarity: note pH drops out of the T/S/DO validation; flag flounder/croaker degree-day bases as placeholders; soften Great Lakes analogy to motivation; replace "out-of-sample" with "literature-calibrated, never fit to catch"; annotate Fig 1 with ρ values + per-species n / base-rate | R1, R2, EIC, R3, DA minor | Wording |

---

## 5. Recommended next step + mandatory user checkpoint

**Next pipeline step: Stage 4 — REVISE.** The integrity gate is PASS (no block), so the proposal advances to a revision pass executed against the roadmap above. Sequence: P0-1 and P0-2 first (a focused day of re-framing existing numbers — no new analysis), then P1-3 through P1-6 (cheap, all data in hand), then the P2 polish. After REVISE, re-enter a light Stage 2.5 re-check on the changed §5.5 numbers and the §1 hypothesis before the document goes to Dr. Rittschof.

**What the MANDATORY user checkpoint must decide (before REVISE begins):**
1. **Headline reframe (P0-1) — approve the new lead number.** Choose: lead with within-year medians, or report complete-case 3-factor ρ as primary, or report the two DO-eras separately. This changes the proposal's single most prominent claim, so Jamie must sign off on which honest framing to lead with (and confirm flounder becomes the load-bearing case).
2. **Hypothesis rewrite (P0-2) — confirm the validated scope statement.** Approve dropping/demoting "explain mortality and habitat loss" to a tested-and-bounded sub-hypothesis, so the front matter matches the §5.6 honest-scope callout.
3. **Whether to fold in the 2022–2026 trend now (P1-3)** — strongly recommended (strongest "why now" sentence, data in hand), but it touches the figures and version, so confirm scope for this pass vs the next.
4. **Repo-file cleanups (P2-7) are outside this review's no-edit discipline** — confirm Jamie will run them in the revision pass (species.yaml caveat, `modmon_annual_summary.csv`, `tolerance_table.md`) so the repo an advisor may inspect is internally consistent.

**Bottom line:** the science is sound and the honesty is the selling point; the only thing standing between this and the advisor is making the front-matter claims as disciplined as the back-matter caveats already are.

---

## 6. Stage 4 disposition (REVISE — completed 2026-06-27)

User approved **P0 + P1** at the mandatory checkpoint. All items applied to `proposal/gen.js` and the document re-rendered (`Trees_to_Seas_Proposal.docx` → `.pdf`, now 13 pp). Every number written into the proposal was independently re-verified before insertion (see `scripts/headline_decomposition.py` + `docs/results.md` §1a).

| Item | Status | What changed |
|---|---|---|
| **P0-1** Honest headline | ✅ done | §5.5 callout now leads with within-year flounder (0.15, 89% of yrs) + complete-case ρ (flounder +0.15, croaker +0.07, crab +0.05, n=2,692), discloses 39% DO-missingness + the nanmean-drops-NaN combiner, decouples p from effect size (AUC 0.55–0.59 = "weak but consistent"), flags spatial pseudoreplication. New paragraph adds the raw-temperature baseline + partial ρ (envelope beats a thermometer only for flounder). Fig 1 caption reconciled (in-panel ρ are pooled). |
| **P0-2** Hypothesis over-claim | ✅ done | §1 central-hypothesis + fundability rewritten: "predict where mobile demersal species are caught / when the squeeze closes," oyster test reframed as an *informative null* that bounds scope; "validated against independent biology." |
| **P1-3** Squeeze persistence + trend | ✅ done | §5.6 new paragraph (2022–25: 56/41/46/47%; +6.9%/decade, p=0.002, R²=0.28; +9.0%/decade on homogeneous 1994–2021 → not a splice artifact) + new **Figure 3** (`modmon_extended_trend.png`). |
| **P1-4** "June/September only" | ✅ done | §1, §2.4, §5.6, Appendix A: now "predominantly June & September (3,715 of 4,417 tows), sparse July–August (128 tows) → systematic gap at the hypoxia peak." |
| **P1-5** Significance vs magnitude | ✅ done | Folded into the P0-1 rewrite (effect-size language, AUC honesty, planned mixed-effects/block-bootstrap). |
| **P1-6** Oyster "anchor" vs null | ✅ done | Objective 5 + deliverable bullet 5 reframed; oyster kept as methodological/high-frequency demonstrator, not *the* validation. |

**Provenance added:** `scripts/headline_decomposition.py` (reproduces the missingness %, pooled vs complete-case ρ, temp baseline, and partial correlations) → `data/processed/headline_decomposition.csv`; recorded in `docs/results.md` §1a.

**P2 cleanups — completed 2026-06-27** (user chose to do them before Stage 4.5): `species.yaml` blue-crab caveat refreshed to current numbers (pooled +0.18, complete-case +0.05, within-year 0.075/58%) + Cadman & Weinstein → p.208; `tolerance_table.md` blue-crab temp/DO rows synced to the YAML's NC-grounded shoulders; regenerated `modmon_annual_summary.csv`; proposal `[your name]`→Jamie Lee, bumped to v0.2/27 June, APNEP CCMP year(s)+URL added (web-verified), plus three clarity notes (pH excluded from the tow validation, degree-day placeholders, Great Lakes as analogy). *Still optional:* regenerate `suitability_validation.png` to print complete-case ρ in-panel (currently reconciled via the Fig 1 caption).

**Next in pipeline:** Stage 4.5 FINAL INTEGRITY (re-verify from scratch — the revision changed load-bearing numbers) → Stage 5 FINALIZE → Stage 6 PROCESS SUMMARY.

---

## 7. Stage 4.5 FINAL INTEGRITY (re-verified 2026-06-27)

**Gate verdict: PASS-WITH-NOTES** (zero load-bearing issues — clears Stage 5). The revised
artifacts were re-verified from scratch and independently of the Stage 2.5 pass: all
load-bearing scripts were re-run with `PYTHONUTF8=1`, the trend regressions and tow-month /
plateau-saturation counts were recomputed directly from source, the rendered PDF was text-
extracted, and `gen.js` numbers were checked against the regenerated outputs. Everything
reproduces; the only residuals are two cosmetic, non-manuscript items.

**Sub-verdicts:**
- **Data re-verification: CLEAR.** Every quantitative claim in revised `gen.js` (§1, §5.5,
  §5.6, Appendix A, figure captions) reproduces from a from-scratch pipeline re-run.
  headline_decomposition (39.1% DO-missing / 100% pre-1996; complete-case flounder +0.150 /
  croaker +0.074 / crab +0.047, n=2,692; partial +0.159/+0.081/+0.046; HSI~temp flounder
  −0.285; raw-temp flounder +0.008), program195 (within-year flounder 0.145/89%, croaker
  0.112/63%, crab 0.075/58%; AUC 0.551–0.593), neuse_bottom_hypoxia (bottom 44.0% vs surface
  0.5%; Aug 53.8% / median DO 1.50 / croaker HSI 0.00; Jul–Aug 50.6% vs Jun+Sep 37.2%),
  extend_modmon (7,681 casts; hist 43%; 2022–25 = 55.9/40.9/46.4/46.8%), oyster (CMAST 0.80
  vs DUML 0.96, MW p=5.8e-7), sensitivity (frac_positive=1.0 ×3). Independent linregress:
  1994–2025 +6.878%/decade p=0.0021 R²=0.275 (→ +6.9%, p=0.002, R²=0.28); 1994–2021
  +9.029%/decade p=0.0014 (→ +9.0%, p=0.001). Tow counts from the extract keyed on
  `COLLECTIONNUMBER`: total 4,417; June 1921 + Sept 1794 = 3,715; July 87 + Aug 41 = 128.
  Plateau saturation 97.2% / 82.1%. 14/14 unit tests pass.
- **Cross-document consistency: CLEAR.** `gen.js` ↔ `docs/results.md` §1+§1a ↔
  `headline_decomposition.csv` ↔ `program195_validation_summary.csv` ↔ fresh re-run all agree.
  Blue-crab breakpoints identical in `species.yaml` and `tolerance_table.md` (temp_C
  [10,20,30,36]; DO_mgL [2.4,4,1000,2000]). `species.yaml` blue-crab caveat now carries the
  CURRENT numbers (pooled +0.18, complete-case +0.05, within-year median 0.075 / 58%, partial
  +0.05) — this RESOLVES the earlier P2-7 staleness flag (the §6 disposition row labeled
  "Deferred" is now an inaccurate label, not a contradiction). APNEP CCMP entry now "(1994;
  rev. 2012, 2025)" + URL. Cadman & Weinstein "193-208" agree across both files. Rendered PDF
  (13 pp, newer than `gen.js`) contains every revised marker and none of the stale overclaims
  ("explain mortality and habitat loss", "predicts oyster survival", "out-of-sample", "June
  and September only" all absent).
- **7-mode re-check: CLEAR (all 7).** Mode 1 (re-runs match CSVs to the decimal; `combine_hsi`
  NaN-drop / zero-zeros / all-NaN→NaN verified empirically). Mode 2 (no new citations
  introduced). Mode 3 (every prose number maps to a re-runnable output). Mode 4 (the
  temperature-shortcut concern is now disclosed and bounded — envelope beats a thermometer
  only for flounder; crab demoted to a labeled tolerance layer). Mode 5 (DUML-survives-better
  framed as an informative null, seasonal confound discounted). Mode 6 (methods match
  `envelopes.py` exactly). Mode 7 (scope statement coherent; §1 hypothesis matches §5.6 honest
  scope).

**Residual issues:**

| ID | Severity | Issue | Load-bearing? |
|---|---|---|---|
| N1 | Cosmetic (docs-only) | `config/species.yaml` line 66 caveat and `docs/results.md` §7 state blue-crab "median bottom DO 6.7 mg/L"; the direct recompute is **6.60 mg/L**. This figure is **absent from `gen.js`** (verified by grep) — no manuscript claim is affected. 0.1 mg/L rounding/version drift in a supporting doc. | No |
| N2 | Cosmetic (wording) | `gen.js` §5.5 line 195 attaches "(partial ρ = +0.08, positive in ~58–63% of years)" to croaker; croaker's own within-year frac-positive is 63% (top of the stated range), 58% is the blue-crab value. Hedged with "~" and brackets croaker's true 63%, so not factually wrong — it loosely folds in the crab's number. | No |
| N3 | Cosmetic (doc label) | §6 disposition table lists P2-7 (species.yaml caveat refresh) as "Deferred", but the caveat was in fact updated to current, correct numbers. The update RESOLVES the staleness flag; only the "Deferred" label is stale. | No |
| N4 | Bibliographic (one-page) | Cadman & Weinstein 1988 cited as JEMBE 121:193-**208** in both repo files (mutually consistent); the repo's `bluecrab_amd2.txt` "via" source lists 193-**207**. Single trailing-page detail; no science/numeric bearing. Confirm against the original journal at leisure. | No |

**Stage-5 readiness:** **CLEARED.** Stage 4.5 achieves PASS with **zero load-bearing issues**;
the four residuals (N1–N4) are cosmetic/bibliographic and touch no manuscript claim or numeric
result. The revised proposal, numeric record, provenance script/output, envelopes, and rendered
PDF are mutually consistent and fully reproducible from the committed pipeline. The proposal is
cleared to proceed to **Stage 5 FINALIZE**.
