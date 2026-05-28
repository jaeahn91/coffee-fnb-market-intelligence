# Project Log

---

## Day 1 — Project Setup

**Goal:** Create the project directory structure and initial files.

**Completed:**
- Created folder structure: `data/raw/`, `data/processed/`, `data/reference/`, `notebooks/`, `reports/`, `prompts/`, `docs/`
- Created `README.md` (initial)
- Created `docs/data_sources.md`
- Created `data/reference/source_tracker.csv`
- Created `reports/monthly_coffee_market_brief_2026_05.md` (empty template)
- Created `prompts/report_generation_prompt_v0.md`

**Key decision:** Start with structured workspace before any analysis.

---

## Day 2 — Data Source Planning

**Goal:** Identify and document the main data sources for the first monthly report.

**Completed:**
- Confirmed 5 main data categories: import, price, FX, origin risk, domestic F&B
- Documented sources in `docs/data_sources.md`
- Populated `data/reference/source_tracker.csv` with initial source entries
- Confirmed first data target: HS 090111 (Coffee, not roasted, not decaffeinated)

**Key decision:** Manual data collection (CSV download, copy-paste) is acceptable for v0. No automation required yet.

---

## Day 3 — First Raw Data Collection (HS 090111)

**Goal:** Create the first raw dataset file and document the data collection process.

**Completed:**
- Created `data/raw/korea_green_bean_imports_hs090111_2024_2026.csv` (header only, ready for data entry)
- Created `docs/data_collection_guide_hs090111.md` with step-by-step collection instructions
- Updated `data/reference/source_tracker.csv` (import source → in_progress)

**Revised:** Using Korea Customs Service OpenAPI (data.go.kr) instead of manual KITA download.
- Created `scripts/fetch_imports.py` — automated XML fetch, one call per month, all countries.
- Created `requirements.txt` (requests, pandas, python-dotenv)
- API key stored in `.env` as `CUSTOMS_API_KEY` (gitignored)
- Installed Python 3.12 (winget) + dependencies on this machine.

**API spec corrections (after `--debug` probing):**
- Params: `strtYymm` / `endYymm` (YYYYMM), `hsSgn`; `cntyCd` optional → omit to get all countries.
- Response is **XML**, not JSON. Parsed with `xml.etree.ElementTree`.
- Fields: `year` (2024.01), `statCd` (code), `statCdCntnKor1` (country, KOR), `statKor` (item), `impWgt`, `impDlr`.
- **Units correction:** `impWgt` is already **kg** and `impDlr` already **USD** — earlier tons/thousand-USD assumption was wrong; no ×1000 conversion.
- First item per response is a **합계 (total) row** (statCd="-") → skipped. Rows with zero imports also skipped.

**Result:** Fetched **1,082 rows** across 28 months (2024-01 → 2026-04) into
`data/raw/korea_green_bean_imports_hs090111_2024_2026.csv`. Top origins: Brazil, Colombia, Ethiopia, Guatemala.

**Next action (Day 4):** Clean/validate the raw data in a notebook (dedupe, sanity-check totals vs 합계 row) and start the price (ICO) source.

---
