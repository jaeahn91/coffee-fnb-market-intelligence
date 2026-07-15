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

## Day 7 — 2026-05 Data Refresh & §7 Trigger Settlement

**Goal:** Execute v1 item (3) — refresh all raw series with 2026-05 data and settle the three confirmable §7 watch-item triggers (A-1 ET premium, A-2 FX-offset, A-3 volume slowdown).

**Completed (data refresh):**
- Re-ran `scripts/fetch_imports.py` → import CSV now **1,126 rows** (added 2026-05, +44 rows). Integrity re-checked: git diff **+44/-0** (no past rows altered), **0 dupes / 0 nulls / 0 negatives**. (commit `a208b95`)
- Re-ran `scripts/fetch_prices.py` → FRED arabica/robusta extended to 2026-05.
  - **Bug fix:** `fetch_prices.py` still used `pd.read_csv(url)` (urllib path → macOS SSL `CERTIFICATE_VERIFY_FAILED`). Switched to `requests.get` + `StringIO` — the same certifi fix Day 6 applied to `fetch_fx.py` but missed here.
- FX series (`fetch_fx.py`) already through 2026-06 (June partial, 5 obs); no refetch needed.

**§7 triggers — all three settled (trigger thresholds from Day 6 §7):**
- **A-1 ET premium (≥ +$0.8/kg):** 2026-05 = **+$1.03/kg** (ET $8.10 vs basket $7.07; ET volume 1,610톤, +6%). Well above threshold for a **second consecutive month** → April's +$1.07 was **not noise**; supply-tightness signal confirmed. Recorded in `docs/origin_notes_ethiopia_2026q1.md` (commit `3cac91f`). Caveat: May may be provisional; HS090111 blended unit price = *direction-consistent* signal, not proof of washed shortage.
- **A-3 volume slowdown (< 13,000톤/월):** 2026-05 = **11,412톤 < 13,000** → triggered. 2026 avg **11,891톤/월** vs 2024 14,112 / 2025 13,952; April's 13,610 was an **isolated bounce**, not a trend reversal → slowdown **reinforced**.
- **A-2 FX-offset persistence (USD/KRW ≥ 1,450 & 원가 > 10,500원/kg):** From the 2025-05 USD-price peak to 2026-05 — arabica **−20.1%**, FX **+7.4%**, won cost **−4.8%**. May: arabica $7.00, import unit price $7.07, FX 1,490.92, **won cost 10,542원/kg** (just above 10,500 threshold; April was 10,178, below). Both conditions met → **FX still absorbing the global price relief**; won cost stays rigid/elevated. June FX 1,526 (partial) → no easing in sight.

**Key insight:** All three confirmable triggers fired in the **same direction as the v0 hypotheses** — this is the watch-item framework *working as designed* (falsifiable thresholds → next-month data settles them, not "keep monitoring"). The story holds one month out: tight ET supply, slowing volume, and an FX-locked won cost that denies importers the world price decline.

**Next action (v1, remaining):** (1) Collect domestic F&B 1차 data (CPI 외식 커피, 프랜차이즈 가격) to convert §6 hypotheses → evidence; (2) add ICO I-CIP + 한국은행 고시환율 authoritative cross-checks (§7 group C). Optional: regenerate processed CSVs + re-run notebooks (still April-based) and roll a 2026-06 report once that month's data closes.

---

## Day 8 — PLAN: Domestic F&B 1차 Data Collection (→ §6 evidence)

> **Status: PLAN only — nothing collected yet.** This entry scopes v1 item (1) before any fetch.

**Goal:** Pull *domestic* primary data so Section 6 (Korean F&B Implications) can move from **hypothesis → evidence**. Today §6 is built on a wholesale→per-cup *mechanism* (green bean ~+100원/잔, ~7% of a 1,500원 저가 아메리카노 vs ~2% premium) with **no Korean retail/CPI data** behind it.

**Why now:** §2~§5 are import/price/FX/origin — all *upstream* (수입 단가까지). §6 is the only section claiming a *domestic* consequence, yet it's the least evidenced. Closing this gap is the single biggest credibility upgrade left in v1.

**The question this data must settle (falsifiable, BA framing):**
- Did the upstream cost shock (원화 원가 ~2배) **actually pass through** to Korean retail coffee prices — and if so, **how much and where** (저가 vs 프리미엄)?
- Three outcomes, each meaningful: (a) retail rose ~in step → pass-through high; (b) retail flat → margin absorbed (저가 체인 마진 압박 = §7 watch); (c) lagged → timing story.

**Target data (candidates — sources to VERIFY before trusting):**
1. **CPI 외식 커피 / 가공식품 커피** — KOSIS (통계청 국가통계포털). 외식 부문 '커피(외식)' 및 가공식품 '커피' 지수, 월별, 2024-01~. → retail price *trend* vs our wholesale cost trend (the core pass-through test).
2. **프랜차이즈 메뉴 가격** — 저가(예: 메가/컴포즈 류), 중가(스타벅스 류), 시점별 아메리카노 표시가격. 보도자료·기사·공시 기반 (브랜드별 1차 수집은 노이즈/시점 주의). → §6의 가격대 가정(1,500원 등) 실측 검증.
3. **(선택) 한국은행/통계청 생산자물가(PPI) 커피 가공품** — 도매·가공 단계 물가, 수입단가와 retail 사이 중간 레이어.

**Acceptance (what upgrades §6 to "evidence"):**
- At least **CPI 외식 커피 월별 시계열 (2024~2026)** ingested as a raw CSV (same pipeline shape as other `data/raw/*`), with a source row in `source_tracker.csv`.
- One cross-check chart: **수입 원화 원가 vs CPI 외식 커피** (index both to 2024-01=100) → lead/lag & pass-through 정도를 *눈으로* 확인.
- §6 prose updated: replace ≥1 hypothesis sentence with a data-backed one (or explicitly confirm "전가 약함 = 마진 흡수" if that's what the data shows).

**Risks / open questions (decide before/while collecting):**
- **Granularity gap (다시 §5의 교훈):** CPI '외식 커피'는 집계라 저가/프리미엄 분해가 안 됨 → 프랜차이즈 표시가로 보강하되 *예시*임을 명시.
- **전가 시차:** retail은 메뉴판 개정 주기로 끈끈(sticky) → 단기 미반영이 "전가 없음"은 아님(끝점 민감도 주의).
- **구성효과:** CPI '외식 커피'엔 원두커피 외 메뉴·매장유형 믹스가 섞임 → 100% 생두 전가로 못 읽음.
- API/수집 경로 미확정: KOSIS는 OpenAPI(인증키) 또는 수기 CSV 다운로드 — Day 3 import 때처럼 먼저 `--debug`로 스펙 확인.

**Next action (Day 9 실행):** KOSIS에서 'CPI 외식 커피' 시리즈 식별 → 수집 경로(API vs 수기) 확정 → `scripts/fetch_cpi_coffee.py`(또는 수기 CSV) + `data/raw/`에 적재 → 수입 원화원가 대비 인덱스 비교 차트 → §6 1문장 evidence化.

---

## Day 9 — Domestic F&B 1차 Data 수집·검증 (CPI 커피 → §6 evidence)

**Goal:** Day 8 plan 실행. KOSIS CPI 커피 시계열을 적재하고 수입 원화원가 대비 전가 정도를 데이터로 확인.

**Completed (수집 경로 확정):**
- **Keyless 경로 없음 확인:** KOSIS 웹 통계표(`statHtml.do`)는 SSO 로그인으로 리다이렉트, OpenAPI는 키 없이 `err=10 인증 KEY 누락`. → 인증키 필수. 사용자가 kosis.kr 인증키 발급 → `.env`의 `KOSIS_API_KEY`. (초기 `.env.txt` 저장 → `.env`로 리네임: 메모장 확장자 이슈.)
- **API 스펙 확정 (probe-first, Day 3 방식):** 표 `DT_1J22112` = 소비자물가지수(**시도 C1 × 품목 C2**). 파라미터 방식(`statisticsParameterData.do`)은 `objL`를 명시해야 함 — `objL1=T10`(전국)+`objL2=ALL` 조합에서 정상. 커피 품목코드 **`F01K01133` 커피(외식)** / **`B01A02101` 커피(가공식품)**, 항목 `T`=지수(2020=100).
- `scripts/fetch_cpi_coffee.py` 작성 → `data/raw/korea_cpi_coffee_2024_2026.csv` (2품목 × 30개월 = 60행, 2024-01~2026-06, 결측 0). `source_tracker.csv` domestic KOSIS 행 → done.

**Completed (환경):** 이 머신에 Python 부재 → winget으로 3.12.10 설치 + `.venv` 생성 + requirements 설치(requests/pandas/dotenv/matplotlib).

**Key insight (→ §6 evidence):**
- **상류에서 하류로 전가가 감쇠한다.** 2024-01→2026-03: 수입 원화 원가 **+114%(≈2배)** → 커피 가공식품(원두 소매) **+15.8%** → 커피 외식(한 잔) **+4.4%**(2026-06까지 동일).
- +4.4%는 §6.1 잔당 산식이 예측한 폭(생두 비중 2~7% × 전가 → +2~8%) 안에 들어 메커니즘과 **정량적으로 부합** — "생두값 2배 ≠ 판매가 2배" 데이터로 확인.
- 외식 CPI는 2025 H1에 1회성 계단(+4%p) 뒤 평탄(2025-07~12 여섯 달 111.43 동일) → 메뉴가 경직성·6~12개월 시차의 전형.
- **Non-overstatement:** 외식 CPI는 집계지수(매장유형·비생두 원가 혼합)라 순수 생두 전가율·마진흡수 입증 아님. 저가/프리미엄 구간 분해 불가(§5 교훈 재연) → 프랜차이즈 실판매가는 잔여 과제.
- 근거 노트 `docs/domestic_passthrough_cpi_2026.md` (발행준비 §6.5 문단 포함), 차트 `reports/figures/07_import_cost_vs_cpi_coffee.png` (`scripts/plot_cost_vs_cpi.py`).

**Housekeeping (하네스):**
- 새 CPI 파일을 Tier-1 무결성 가드(`validate_data.py`)에 편입 → PASS. Tier-2 골든 13개 불변(PASS) — CPI 추가가 기존 수치 무영향 확인.
- **크로스플랫폼 버그 fix:** `check_figures.py`·`validate_data.py`가 최종 `print("PASS —")`의 em대시를 cp949 콘솔에 출력하다 크래시(exit 1) → `sys.stdout.reconfigure(encoding="utf-8")` 추가. 검사 로직·골든값 불변. (macOS 개발 → Windows 실행 격차.)

**v0 freeze 존중:** v0 리포트(2026 5월호) 본문은 수정하지 않음. CPI 증거는 노트에 **발행준비 상태**로 두고, v1 발행 시 §6.5로 접붙임 (CHANGELOG 버전 규율).

**Next action (v1 잔여):** (1) 프랜차이즈 구간별 실판매가 → §6.2 양극단 비대칭 검증; (2) (선택) ICO I-CIP + 한국은행 고시환율 교차검증; (3) v1 발행 시 processed/notebook 재생성 + `check_figures.py --update`. **미결정(사용자):** CPI 증거를 지금 v1 리포트 초안으로 착수할지, 노트에 대기시킬지. **커밋 시 주의:** pre-commit 훅이 `.venv/bin/python`(Unix 경로) 참조 → Windows에선 `.venv/Scripts/python.exe` 미스매치로 훅이 python을 못 찾음. 커밋하려면 훅 크로스플랫폼화 or `--no-verify`(단, 하네스는 위에서 수동 green 확인).

---

## Day 10 — v1 발행: 6월호 트리거 검증호 (Verification Issue)

**Goal:** Day 9까지 은행에 쌓인 §7 트리거 정산(Day 7)과 §6 CPI 검증(Day 9)을 **실제 발행물**로 패키징. 조언 반영 — "월간이라더니 5월 1편"으로 읽히지 않도록, 5월호가 스스로 건 검증 가능한 트리거를 새 데이터로 판정하는 6월호를 낸다. 사용자 결정: **린 v1 완성호**(트리거 판정 + CPI 전가 evidence 둘 다 담되 분량은 절반).

**Completed:**
- **2026-05 헤드라인 수치 raw 재검증:** `scripts` 없이 raw 3종에서 직접 산출 → Day 7 로그와 **전부 일치**(오차 없음). 수입단가 $7.071, 물량 11,411톤, 아라비카 $7.00, FX 1,490.92, 원화 원가 10,542원, ET 프리미엄 +$1.03, ET 물량 1,610톤. 2025-05 정점→2026-05: 아라비카 −20.1% / FX +7.4% / 원화 원가 −4.8%. 2026 월평균(1~5월) 11,891톤.
- **리포트 발행:** `reports/monthly_coffee_market_brief_2026_06.md` (v1). 구조 — §1 Exec / §2 트리거 판정(A-1/A-2/A-3 ✅, A-4는 미판정 명시) / §3 데이터 델타 / §4 국내 전가 CPI evidence(그림 07) / §5 갱신 Watchpoints(신규 트리거 C-1 = 프랜차이즈 구간가 비대칭).
- **판정 결과:** 세 트리거 모두 v0 가설과 **같은 방향으로 확정(반증 안 됨)**. 반증 가능성 프레임이 "지켜보자"가 아니라 숫자 정산으로 작동함을 입증.
- **CHANGELOG:** v1을 *진행 중* → *발행 완료(트리거 검증호)*로 갱신. README 최신호 포인터를 6월호로 교체 + "반증 가능성은 실행이다" 헤드라인 추가(조언의 다운그레이드 대신 정직한 업그레이드 경로).

**린 발행 판단 (규율):**
- processed CSV/노트북 **재생성 안 함.** 2026-05 수치는 raw에서 직접 산출해 판정표에 실음. 이유: 골든 가드(`check_figures.py`)가 모든 지표를 `data_cut` 윈도우로 고정 → 새 달 추가가 과거 골든 13개를 바꾸지 않음(오탐 없음). v0 processed 레이어는 v0 골든의 재현 앵커로 frozen 유지.
- **이월:** 차트를 2026-05로 연장 + 구성효과(A-4) 재계산 + `check_figures.py --update`로 골든 재캡처는 다음 사이클로. 이번 호는 트리거 판정표가 시각적 주인공이라 신규 차트 없이 성립.

**정직한 관찰(과장 방지):** A-2 원화 원가 10,542원은 임계선 10,500을 *간신히* 넘김(4월은 10,178으로 임계선 아래였음) → 원가는 임계선 근처 진동 + 정점 대비 −4.8% 완만한 하락. 트리거는 "FX 상쇄 여전히 작동"까지만 말하며 "원가 재급등"이 아님. §4 CPI도 집계지수라 순수 생두 전가율/마진 흡수 입증 아님 — 데이터는 "2배가 판매가로 안 왔다"까지.

**Next action (v2 후보):** (1) 프랜차이즈 구간별 실판매가 → §6.2/C-1 양극단 비대칭 검증(최대 공백); (2) 차트 2026-05 연장 + processed/골든 재캡처; (3) (선택) ICO I-CIP·한국은행 고시환율 교차검증.

---
