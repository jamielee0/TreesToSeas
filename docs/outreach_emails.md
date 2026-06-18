# Outreach email drafts (refreshed)

Three drafts, updated to reflect the validated proof-of-concept. Replace everything in
[brackets]. Verify current contact addresses before sending (people move labs).

---

## 1 — To Dr. Rittschof (intro + proposal review)

**To:** [Dr. Rittschof's email]
**Subject:** Trees to Seas — validated proof-of-concept, and a quick intro to the Paerl Lab?

Hi Dr. Rittschof,

The Trees to Seas proof-of-concept is now built *and* validated, and the proposal +
figures are ready for your review. Three results stand out:

- Using each Program 195 tow's own bottom temperature, salinity, and dissolved oxygen
  with literature-calibrated tolerance envelopes (never fit to catch data), the habitat
  suitability index **predicts where blue crab, southern flounder, and Atlantic croaker
  are caught** across 4,312 tows (1987–2021), and the signal is robust to ±15% changes
  in every threshold.
- Depth-resolved ModMon shows the **Neuse bottom water is hypoxic in 44% of warm-season
  profiles (vs 0.5% at the surface), peaking in July–August — between the survey's June
  and September visits.** The squeeze is real and survey-blind.
- Two honest nulls define the scope: the model does **not** predict annual abundance or
  oyster mortality, so it's a spatial/sub-seasonal habitat lens, not a stock model.

Two asks:

1. **An intro to the UNC Paerl Lab.** The public ERDDAP ModMon record (which the whole
   analysis leans on) ends in Dec 2021, and the FerryMon ferry-track data isn't posted
   publicly. Would you introduce me to their data manager (or let me say you suggested I
   reach out)? I've drafted the request and can send it the moment you point me at them.
2. **Sign-off on a few design choices** before I lock the methods (proposal §10): validate
   on the oyster sites/Program 195 first vs. broaden; the focal-species list; geometric-mean
   vs. Liebig-minimum HSI; and the validation bar (the sufficiency demo I have, vs. a
   quantitative comparison against the Program 195 abundance index).

Happy to walk through the figures whenever suits you. Thanks!
[Your Name]

---

## 2 — To the UNC Paerl Lab (data request)

**To:** [Paerl Lab data manager — e.g. Jack Cheshire, jcheshi@ad.unc.edu; confirm current contact]
**Cc:** [Dr. Rittschof, if he's making the intro]
**Subject:** Data request: post-2021 ModMon + FerryMon (Neuse–Pamlico habitat modeling)

Dear [Name],

I'm [Your Name], a [student/researcher] at [Duke University Marine Laboratory] working with
Dr. Dan Rittschof. We're building a physiological habitat-suitability model for NC estuarine
species, and the **ModMon record (via SECOORA ERDDAP) has been central** to it — we've used
the depth-resolved Neuse mid-river stations and the Pamlico Sound PS1–9 stations (1994–2021)
to show, for example, that Neuse bottom water is hypoxic in ~44% of warm-season profiles and
that habitat suitability tracks Program 195 catch. We're grateful the data is available, and
we want to acknowledge it correctly.

Two things that don't appear to be publicly posted:

1. **ModMon after December 2021** — the SECOORA ERDDAP holdings for the Neuse stations
   (e.g., Marker 9 / ModMon 120, Marker 52-A / ModMon 20) end ~2021-12-06. Is a more recent
   extract available, ideally with the depth (z) profiles and the QARTOD flags?
2. **FerryMon continuous (flow-through) data** — the GPS-tagged temperature, salinity, DO,
   turbidity, and chlorophyll along the Pamlico Sound and Neuse ferry transects, for whatever
   period is available.

Anything you can share (CSV or a repository pointer) would help a lot, and I'll follow any
data-use terms. Could you also confirm the citation/acknowledgment language you'd like for
ModMon and FerryMon?

Thank you very much for your time.

Best regards,
[Your Name] — [affiliation / email / phone]

---

## 3 — To the Bass Connections oyster team (metadata + a specific finding)

**To:** [Ty], [Juliet], [Mihir]
**Cc:** [Henry Sun; Dr. Rittschof as appropriate]
**Subject:** Oyster data — quick questions (and a result that needs your context)

Hi all,

Thanks again for the GitHub data (the oystersdukebc repos) — the pipeline now reads the
2024–25 environmental and mortality files and the 2025–26 sensor sheets. One result makes
your context especially important:

**Temperature and dissolved oxygen did *not* explain the oyster mortality.** In fact the more
oxygen-stressed site (DUML: 21% of the season below 4 mg/L) had *higher* survival than CMAST
(median 0.96 vs 0.80). So the mortality is being driven by something other than the
temperature/oxygen suitability we model — and I'd like your help interpreting it:

1. **Disease** — was Dermo/*Perkinsus* (or *Haplosporidium*) monitored at either site? That's a
   leading candidate for the CMAST mortality.
2. **Strains & treatments** — what do BS, CN, CS, SJ denote, and the 50 / 100 levels (starting
   density?)? Which are most comparable, and were any strains hit harder?
3. **Handling** — flip/maintenance schedule (the `FlipFreq` column) and any transplant/handling
   events that could spike mortality.
4. **Salinity** — is the 2024–25 salinity conductivity-derived (what conversion / reference
   temperature)? Same method as the 2025–26 `Sal_ppt`?
5. **Sites** — approximate lat/long and sensor depth for CMAST, DUML, Stump Sound, Ward Creek.
6. **Going forward** — could you keep exporting the cleaned files with the same column names
   each season, so the model ingests new years automatically?

Even partial answers help, and I'm glad to share what the model is doing in return.

Thanks!
[Your Name]
