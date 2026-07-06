"""
Fetch Korean Consumer Price Index (CPI) sub-items for coffee
from KOSIS OpenAPI (통계청 국가통계포털).

Purpose : domestic retail-price evidence for report Section 6 (전가 검증).
          We pull the item-level CPI table and keep the coffee rows —
          '커피(외식)' (외식 부문, 카페/음식점 한 잔) is the primary pass-through
          signal; '커피' (가공식품, 원두/인스턴트 소매) is the secondary layer.

Data source : 통계청_소비자물가지수(품목별) — KOSIS OpenAPI (파라미터 방식)
Endpoint    : https://kosis.kr/openapi/Param/statisticsParameterData.do
Response    : JSON (list of period×item cells)

Request params (KOSIS 파라미터 방식 — verified with --debug):
  apiKey      발급 인증키 (.env: KOSIS_API_KEY)
  orgId       101  (통계청)
  tblId       DT_1J22112  (소비자물가지수, 시도(C1) × 품목(C2), 월)
  itmId       ALL  (단일 항목 'T' = 소비자물가지수, 2020=100)
  objL1       T10  (전국 — 시도 레벨 C1; 전국만 사용)
  objL2       ALL  (모든 품목 C2 → 그중 '커피' 필터)
  prdSe       M    (월)
  startPrdDe  202401
  endPrdDe    직전월 (YYYYMM)
  format=json, jsonVD=Y

  NOTE: 파라미터 방식은 objL를 명시해야 함 (objL1=ALL 단독은 err20).
  이 표는 2단계 분류라 objL1(시도)+objL2(품목) 둘 다 필요.

Response fields (verified):
  PRD_DE            수록시점  e.g. "202401"
  C1 / C1_NM        시도코드 / 시도명   e.g. "T10" / "전국"
  C2 / C2_NM        품목코드 / 품목명   e.g. "F01K01133" / "커피(외식)"
  ITM_ID / ITM_NM   항목코드 / 항목명   e.g. "T" / "소비자물가지수"
  UNIT_NM  단위      "2020＝100"
  DT       수치      index value (string; jsonVD=Y)

Coffee 품목 codes kept (C2):
  F01K01133  커피(외식)      — 외식 부문 카페/음식점 한 잔 (핵심 전가 신호)
  B01A02101  커피            — 가공식품 원두/인스턴트 소매 (보조 레이어)

Usage:
  python scripts/fetch_cpi_coffee.py --debug   # dump structure: keys + all 품목명 + coffee rows, then exit
  python scripts/fetch_cpi_coffee.py           # fetch 2024-01 → prev month, keep coffee rows, write CSV
"""

import os
import sys
import json
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
load_dotenv()

API_KEY    = os.getenv("KOSIS_API_KEY")
BASE_URL   = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
ORG_ID     = "101"           # 통계청
TBL_ID     = "DT_1J22112"    # 소비자물가지수 (시도 × 품목), 월
REGION     = "T10"           # 전국 (C1)
START_YM   = "202401"
OUTPUT     = Path("data/raw/korea_cpi_coffee_2024_2026.csv")

# Item-name substring used to keep coffee rows (품목명 = C2_NM).
# Matches 커피(외식) F01K01133 and 커피 B01A02101.
COFFEE_KEY = "커피"


# ── Helpers ─────────────────────────────────────────────────────────────────
def prev_month() -> str:
    """Return last month as YYYYMM (latest CPI likely published)."""
    today = datetime.today()
    if today.month == 1:
        return f"{today.year - 1}12"
    return f"{today.year}{today.month - 1:02d}"


def base_params() -> dict:
    return {
        "method"    : "getList",
        "apiKey"    : API_KEY,
        "orgId"     : ORG_ID,
        "tblId"     : TBL_ID,
        "itmId"     : "ALL",
        "objL1"     : REGION,   # 전국
        "objL2"     : "ALL",    # 모든 품목 → '커피' 필터
        "prdSe"     : "M",
        "startPrdDe": START_YM,
        "endPrdDe"  : prev_month(),
        "format"    : "json",
        "jsonVD"    : "Y",
    }


def fetch_raw() -> list | dict:
    """Single call; KOSIS returns a JSON list on success or a dict on error."""
    resp = requests.get(BASE_URL, params=base_params(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def check_api_error(payload) -> None:
    """KOSIS returns {'err':..,'errMsg':..} on failure (dict, not list)."""
    if isinstance(payload, dict) and "err" in payload:
        raise RuntimeError(f"KOSIS API error {payload.get('err')}: {payload.get('errMsg')}")


def item_name(row: dict) -> str:
    """Item (품목) name. In DT_1J22112 the 품목 is C2 (C1 = 시도/전국)."""
    return (row.get("C2_NM") or "").strip()


# ── Debug ─────────────────────────────────────────────────────────────────────
def debug_mode():
    """Reveal table structure: JSON keys, all distinct 품목명, and coffee rows."""
    if not API_KEY:
        sys.exit("ERROR: KOSIS_API_KEY not found in .env")

    print(f"[DEBUG] tblId={TBL_ID}  {START_YM} -> {prev_month()}\n")
    payload = fetch_raw()

    if isinstance(payload, dict):
        print("[DEBUG] response is a dict (likely error):")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        sys.exit(1)

    print(f"[DEBUG] {len(payload)} cells returned.")
    print(f"[DEBUG] keys on first cell: {list(payload[0].keys())}\n")
    print("[DEBUG] first cell:")
    print(json.dumps(payload[0], ensure_ascii=False, indent=2))

    coffee = sorted({(r.get("C2"), item_name(r)) for r in payload if COFFEE_KEY in item_name(r)})
    print(f"\n[DEBUG] coffee 품목 (C2 code / 품목명):")
    for code, n in coffee:
        print(f"   - {code}  {n}")

    measures = sorted({(r.get('ITM_ID'), r.get('ITM_NM')) for r in payload})
    print(f"\n[DEBUG] ITM (항목) values present: {measures}")
    print(f"[DEBUG] region C1 present: {sorted({(r.get('C1'), r.get('C1_NM')) for r in payload})}")
    sys.exit(0)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if "--debug" in sys.argv:
        debug_mode()

    if not API_KEY:
        sys.exit("ERROR: KOSIS_API_KEY not found in .env")

    print(f"Fetching CPI items  tbl={TBL_ID}  {START_YM} -> {prev_month()}\n")
    payload = fetch_raw()
    check_api_error(payload)

    coffee = [r for r in payload if COFFEE_KEY in item_name(r)]
    if not coffee:
        sys.exit(f"ERROR: no rows with '{COFFEE_KEY}' — run --debug to inspect 품목명 / tblId.")

    records = [{
        "year_month": f"{r['PRD_DE'][:4]}-{r['PRD_DE'][4:]}",
        "region"    : r.get("C1_NM", ""),
        "item_code" : r.get("C2", ""),
        "item_name" : item_name(r),
        "measure"   : r.get("ITM_NM", ""),
        "value"     : r.get("DT", ""),
        "unit"      : r.get("UNIT_NM", ""),
        "source"    : "KOSIS OpenAPI (통계청 소비자물가지수, 전국 품목별)",
    } for r in coffee]

    df = pd.DataFrame(records, columns=[
        "year_month", "region", "item_code", "item_name", "measure", "value", "unit", "source",
    ]).sort_values(["item_name", "year_month"]).reset_index(drop=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    items = df["item_name"].unique().tolist()
    print(f"Saved {len(df)} rows -> {OUTPUT}")
    print(f"Coffee items kept: {items}")


if __name__ == "__main__":
    main()
