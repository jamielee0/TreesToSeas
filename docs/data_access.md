# Data access & automation — what's automated vs. what's on you

Goal: automate everything that can be automated. The good news — **none of the
programmatic sources need an API key or login.** The only manual steps are a couple
of email requests for data that isn't posted publicly.

## TL;DR

| Source | Login / key? | Automatable now? | How |
|---|---|---|---|
| Ty's oyster data (GitHub `oystersdukebc`) | No (public) | ✅ Fully | `python scripts/fetch_data.py` |
| SECOORA ERDDAP — ModMon (Neuse–Pamlico) | No (public) | ✅ Fully | `treestoseas.io.erddap` (verified live) |
| USGS NWIS — discharge (Fort Barnwell) | No (public) | ✅ Fully | `treestoseas.io.usgs` (`pip install dataretrieval`) |
| NOAA CO-OPS — water temp (Beaufort) | No (public) | ✅ Fully | `treestoseas.io.noaa_coops` (plain `requests`) |
| FerryMon continuous ferry-track data | n/a | ❌ Manual | **Email UNC Paerl Lab** (see below) |
| ModMon data **after Dec 2021** | n/a | ❌ Manual | **Email UNC Paerl Lab** |
| NC Program 195 catch/abundance (Pamlico Sound Survey) | Free account | ⚠️ Self-service | **SEAMAP-SA Data Portal** (register + agree to citation protocol → online query). *Only needed for the optional catch-vs-suitability comparison.* |
| Tolerance-parameter papers (full text) | Mostly free | ✅ Mostly | Values + citations already captured in `species.yaml`. Key sources are open (NOAA memos, NC CHPP, PLOS ONE, SEDAR); a few paywalled → Duke library/VPN |

## Fully automated (no action from you)

1. **Oyster data (primary).** `python scripts/fetch_data.py` downloads the 2024–25 CSVs;
   `--year both` adds the 2025–26 XLSX (4 sites). Public GitHub, no login.
2. **ModMon / Neuse–Pamlico (SECOORA ERDDAP).** Verified live: 24 stations, QARTOD-flagged,
   coverage **1994-01-24 → 2021-12-06** (Neuse) and ~2000–2021 (Pamlico). Zero dependencies
   beyond `requests`:
   ```python
   from treestoseas.io import erddap
   erddap.list_modmon_datasets()                       # auto-discovers all station IDs
   erddap.load_modmon_station("neuse-river-at-marker-9-modmo",
                              start="2010-06-01", end="2010-09-30")
   ```
3. **USGS discharge.** `pip install dataretrieval`, then `treestoseas.io.usgs.load_discharge()`
   for Fort Barnwell (02091814). Public.
4. **NOAA CO-OPS water temperature.** `treestoseas.io.noaa_coops.load_water_temperature()`
   for Beaufort (8656483). Public API; it caps the date-range length, so call it per
   year and concatenate (the function is written for that).

## Needs a human (once)

These are the only true blockers — all are because the data isn't posted publicly,
**not** because of credentials:

1. **FerryMon continuous data** — email the **UNC Institute of Marine Sciences / Paerl
   Lab** (data manager **Jack Cheshire, jcheshi@ad.unc.edu**). It's fulfilled by email,
   and the Pamlico/Neuse ferry routes have been down since 2019/2021, so treat it as a
   *stretch goal*, not a dependency. **Ask Ty/Dr. Rittschof to make the intro.**
2. **ModMon after Dec 2021** — same lab; the public ERDDAP holdings end ~2021.
3. **NC Program 195 catch/abundance** — NOT a formal email request. The Pamlico Sound
   Survey lives on the **SEAMAP-SA Data Portal** (https://seamap.org/data-portal/ ->
   https://www2.dnr.sc.gov/seamap/): make a free account, agree to the Intellectual
   Property / citation protocol, then use the online query tool. The survey *design* and
   the June/September window dates are public with no account. You only need the catch
   data for the OPTIONAL quantitative catch-vs-suitability comparison; the POC's
   validation runs on oyster biology, not Program 195 catch. (If you just need numbers to
   cite, SEDAR/ASMFC stock-assessment reports already publish derived indices for free.)
4. **Confirm metadata with the oyster team (Ty / Juliet / Mihir)** — units and sensor
   models for the 2024–25 files, what the strains (BS/CN/CS/SJ) and treatments (50/100)
   mean, and whether 2024–25 salinity is conductivity-derived. (Questions are listed in
   the proposal, §10.)
5. **Decide a stable data-format contract** with the oyster team so each new season
   auto-ingests (e.g., they always export the cleaned files with the same column names).

## What you personally still decide (not data, judgment)

- Sign off on the tolerance-envelope values once compiled (NC-specific vs. transferred).
- Confirm the scope refinement (validate on oyster sites first → generalize to Neuse–Pamlico).
- Pick the HSI combiner (geometric-mean vs. Liebig minimum) — see proposal §10.

## Once the manual intros are made, the whole thing is hands-off

After the FerryMon/ModMon email relationship exists and the oyster team fixes a file
format, a single scheduled job can: pull GitHub + ERDDAP + USGS + NOAA, run
`scripts/run_pipeline.py`, and regenerate figures — no logins, no manual downloads.
