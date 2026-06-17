# Outreach email drafts

Three drafts. Replace everything in [brackets]. Verify current contact addresses
before sending (people move labs).

---

## 1 — To Dr. Rittschof (ask for the intro + proposal review)

**To:** [Dr. Rittschof's email]
**Subject:** Trees to Seas — proposal ready, and a quick intro to the Paerl Lab?

Hi Dr. Rittschof,

The Trees to Seas proof-of-concept is in good shape: I've built the modeling
pipeline, calibrated the oyster tolerance envelopes from the literature, and it
already runs end-to-end on the Bass Connections oyster data (CMAST/DUML) and against
the live ModMon record on SECOORA ERDDAP. The proposal + roadmap is ready for your
review whenever you have a moment.

Two things I could use your help with:

1. **An intro to the UNC Paerl Lab.** The public ERDDAP ModMon record ends in Dec
   2021, and the FerryMon ferry-track data isn't posted publicly — both come by
   request from the lab. Would you be willing to introduce me (or let me say you
   suggested I reach out) to their data manager? I've drafted the request and can
   send it the moment you point me at the right person.

2. **A few design decisions** I'd like your read on before I lock the methods: whether
   to validate on the oyster sites first and then generalize to the Neuse–Pamlico;
   the focal species list; and whether the habitat index should zero out on any single
   lethal factor (geometric mean) or track the single most-limiting factor. These are
   in §10 of the proposal.

Thanks!
[Your Name]

---

## 2 — To the UNC Paerl Lab (the data request)

**To:** [Paerl Lab data manager — e.g. Jack Cheshire, jcheshi@ad.unc.edu; confirm current contact]
**Cc:** [Dr. Rittschof, if he's making the intro]
**Subject:** Data request: FerryMon + post-2021 ModMon (Neuse–Pamlico)

Dear [Name],

I'm [Your Name], a [student/researcher] at [Duke University Marine Laboratory] working
with Dr. Dan Rittschof. We're building a physiological habitat-suitability model for
North Carolina estuarine species, using high-frequency water-quality time series to map
when and where conditions leave each species' survivable range (temperature × salinity
× dissolved oxygen). The ModMon record on SECOORA ERDDAP has been invaluable.

I'm writing to ask about two datasets that don't appear to be publicly posted:

1. **ModMon after December 2021.** The SECOORA ERDDAP holdings for the Neuse River
   Estuary stations end ~2021-12-06. Is there a more recent extract we could obtain for
   the mid-river stations (e.g., Marker 9 / ModMon 120 and Marker 52-A / ModMon 20)?

2. **FerryMon continuous (flow-through) data** — the GPS-tagged temperature, salinity,
   dissolved oxygen, turbidity, and chlorophyll along the Pamlico Sound and Neuse River
   ferry transects, for whatever period is available.

Anything you can share (CSV, or a pointer to a repository) would be a big help. I'm
happy to follow any data-use and citation terms you specify and to acknowledge the lab
in any outputs. Could you also let me know the appropriate citation/acknowledgment
language for ModMon and FerryMon?

Thank you very much for your time.

Best regards,
[Your Name]
[affiliation / email / phone]

---

## 3 — To the Bass Connections oyster team (metadata questions)

**To:** [Ty], [Juliet], [Mihir]
**Cc:** [Henry Sun, Dr. Rittschof as appropriate]
**Subject:** Quick questions on the oyster sensor + mortality data

Hi all,

Thanks for putting the oyster data on GitHub (the oystersdukebc repos) — I've got the
pipeline reading the 2024–25 environmental and mortality files and the 2025–26 sensor
sheets. A few questions so I represent the data correctly:

1. **Sensor units & models.** For `AverageCMASTtemp.csv` / `AverageDUMLtemp.csv` and the
   `environmental_data_*` files — are temperature in °C and DO in mg/L throughout, and
   which sensors (e.g., YSI/HOBO model) were deployed at each site?
2. **Salinity.** Is the 2024–25 salinity conductivity-derived, and if so what conversion
   (and reference temperature) was used? In the 2025–26 sheets it's `Sal_ppt` — same method?
3. **Strains & treatments.** What do the strain codes (BS, CN, CS, SJ) and the treatment
   levels (50 / 100 — starting density?) denote, and which are most directly comparable?
4. **Site coordinates & depth.** Approximate lat/long and sensor depth for CMAST, DUML,
   Stump Sound, and Ward Creek?
5. **Going forward.** Would it be possible to keep exporting the cleaned files with the
   same column names each season? That lets the model ingest new years automatically.

No rush — even partial answers help. Happy to share what the model is doing in return.

Thanks!
[Your Name]
