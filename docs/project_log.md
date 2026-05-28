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

## Day 4 — Import Data Validation & Trend Analysis

**Goal:** Validate the raw import dataset and produce the analysis behind report Section 2.

**Completed (part 1 — import analysis):**
- Installed matplotlib + ipykernel (notebook tooling).
- Validation passed: 1,082 rows / 28 months, **0 duplicates, 0 negatives, 0 missing**, 33–47 countries/month.
- Cross-check vs API 합계 row: 2024-01 country-sum 16,411,523 kg ≈ API total 16,411,521 kg (diff 2 kg) → consistent.
- Created notebook `notebooks/01_import_validation_and_trend.ipynb` (validation + trend + origin charts).
  - Written valid but **unexecuted** — run "Run All" in VSCode to render charts (nbclient kernel launch fails on this Windows setup).
- Created processed datasets:
  - `data/processed/monthly_import_summary.csv` (28 months: volume, value, unit price, #countries)
  - `data/processed/origin_summary.csv` (85 origin rows with share %)

**Key insight (feeds Section 2 & 3):**
- Import **volume** is roughly flat (~12–16k tons/month), but **avg unit price ~ $3.9/kg (2024-01) → ~$7/kg (2026 Q1)**.
- → Rising import *value* is **price-driven, not volume-driven**. Directly ties to international price trend (Section 3).
- Origin concentration: top 4 (Brazil 33.9%, Vietnam 16.7%, Colombia 16.5%, Ethiopia 12.2%) ≈ **79%** of volume → supply-risk focus (Section 5).

**Completed (part 2 — international price + cross-check):**
- Source decision: **FRED first** (free, no key, monthly, automatable), ICO kept as later authoritative cross-reference.
- Created `scripts/fetch_prices.py` — pulls FRED `PCOFFOTMUSDM` (Arabica Other Milds) + `PCOFFROBUSDM` (Robusta),
  converts US cents/lb → USD/kg (×0.0220462) for direct comparison with import unit price.
- Created `data/raw/coffee_prices_fred_2024_2026.csv` (27 months, 2024-01 → 2026-03).
- Created `data/processed/price_vs_import_unitprice.csv` (import unit price merged with world prices).
- Created notebook `notebooks/02_price_trend_and_crosscheck.ipynb` (unexecuted; Run All in VSCode).

**Key insight (Section 3):**
- Korea import unit price correlation: **Arabica 0.87**, Robusta 0.26 → import cost is **arabica-driven**.
- Import price sits ~$0.93/kg below Arabica (cheaper Robusta/Brazilian-naturals blend); converges to Arabica by 2026-03 ($7.40 vs $7.37/kg).
- → The ~2x rise in import unit price is **explained by the world arabica price surge (exogenous cost shock)**, not a domestic sourcing change → feeds F&B cost pressure (Section 6).

**Next action:** Draft report Section 2 + 3 prose from these processed datasets; later add ICO I-CIP as authoritative cross-check; then FX (Section 4).

---
