const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType, ShadingType,
  Footer, Header, PageNumber, TableOfContents, PageBreak, ExternalHyperlink, ImageRun,
} = require("docx");

const OUT = "C:/Users/pingp/Documents/fisheries/Trees_to_Seas_Proposal.docx";
const FIG = "C:/Users/pingp/Documents/fisheries/data/processed/suitability_validation.png";
const FIG2 = "C:/Users/pingp/Documents/fisheries/data/processed/neuse_bottom_hypoxia.png";
const FIG3 = "C:/Users/pingp/Documents/fisheries/data/processed/modmon_extended_trend.png";
const CONTENT_W = 9360; // US Letter, 1in margins

// ---------- helpers ----------
const P = (text, opts = {}) =>
  new Paragraph({ spacing: { after: 120, line: 276 }, ...opts,
    children: typeof text === "string" ? [new TextRun(text)] : text });

const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const B = (t) => new TextRun({ text: t, bold: true });
const I = (t) => new TextRun({ text: t, italics: true });
const T = (t) => new TextRun(t);

const bullet = (children) =>
  new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 80 },
    children: typeof children === "string" ? [new TextRun(children)] : children });
const numItem = (children) =>
  new Paragraph({ numbering: { reference: "nums", level: 0 }, spacing: { after: 80 },
    children: typeof children === "string" ? [new TextRun(children)] : children });

const border = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };

function cell(content, width, { head = false } = {}) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    margins: { top: 60, bottom: 60, left: 110, right: 110 },
    shading: head ? { fill: "D5E8F0", type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({ spacing: { after: 0 },
      children: [new TextRun({ text: String(content), bold: head })] })],
  });
}

function makeTable(rows, colWidths) {
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: rows.map((cells, ri) => new TableRow({
      tableHeader: ri === 0,
      children: cells.map((c, ci) => cell(c, colWidths[ci], { head: ri === 0 })),
    })),
  });
}

const callout = (runs) => new Paragraph({
  spacing: { before: 120, after: 160 },
  shading: { fill: "EAF3E9", type: ShadingType.CLEAR },
  border: { left: { style: BorderStyle.SINGLE, size: 18, color: "4F8A4A", space: 8 } },
  children: runs,
});

// ---------- document body ----------
const body = [];

// Title block
body.push(new Paragraph({ spacing: { after: 60 }, children: [
  new TextRun({ text: "Trees to Seas", bold: true, size: 44 }) ] }));
body.push(new Paragraph({ spacing: { after: 60 }, children: [
  new TextRun({ text: "A Dynamic Physiological-Suitability Engine for North Carolina Coastal Fisheries", size: 28, bold: true, color: "2E5E8C" }) ] }));
body.push(P([ I("Proof-of-concept proposal and modeling roadmap") ]));
body.push(P([ B("Prepared for: "), T("Dr. Daniel Rittschof, Duke University Marine Laboratory") ]));
body.push(P([ B("In collaboration with: "), T("the Duke Bass Connections oyster team (data via Ty; GitHub: oystersdukebc)") ]));
body.push(P([ B("Prepared by: "), T("Jamie Lee") ]));
body.push(P([ B("Date: "), T("27 June 2026     "), B("Version: "), T("0.2 (companion to the treestoseas v0.2 repository)") ]));
body.push(new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E5E8C", space: 2 } }, children: [] }));

body.push(new Paragraph({ spacing: { before: 120 }, children: [ B("Contents") ] }));
body.push(new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }));
body.push(new Paragraph({ children: [new PageBreak()] }));

// 1. Summary
body.push(H1("1. Project summary"));
body.push(P([
  T("North Carolina's fisheries are among the most heavily managed in the United States, yet several stocks keep declining — a pattern that echoes the Great Lakes collapse. The root limitation is that management treats estuarine water as a "),
  B("static backdrop"), T(" and regulates species one at a time within fixed salinity zones. But every commercially and ecologically important species has known temperature, salinity, and dissolved-oxygen tolerances, and estuarine conditions swing week to week. This project turns water into a "),
  B("dynamic, predictive habitat layer"),
  T(": drive per-species physiological "), B("suitability envelopes"),
  T(" with high-frequency water-quality time series to map "),
  B("when and where"),
  T(" each species is inside vs. outside its survivable range — resolving the sub-seasonal heat-and-hypoxia “squeeze” windows that a trawl survey sampled mainly in early summer and early fall structurally cannot capture."),
]));
body.push(P([
  B("Why now, and why this is fundable: "),
  T("the proof-of-concept does not rest on a theoretical argument. It is "),
  B("validated against independent biology"),
  T(". The Duke Bass Connections oyster team has collected paired data — high-frequency environmental sensors (temperature, dissolved oxygen, salinity, pH, precipitation) "),
  I("and"),
  T(" observed oyster mortality and growth — at working farm sites, which let us test directly whether a mechanistic stress index predicts oyster survival. That paired test returned an "),
  B("informative null"),
  T(" (the tolerant oyster stayed within its adequate range at these well-flushed sites; see §5.3 and §5.6) — which usefully bounds the tool's scope. The validation that "),
  I("held"),
  T(" is independent and at the population scale: the same literature-calibrated index predicts "),
  B("where"),
  T(" trawl-survey species are actually caught across the Neuse–Pamlico system, and resolves a severe, intensifying bottom-water summer squeeze the survey cannot see (§5.5–5.6)."),
]));
body.push(callout([
  B("Central hypothesis. "),
  T("For estuarine species, sub-seasonal variation in physiological habitat suitability (temperature × salinity × dissolved oxygen) is large, spatially structured, and largely invisible to a survey sampled mainly twice a year; a continuous suitability/stress index built from existing high-frequency data will reveal recurring summer hypoxia-and-heat squeeze windows, and will predict where mobile demersal species are caught and when the bottom-water squeeze closes — information that static, salinity-zone, single-species management cannot resolve. (As the results below show, the index validates as a spatial and sub-seasonal habitat-stress lens; it is deliberately not advanced as a stock-abundance or mortality predictor.)"),
]));

// 2. Background
body.push(H1("2. Background and motivation"));
body.push(H2("2.1 Heavily managed, still declining"));
body.push(P("NC regulates each species individually, partitioned by static salinity zones, and leans on fishery-independent trawl surveys sampled only a few times per year. The result is biomass estimates built on temporally sparse snapshots, while the conditions that actually determine survival — summer heat, hypoxia, drought-driven salinity spikes, post-rainfall stratification — vary on the scale of days."));
body.push(H2("2.2 The Great Lakes cautionary parallel"));
body.push(P("The Great Lakes lost numerous fish taxa (26 extirpated from at least one lake, four globally extinct) under cumulative stressors plus species-by-species management. Lake sturgeon collapsed around the 1880s–1920s and never recovered. The lesson is not a single cause but the failure of a management paradigm that ignored cumulative, interacting stressors — exactly the blind spot a dynamic suitability model is built to address. We carry the Great Lakes as a cautionary analogy that motivates the approach, not as a mechanistic precedent for North Carolina."));
body.push(H2("2.3 The “trees to seas” land-use drivers"));
body.push(P("NC's coastal plain is forest on a ~25-year harvest rotation, and the state is a top-three hog producer with dense poultry operations; clearing and runoff drive siltation, nutrient loading, and summer hypoxia that smother oyster reefs and silt over spawning beds. These drivers motivate why suitability collapses occur where and when they do — they are the context, while the model focuses on the water-quality-to-physiology link."));
body.push(H2("2.4 The real, defensible gap (an important correction)"));
body.push(callout([
  B("Do not pitch this as “the survey ignores the water.” "),
  T("NC DMF Program 195 (the Pamlico Sound trawl survey) is "), B("stratified-random"),
  T(" and "), B("does record"),
  T(" surface/bottom temperature, salinity, dissolved oxygen, secchi (turbidity), and precipitation at every grid. The defensible, verifiable gap is "),
  B("coarse warm-season temporal resolution (effort concentrated in June and September, with only sparse July–August coverage) and under-use of those covariates"),
  T(" — not non-measurement. The whole proposal is built on that solid footing. (See Appendix A.)"),
]));

// 3. Objectives
body.push(H1("3. Objectives"));
body.push(numItem("Lock the critique to the verified gap (coarse warm-season snapshot resolution + covariate under-use), not the false “no covariates measured” claim."));
body.push(numItem("Stand up a reproducible Python pipeline that ingests the oyster team's environmental + biological data with QC and daily resampling."));
body.push(numItem("Compile a cited tolerance table (temperature, salinity, DO, pH min/optimum/max, plus degree-day base temperatures) for the focal species, flagging NC-specific vs. transferred values."));
body.push(numItem("Implement per-species suitability envelopes f(T,S,DO,pH) → [0,1] combined into a geometric-mean Habitat Suitability Index, plus a separate degree-day phenology layer."));
body.push(numItem("Validate the index against independent biology — observed oyster mortality/growth at the farm sites (an informative null; see §5.5–5.6) and, as the load-bearing test, where species are caught in the Program 195 trawl survey — and quantify the summer squeeze windows the snapshot survey misses."));
body.push(numItem("Package everything as a runnable, journaled repository so additional species, sites, and the Neuse–Pamlico data plug in later."));

// 4. Data
body.push(H1("4. Data — the key asset"));
body.push(H2("4.1 Primary (in hand): the Duke Bass Connections oyster dataset"));
body.push(P([ T("Source: "), new ExternalHyperlink({ link: "https://github.com/oystersdukebc", children: [ new TextRun({ text: "github.com/oystersdukebc", style: "Hyperlink" }) ] }),
  T(". Sites: CMAST (Morehead City), DUML (Beaufort), and — in 2025–26 — Stump Sound and Ward Creek.") ]));
body.push(makeTable([
  ["Data", "Variables", "Role in the model"],
  ["AverageCMASTtemp.csv / AverageDUMLtemp.csv", "Water temperature, dissolved oxygen (hourly), by site", "Environmental drivers"],
  ["environmental_data_{daily,hourly,5minute}.csv", "Long-format: temperature, salinity, pH, precipitation", "Environmental drivers (multi-resolution)"],
  ["2025–26 XLSX (DO, pH, Salinity, Precip; Cleaned/ per site)", "DO, Temp, pH, salinity (conductivity-derived)", "Environmental drivers (4 sites)"],
  ["MortalityContinuous.csv / OysterMortalityData_Processed.csv", "Per-bag survivorship over a biweekly census, by strain & site", "Response variable (validation target)"],
  ["MortalityBySiteBinned.csv", "Survivorship by site/date with N, sd, se, ci", "Response variable (aggregated)"],
  ["growth_rates.csv", "Growth rate by strain/treatment/site, with CIs and p-values", "Response variable (growth)"],
], [3400, 3160, 2800]));
body.push(P([ I("This pairing of drivers and biological response is what elevates the proof-of-concept from a plausibility demo to a genuine validation.") ]));

body.push(H2("4.2 Generalization targets (Neuse–Pamlico)"));
body.push(makeTable([
  ["Source", "Variables", "Access"],
  ["ModMon (Neuse River Estuary, UNC Paerl Lab)", "Temp, salinity, DO, turbidity, chlorophyll (1994–2021)", "SECOORA ERDDAP (erddapy), QARTOD flags"],
  ["USGS Fort Barnwell (02091814)", "River discharge (freshwater forcing)", "USGS NWIS (dataretrieval)"],
  ["NOAA CO-OPS Beaufort (8656483)", "Water temperature (no salinity sensor)", "CO-OPS API (requests)"],
], [3400, 3160, 2800]));
body.push(callout([
  B("Scope note for Dr. Rittschof. "),
  T("We chose “Neuse–Pamlico first,” but the richest "), I("paired"),
  T(" data (environment + biological response) is the oyster-farm sites. The strongest path is to build and "),
  B("validate"), T(" the engine where we have ground-truth biology (oyster sites), then extend the environmental engine to the Neuse–Pamlico. This is a deliberate refinement to confirm."),
]));

// 5. Approach
body.push(H1("5. Approach and methods"));
body.push(H2("5.1 Suitability envelopes and the Habitat Suitability Index"));
body.push(P("Each environmental factor maps to a [0,1] suitability via a transparent trapezoidal curve defined by min / optimum-low / optimum-high / max thresholds. Factors are combined into a single Habitat Suitability Index (HSI) using the geometric mean, so that any one lethal factor (for example, DO → 0) drives the whole HSI to zero. This is what captures a true hypoxia/heat “squeeze”; an arithmetic mean would mask it. A Liebig minimum-factor combiner is also provided and compared. The model is deliberately mechanistic and interpretable — not a machine-learned species-distribution model — because interpretability, not raw fit, is the point. (The envelope set includes pH for the calcifying oyster, but the Program 195 spatial validation in §5.5 uses temperature, salinity, and dissolved oxygen only — pH is not recorded at trawl tows.)"));
body.push(H2("5.2 Degree-days (phenology layer, kept honest)"));
body.push(P("Degree-days predict the timing of development, spawning, and activity for cold-blooded animals and are well supported for pre-maturation growth (Neuheimer & Taggart 2007 found accumulated degree-days explained >92% of length-at-day variance across nine fish species). They are kept strictly separate from the survival envelope, because a plain degree-day sum breaks down near thermal extremes — upper-lethal limits and hypoxia are handled by the envelope, while degree-days only predict when favorable windows open. Base temperatures are species-specific where published (e.g. 20 °C oyster spawning, 10.8 °C blue-crab molt) and explicit placeholders for southern flounder and Atlantic croaker, which have no published developmental base — flagged as such in the repository."));
body.push(H2("5.3 Validation against observed biology (the payoff)"));
body.push(P("For each census interval at a site we accumulate a stress load from the suitability time series and test whether it rank-correlates with observed oyster mortality. As reported in §5.5, this oyster-mortality test came back null — the tolerant oyster stayed within its adequate range at these well-flushed sites — so the load-bearing validation is the Program 195 spatial-occupancy result below, not oyster mortality. The continuous suitability series is also contrasted with documented low-DO periods (§5.6)."));
body.push(H2("5.4 Tooling: Python"));
body.push(P("Recommended: Python. The machine-readable route to the generalization data is SECOORA ERDDAP, and erddapy gives clean, scriptable queries that preserve QC flags; pandas/xarray, dataretrieval (USGS), matplotlib, and scipy cover the rest of the pipeline in one coherent stack that also matches the oyster team's GitHub workflow. R remains fully capable (the team already uses tidyverse/Shiny), and the repository's loaders read their R-exported CSV/XLSX directly."));

body.push(H2("5.5 Results to date — what is already validated (and what is not)"));
body.push(callout([
  B("Headline result — a modest, consistent, literature-calibrated spatial signal. "),
  T("Using each tow's own bottom temperature, salinity, and dissolved oxygen with the "),
  I("literature-calibrated"),
  T(" envelopes (never fit to catch data), the Habitat Suitability Index predicts "),
  B("where"),
  T(" trawl species are caught in the NC Program 195 survey. The honest, year-controlled effect is "),
  B("modest but directionally consistent"),
  T(", and southern flounder is the clean, load-bearing case: within years, flounder ρ (median) = 0.15, positive in 89% of years. Restricting to the 2,692 tows that actually measured all three factors — bottom dissolved oxygen is absent from 39% of tows (every pre-1996 tow), and the geometric-mean combiner averages over whatever factors are present — the per-tow correlations are flounder +0.15, Atlantic croaker +0.07, and blue crab +0.05. Effects are small (a few percent of variance; presence-AUC 0.55–0.59 — weak but consistent discrimination); the very small p-values reflect the large sample (≈2,700–4,300 tows), not a large effect, and tows are spatially clustered — so we report the robustness of the relationship's "),
  B("sign and direction"),
  T(", not its magnitude, and flag a mixed-effects / block-bootstrap treatment of spatial non-independence as planned work."),
]));
body.push(P([
  B("Does the envelope beat a thermometer? Only for flounder — and that is the point. "),
  T("Against a raw bottom-temperature baseline, flounder's signal is genuinely multi-axis: its suitability is salinity-driven (HSI–temperature rank-correlation = −0.29), raw temperature alone is uninformative for flounder (ρ ≈ +0.01), and partialling temperature out leaves the signal intact (partial ρ = +0.16). Croaker's weaker signal is a temperature-shaped preference the trapezoidal envelope captures (partial ρ = +0.08, positive in ~63% of years), and blue crab is essentially flat (partial ρ = +0.05; raw temperature does as well or better). The blue-crab result is "),
  B("expected, not a defect"),
  T(": 97% of tows fall inside the crab's salinity tolerance plateau and 82% inside its oxygen plateau, so those axes are mathematically flat across the well-mixed sound, and adult blue crab is a euryhaline, mobile, sex-segregated generalist that avoids hypoxic bottom water and buries below ~10 °C — its realized location is not set by a static bottom reading. We therefore keep the crab envelope as a labeled physiological-tolerance layer (not an occurrence predictor) and flag a sex-/life-stage-structured model as the correct future path. Flounder, pinned to low-salinity fine sediment, is the case the method is built for; croaker is a consistency check. The relationship's "),
  B("sign is robust to envelope uncertainty"),
  T(": under ±15% perturbation of every threshold (300 Monte-Carlo draws) the pooled correlation stays positive in 100% of draws for all three species."),
]));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
  children: [new ImageRun({
    type: "png", data: fs.readFileSync(FIG),
    transformation: { width: 600, height: 170 },
    altText: { title: "Suitability validation", name: "validation",
      description: "Fraction of Program 195 tows where each species was present, by HSI decile" },
  })],
}));
body.push(P([
  I("Figure 1. Independent validation: fraction of Program 195 tows where each species was caught, by habitat-suitability decile (suitability computed from each tow's own bottom T/S/DO using the literature-calibrated envelopes, never fit to catch). Occurrence rises with modeled suitability for all three species. The ρ and AUC printed in each panel are pooled over all 1987–2021 tows; as the text explains, the honest year-controlled and complete-oxygen correlations are lower for croaker and blue crab, and the signal is genuinely multi-factor only for southern flounder. Data: SEAMAP-SA Pamlico Sound Survey (NC DMF), used under the SEAMAP-SA Intellectual Property Protocol — not for redistribution."),
]));

body.push(H2("5.6 The summer squeeze the survey can't see"));
body.push(P([
  T("The model's central claim — that sub-seasonal, bottom-water stress is large and survey-blind — is borne out directly by depth-resolved ModMon profiles. In the Neuse River estuary, "),
  B("bottom water is hypoxic (DO < 2 mg/L) in 44% of warm-season profiles versus 0.5% at the surface"),
  T("; it peaks in August (54% of bottom profiles; median bottom DO 1.5 mg/L; modeled croaker bottom-habitat suitability → 0) and is worst in July–August. The trawl survey samples predominantly in June and September (3,715 of 4,417 tows in 1987–2021), with only sparse opportunistic July–August coverage (128 tows) — so the hypoxia peak falls in a systematic sampling gap (bottom hypoxia is 51% in July–August versus 37% in June and September). The surface looks pristine while the bottom — where demersal species live — suffocates. This is measured dissolved oxygen, in the survey's own system, with no model assumptions."),
]));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
  children: [new ImageRun({
    type: "png", data: fs.readFileSync(FIG2),
    transformation: { width: 540, height: 284 },
    altText: { title: "Neuse bottom hypoxia", name: "hypoxia",
      description: "Neuse bottom vs surface water hypoxia by month, depth-resolved ModMon" },
  })],
}));
body.push(P([
  I("Figure 2. Neuse bottom- vs surface-water hypoxia by month (depth-resolved ModMon, 1994–2021). Bottom-water hypoxia peaks in July–August — between the June and September survey windows. Data: UNC ModMon via SECOORA ERDDAP."),
]));
body.push(P([
  B("The squeeze is current and intensifying. "),
  T("Extending the same depth-resolved monitoring with the UNC Paerl Lab's post-2021 sonde data (7,681 Neuse bottom casts, 1994–2026) shows the summer squeeze has not eased: recent full summers run 56% (2022), 41% (2023), 46% (2024), and 47% (2025) bottom-hypoxic, around the 43% historical (1994–2021) mean. Bottom-water hypoxia is "),
  B("trending upward at +6.9 percentage points per decade"),
  T(" (1994–2025; p = 0.002, R² = 0.28). This is not a splice artifact: on the homogeneous 1994–2021 ERDDAP record alone the trend is steeper (+9.0%/decade, p = 0.001), and the newer sonde reads lower, not higher — so the long-term signal is, if anything, conservative. The condition the survey under-samples is getting worse — which is exactly why sub-seasonal, depth-resolved monitoring is the right investment now."),
]));
body.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
  children: [new ImageRun({
    type: "png", data: fs.readFileSync(FIG3),
    transformation: { width: 560, height: 205 },
    altText: { title: "Neuse bottom hypoxia trend", name: "trend",
      description: "Neuse summer bottom-water hypoxia by year 1994-2026 with upward trend" },
  })],
}));
body.push(P([
  I("Figure 3. Neuse summer bottom-water hypoxia by year (1994–2026): ERDDAP CTD casts (1994–2021) plus UNC Paerl-Lab sonde (2022–2026), same monitoring program. The fraction of warm-season bottom profiles below 2 mg/L trends upward (+6.9%/decade, p = 0.002, R² = 0.28). Data: UNC ModMon via SECOORA ERDDAP + UNC Paerl Lab."),
]));
body.push(callout([
  B("Honest scope — what the model does NOT do. "),
  T("Two stringent tests returned null, and they sharpen the tool's purpose. (a) Annual abundance is "),
  B("not"),
  T(" predicted by that year's mean habitat suitability (no positive correlation across 28 years) — year-to-year abundance is dominated by recruitment and fishing, not adult habitat. (b) Oyster mortality at the well-flushed CMAST/DUML farm sites is not explained by temperature/oxygen suitability; in fact the more oxygen-stressed site had "),
  I("higher"),
  T(" survival (0.96 vs 0.80), because the tolerant oyster stayed within its adequate range and mortality there is governed by other factors (salinity, disease, handling). The conclusion: this is a "),
  B("spatial and sub-seasonal habitat-stress lens"),
  T(" — validated for where mobile species occur and for resolving the bottom-water squeeze — not a stock-abundance or oyster-mortality predictor. Stating that scope is itself a contribution: it tells managers exactly what the tool is and is not for."),
]));

// 6. Workflow
body.push(H1("6. Research workflow — modeled on The AI Scientist"));
body.push(P([
  T("The project's "), B("process"),
  T(" (not its AI content) is modeled on The AI Scientist (Lu et al., Nature 2026), which runs research as a single automated driver advancing through discrete stages, where each experiment is a journaled “node” that is automatically reviewed before the best one is carried forward. We adopt that scaffold because it gives a small project reproducibility, auditability, and explicit go/no-go gates."),
]));
body.push(makeTable([
  ["The AI Scientist (Lu et al. 2026)", "Trees to Seas implementation"],
  ["Four-stage experiment progress manager", "Stage 1 viability → Stage 2 envelope tuning → Stage 3 execution → Stage 4 ablation"],
  ["Stage transitions on pre-defined criteria", "e.g. Stage 2 advances only if the full HSI beats the temperature-only baseline"],
  ["Each experiment is a journaled, typed node", "Structured journal.jsonl + final_info.json + best_node.json + notes.txt"],
  ["LLM judge selects the best node to seed the next stage", "Driver selects the best node (review score) and carries the best combiner forward"],
  ["Automated Reviewer (LLM ensemble, NeurIPS rubric)", "Deterministic 5-dimension review rubric (upgradeable to an LLM reviewer)"],
  ["Buggy nodes recorded, not fatal", "Every stage is wrapped so failures are journaled, not crashes"],
], [4680, 4680]));
body.push(P([ I("Full mapping and rationale are in docs/methodology.md in the repository.") ]));

// 7. Roadmap
body.push(H1("7. Eight-week roadmap"));
body.push(P("Because the primary data is already in hand, the schedule front-loads validation rather than data hunting."));
body.push(makeTable([
  ["Week", "Goal", "Deliverable"],
  ["1", "Lock scope + corrected framing; initialize repo; request FerryMon/post-2021 ModMon; sync data format with the oyster team", "One-page scope + corrected-facts sheet; reproducible repo (done in v0.1)"],
  ["2", "Reliable ingestion + QC of all oyster sites/years (CSV + XLSX)", "Clean dataset + data-coverage figure"],
  ["3", "Parameterize defensible, cited tolerance envelopes (NC vs. transferred)", "Versioned tolerance table + factor-curve panel"],
  ["4", "Implement + unit-test the HSI engine; calibrate against mortality", "Tested HSI module + per-site HSI time series"],
  ["5", "Add the degree-day phenology layer with honest caveats", "GDD curves + predicted spawning/activity windows"],
  ["6", "Headline figures: when/where suitability-vs-stress; quantify the snapshot gap", "Dynamic suitability maps + “what the snapshots miss” figure"],
  ["7", "Generalize: wire ERDDAP/USGS/NOAA; reproducibility hardening", "One-command-reproducible repo; optional Neuse demo"],
  ["8", "Write proposal narrative around figures; advisor review packet", "Final proposal + roadmap + repo v0.2 + advisor question list"],
], [700, 4660, 4000]));

// 8. Deliverables
body.push(H1("8. Deliverables"));
[
  "This proposal + modeling roadmap document.",
  "A reproducible Python repository (treestoseas v0.1): ingestion → QC → HSI → degree-days → validation → figures, journaled per run.",
  "A cited species tolerance/parameter table with NC-specific vs. transferred values flagged.",
  "A tested HSI module (geometric-mean envelopes) and a separate degree-day module.",
  "The headline figure set: the spatial suitability-vs-catch validation, the depth-resolved when/where squeeze maps, and the 1994–2026 bottom-hypoxia trend.",
  "A corrected-facts crib sheet (Appendix A).",
  "An advisor packet: open questions and a data-coordination note for the oyster team; a generalization/validation plan for the Neuse–Pamlico.",
].forEach(d => body.push(bullet(d)));

// 9. Risks
body.push(H1("9. Risks and mitigations"));
body.push(makeTable([
  ["Risk", "Mitigation"],
  ["Pitch resting on the false “no covariates” premise", "Already corrected: lead with temporal-resolution + under-use; cite SEAMAP-SA (Appendix A)"],
  ["Tolerance thresholds transferred from other systems → false precision", "Tag every value NC-specific vs. transferred; run a sensitivity pass; present HSI as a relative index"],
  ["FerryMon access is email-only and routes have been down since 2019", "Make the oyster sites + ModMon-via-ERDDAP primary; FerryMon a stretch goal"],
  ["Degree-days over-promise near thermal extremes", "Keep degree-days as a timing layer only; the envelope handles upper-lethal limits and hypoxia"],
  ["Sensor gaps / cadence mismatch across sources", "Resample to common daily/weekly cadence, carry QC flags, show coverage plots, never silently interpolate"],
  ["Landings declines mistaken for abundance declines", "State the distinction explicitly; use croaker suitability-vs-landings as a feature, not a hidden assumption"],
  ["Scope creep into a validated SDM or multi-region build", "Hard-commit to oyster sites, the focal species, a mechanistic model, and sufficiency-style validation"],
], [3400, 5960]));

// 10. Open questions
body.push(H1("10. Open questions"));
body.push(H2("For Dr. Rittschof"));
[
  "Is the reframed critique (sub-seasonal resolution + covariate under-use, not “no covariates”) strong enough to anchor the proposal?",
  "Confirm the scope refinement: validate on the oyster sites first, then generalize the engine to the Neuse–Pamlico?",
  "Is the focal species set right (eastern oyster anchor; blue crab, southern flounder, Atlantic croaker)? Add river herring?",
  "Is the geometric-mean HSI (any lethal factor zeros suitability) the right combiner, or do you prefer a Liebig minimum-factor approach?",
  "What validation bar do you expect — is the sufficiency demo enough, or do you want a quantitative comparison against Program 195 catch indices?",
  "Should the land-use “trees to seas” driver narrative be carried explicitly, or kept to the significance section?",
].forEach(q => body.push(bullet(q)));
body.push(H2("For the oyster team (Ty / Juliet / Mihir)"));
[
  "What are the units, sensor models, and known QC issues for the CMAST/DUML/Stump Sound/Ward Creek sensors?",
  "What do the oyster strains (BS, CN, CS, SJ) and treatments (50/100 starting density) denote, and which are most comparable?",
  "Is salinity in the 2024–25 data conductivity-derived, and what conversion was used?",
  "Can we get post-2024 cleaned files and a stable data-format contract so the pipeline ingests new seasons automatically?",
].forEach(q => body.push(bullet(q)));

// Appendix A
body.push(new Paragraph({ children: [new PageBreak()] }));
body.push(H1("Appendix A — Corrected-facts crib sheet"));
body.push(P("The original brainstorming notes contained several factual errors, fact-checked against NOAA, USGS, NC DMF, UNC/Duke, and APNEP sources. Several are load-bearing."));
body.push(makeTable([
  ["Claim in the notes", "Corrected"],
  ["Menhaden killed in Chicago, 1964", "Alewife (Alosa pseudoharengus) die-off, Lake Michigan / Chicago shoreline, 1967. Menhaden are absent from the Great Lakes."],
  ["~20 species extinct in the Great Lakes", "26 fish extirpated from ≥1 lake, 4 globally extinct (DFO checklist). “~20” only as a loose figure."],
  ["Sturgeon collapsed in the 1960s–70s", "Lake sturgeon collapsed ~1880s–1920s; ~1% of historic abundance today. The 1960s–70s is when blue pike went extinct."],
  ["Cisco/whitefish lost mainly to logging siltation", "Primary drivers: overfishing + invasives; siltation contributing, not the lead cause, and not attributed to logging."],
  ["2nd-largest estuary in the world", "“2nd-largest estuarine complex in the lower 48” (APNEP). Pamlico Sound is the largest embayed estuary in the world — keep distinct."],
  ["Program 195 ignores salinity/rainfall/turbidity/temperature", "FALSE. Program 195 is stratified-random and records temp, salinity, DO, secchi (turbidity), precipitation at every grid. Real critique: warm-season effort concentrated in June and September (only ~128 of 4,417 tows fall in July–August, the hypoxia peak) + covariate under-use — not non-measurement."],
  ["NC #2 in hog production", "#3 in total hog inventory (Iowa, Minnesota ahead); ~#2 in the breeding herd. State metric + year."],
  ["Hogs = #1 nutrient-pollution source in NC", "Poultry has overtaken swine (~3× the N, ~6× the P; NC DEQ 2017)."],
  ["Croaker/spot “crashed ~97%”", "That is a landings decline, not abundance — NC surveys show croaker/spot remain among the most abundant estuarine fish."],
  ["Drought pushes crabs into freshwater and they die", "Backwards: drought raises salinity; higher salinity correlates with lower crab abundance and faster Hematodinium spread."],
  ["FerryMon = clean continuous 20-yr record", "FerryMon (not “Fairymon”) is NOT continuous: funding gap after ~2016; routes down since 2019/2021. Treat as a stretch goal."],
  ["Cape Hatteras NERR (Beaufort)", "No Cape Hatteras NERR. NC NERR: Currituck Banks, Rachel Carson (Beaufort), Masonboro Island, Zeke's Island."],
], [3400, 5960]));

// References
body.push(H1("References"));
[
  "Lu, C., Lu, C., Lange, R. T., Yamada, Y., Hu, S., Foerster, J., Ha, D., & Clune, J. (2026). Towards end-to-end automation of AI research. Nature, 651, 914–919. https://doi.org/10.1038/s41586-026-10265-5",
  "Neuheimer, A. B., & Taggart, C. T. (2007). The growing degree-day and fish size-at-age: the overlooked metric. Canadian Journal of Fisheries and Aquatic Sciences, 64(2), 375–385.",
  "Albemarle-Pamlico National Estuary Partnership (APNEP). Comprehensive Conservation and Management Plan (1994; rev. 2012, 2025). https://apnep.nc.gov/resources/publications-and-reports/comprehensive-conservation-and-management-plan",
  "SEAMAP-South Atlantic / NC Division of Marine Fisheries. Pamlico Sound Survey (Program 195), Abundance & Biomass extract, 1987–2021, obtained via the SEAMAP-SA Data Portal (seamap.org/data-portal) under the SEAMAP-SA Intellectual Property Protocol. Used for the Figure 1 validation; not redistributed.",
  "NC Department of Environmental Quality (2017). Basinwide Manure Production Report.",
].forEach(r => body.push(P(r)));

// ---------- document ----------
const doc = new Document({
  creator: "Trees to Seas",
  title: "Trees to Seas — Proposal and Modeling Roadmap",
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Arial", color: "2E5E8C" },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "3A6EA5" },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 600, hanging: 300 } } } }] },
      { reference: "nums", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 600, hanging: 300 } } } }] },
    ],
  },
  sections: [{
    properties: { page: {
      size: { width: 12240, height: 15840 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
    } },
    headers: { default: new Header({ children: [ new Paragraph({
      alignment: AlignmentType.RIGHT,
      children: [ new TextRun({ text: "Trees to Seas — Proposal & Modeling Roadmap", size: 16, color: "888888" }) ] }) ] }) },
    footers: { default: new Footer({ children: [ new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [ new TextRun({ text: "Page ", size: 18 }), new TextRun({ children: [PageNumber.CURRENT], size: 18 }),
                  new TextRun({ text: " of ", size: 18 }), new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18 }) ] }) ] }) },
    children: body,
  }],
});

Packer.toBuffer(doc).then(buf => { fs.writeFileSync(OUT, buf); console.log("WROTE", OUT, buf.length, "bytes"); });
