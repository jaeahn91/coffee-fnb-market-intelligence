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

## Day 5 — Report Drafting (Sec 2·3·5), Critical Review & Origin Deep-dive

**Goal:** Turn the processed datasets into report prose, with a critical pass to avoid overstated interpretation.

**Completed (part 1 — draft + editorial review):**
- Set up local `.venv` + Jupyter/nbconvert; executed both notebooks (charts now embedded).
- Exported charts to PNG and placed copies in `reports/figures/` (relative path renders in VSCode preview & GitHub).
- Drafted report **Section 2 (Import Trend)** and **Section 3 (Price / Cross-check)** prose.
- **Critical review (editor role)** — stress-tested claims against data and corrected three overstatements:
  - **Correlation:** level corr 0.87 vs **differenced corr 0.08** → reframed as *co-trend, not short-term causation* (spurious-correlation caveat added).
  - **Value growth:** single-month endpoint +47% is fragile → shown as range **+47~65%** (3-month-avg basis).
  - **Blended unit price** conflates price with origin mix (Brazil share 40%→30%) → noted as confounder; "주로 가격, 일부 구성 변화".

**Completed (part 2 — origin deep-dive → Section 5):**
- Investigated a field rumor ("Ethiopia new crop not arriving in 2026 Q1; pre-contracted stock held").
- **Data check:** ET volume never zero; 2026 Jan–Apr total **+13% YoY**; monthly YoY noisy (Feb −25%, Mar +131%) → no trend decline. ET **price premium vs basket** compressed 2024→25, then **rebounded +$1.07 in 2026-04** (watch-item).
- **Conclusion:** rumor not visible at HS090111 granularity (stock vs flow; no harvest-year field) — data and rumor both can be true.
- **News cross-check** (algrano, Crop to Cup): washed-coffee shortage (40-45%→~20%), first container arrived **Mar 2026** (shifted from Jan), cherry price **$0.45→$1.51/kg (3x)**, pre-contracting & sold-out early containers, East-Africa shipping disruption → rumor explained.
- Wrote **Section 5 (Origin & Supply Risk)** + supporting note `docs/origin_notes_ethiopia_2026q1.md`.

**Key insight:** Aggregate import volume being flat does **not** mean supply is safe — quality/season-level disruptions (washed new crop) surface late and weakly in totals. Triangulation **data + news** is what turns a number into intelligence.

**Housekeeping:** `.gitignore` += `outputs/` (regenerable). `.venv`/`.env` confirmed ignored.

**Next action:** Section 7 Watchpoint — track whether ET premium persists in May data. Then FX (Section 4: USD/KRW → 원화 원가, "이중 비용 압박"). ICO I-CIP as authoritative price cross-check later.

---

## Day 6 — FX Impact (Section 4) + Cost Decomposition

**Goal:** Collect USD/KRW, quantify the "이중 비용 압박", and draft report Section 4.

**Completed (data collection):**
- Created `scripts/fetch_fx.py` for USD/KRW monthly series.
- **Source pivot:** FRED `DEXKOUS` was unreachable from this machine today (TLS handshake OK but read times out / HTTP-2 stream error; generic internet fine → FRED-specific egress block). Stooq returned a JS anti-bot challenge.
  - Switched to **ECB reference rate via Frankfurter API** (`api.frankfurter.dev`, key-free, equally authoritative). Daily → monthly avg.
  - Also fixed a macOS python.org SSL cert-verify failure by fetching through `requests` (bundles certifi) instead of `pd.read_csv(url)`'s urllib path.
- Created `data/raw/fx_usdkrw_ecb_2024_2026.csv` (USD/KRW monthly avg, 2024-01 → 2026-06; 2026-06 partial).

**Completed (analysis → Section 4):**
- Created `notebooks/03_fx_and_cost_decomposition.ipynb` (executed via nbconvert; charts embedded).
- Log decomposition `cost_KRW = price_USD × FX` (exactly additive in logs).
- Created `data/processed/fx_and_cost_decomposition.csv` + figures `05_fx_usdkrw_trend.png`, `06_krw_cost_decomposition.png`.
- Drafted **Section 4 (FX Impact)** with the same critical/non-overstated calibration.

**Key insight:**
- Won import cost ~**doubled** (5,150 → 11,030 KRW/kg, +114%); contribution **price ~85% / FX ~15%** — "이중 압박" is real but **asymmetric** (FX is a secondary amplifier, not co-equal).
- **Sharpest finding:** from the 2025-05 USD-price peak, world price eased −7.2% but the won weakened +7.4%, so won cost was **−0.4% (flat)** — FX *offset the price relief*; importers felt none of the global easing. Explains why domestic F&B cost stays elevated (→ Section 6).

**Housekeeping:** `.gitignore` += bkit plugin scratch files (`docs/.bkit-memory.json`, `docs/.pdca-status.json`).

**Completed (part 3 — Section 6, same session):**
- Drafted **Section 6 (Korean F&B Implications)** — synthesis section, no domestic 1차 data yet, so framed as cost-structure *mechanisms + hypotheses*, not confirmed outcomes.
- **Core move:** translated wholesale shock to **per-cup** terms — green bean ~+100 KRW/cup (16-20g band) ≈ **~7% of a 1,500원 저가 아메리카노 but ~2% of a premium cup**. "생두값 2배 ≠ 판매가 2배."
- Segmented exposure (저가 / 중가 / 프리미엄 / 스페셜티-로스터; specialty hit on BOTH price AND §5 supply), 4 pass-through levers, and an explicit **data-to-collect list** feeding §7.
- Strong caveat block: per-cup math is order-of-magnitude (stated assumptions); price tiers illustrative, no brand-specific claims.

**Next action:** §7 Watchpoints (consolidate watch-items: ET premium in May, FX-offset persistence, low-cost-chain margin signals, domestic price/CPI to collect), then §1 Exec Summary last. ICO I-CIP + 한국은행 고시환율 + domestic F&B 1차 data as next data pulls.

**Completed (part 4 — Section 7, same session):**
- Drafted **Section 7 (Next Month Watchpoints)** — consolidated scattered watch-items into one forward-looking list.
- **BA value-add:** each watchpoint is **falsifiable** — paired with a concrete trigger threshold (ET premium ≥ +$0.8, USD/KRW ≥ 1,450 & cost > 10,500원/kg, import < 13,000톤/월) so next month's data can *settle* each hypothesis, not just "monitor."
- Grouped: A) confirmable on next data refresh (ET premium, FX-offset, volume slowdown, origin-mix), B) structural/field (washed tightness, domestic pass-through = §6 verification list), C) methodology cross-checks (ICO I-CIP, 한국은행 고시환율).

**Report status:** §2~§7 drafted. Only **§1 Executive Summary** remains for v0-complete.

**Completed (part 5 — Section 1, v0 COMPLETE):**
- Drafted **Section 1 (Executive Summary)** last, by design — BLUF + 5 findings (each → section) + 비즈니스 함의 + a **신뢰 범위** block separating verified (§2/3/4) vs news-based (§5) vs hypothesis (§6).
- Synthesis spine: 원화 원가 ~2배 ↑ → 외생(시세 ~85% + 환율 ~15%) → 환율이 가격 하락분 상쇄해 고점 고착 → 전가는 저가·스페셜티 양극단 집중 → §7 트리거.
- **🎉 v0 complete: Section 1~7 all drafted.**
- Learning: added 2 newly-surfaced data concepts to `learning_notes.md` tracker (FX/price 곱셈 분해, 전가·잔당 원가 환산) as ⬜ queued — left the "내 말로" one-liners for the user's own active-recall loop per the notes' own rule. (Exec-summary *writing craft* deliberately NOT added — tracker is for domain/data concepts, not writing skill.)

**Completed (part 6 — v0 consistency pass / FREEZE):**
- Full end-to-end audit: every shared number cross-checked across §1~§7 → all agree (원가 5,150→11,030, 85/15, FX 1,327→1,491, ET +$1.07 등). Figures 01~06 exist & match captions; footnotes & cross-refs resolve.
- Fixes: (a) added missing `---` separators before §5/§6/§7; (b) §7 A-3 "약 13,950"→"약 14,000" (2024 was 14,112); (c) standardized all cross-refs `§`→`Section X`; (d) softened §4.3 verified/hypothesis leak ("국내 F&B 원가"→"수입 기준 원가", defer domestic to §6); (e) §2.1 added "/월" to annual averages.
- **v0 FROZEN.**

**Next action (v1 / next cycle):** (1) Collect domestic F&B 1차 data to convert §6 hypotheses → evidence; (2) add ICO I-CIP + 한국은행 고시환율 authoritative cross-checks; (3) refresh with 2026-05 data and test §7 triggers (ET premium ≥+$0.8? FX-offset persists? volume <13k톤?). Optional: a `git` commit of the v0 milestone.

---
