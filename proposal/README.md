# Building the proposal (`Trees_to_Seas_Proposal.docx` / `.pdf`)

The proposal is generated programmatically from **`gen.js`** (docx-js / Node), not hand-edited.
Edit `gen.js`, regenerate, validate, then export the PDF.

## Dependencies
- **Node** + the `docx` package (`npm install docx`)
- **Python** with `docx`-skill validators (`pip install defusedxml lxml`) — optional but recommended
- **Microsoft Word** (used here for docx→PDF and to populate the table of contents). LibreOffice
  `soffice --convert-to pdf` also works if Word isn't available.

## Figures
`gen.js` embeds PNGs from `../data/processed/` (absolute paths near the top of the file:
`FIG`, `FIG2`). **Run the analysis scripts first** so those figures exist:
- `suitability_validation.png` ← `scripts/program195_analysis.py`
- `neuse_bottom_hypoxia.png` ← `scripts/neuse_bottom_hypoxia.py`

## Steps
```bash
# 1. generate the docx
node gen.js                      # writes ../Trees_to_Seas_Proposal.docx

# 2. (optional) validate
python <docx-skill>/scripts/office/validate.py ../Trees_to_Seas_Proposal.docx

# 3. docx -> PDF (PowerShell, via Word; updates the TOC)
#   $w = New-Object -ComObject Word.Application; $w.Visible=$false
#   $d = $w.Documents.Open("<abs path>.docx")
#   $d.TablesOfContents | %{ $_.Update() }; $d.Fields.Update()
#   $d.ExportAsFixedFormat("<abs path>.pdf", 17); $d.Close($false); $w.Quit()
```

## Notes
- Use `PYTHONUTF8=1` for the validator (the doc contains °C, ρ, ×, em-dashes).
- docx-js hashes media filenames (`word/media/<hash>.png`) — that's normal.
- The original build ran in a temp dir; **this `gen.js` is the canonical preserved copy** —
  if you regenerate from elsewhere, copy the updated `gen.js` back here so it stays in the repo.
- Content structure: §1 summary, §2 background (with corrected facts), §3 objectives,
  §4 data, §5 methods + **§5.5 results / §5.6 the squeeze** (the validated findings + figures
  + honest-scope nulls), §6 AI-Scientist workflow, §7 roadmap, §8 deliverables, §9 risks,
  §10 open questions, Appendix A corrected-facts, References.
