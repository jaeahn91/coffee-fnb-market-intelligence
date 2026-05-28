"""
Fetch Korean green coffee bean import data (HS 090111)
from Korea Customs Service OpenAPI via data.go.kr.

Data source : 관세청_품목별 국가별 수출입실적 (GW)
Endpoint    : http://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList
Response    : XML

Request params (verified):
  serviceKey, strtYymm (YYYYMM), endYymm (YYYYMM), hsSgn (HS code)
  cntyCd is optional in practice — omit it to get ALL countries at once.

Response fields (verified):
  year            조회기간      e.g. "2024.01"  ("합계" on the total row → skipped)
  statCd          국가코드      e.g. "BR"
  statCdCntnKor1  국가명(국문)  e.g. "브라질"
  statKor         품목명
  hsCd            HS코드        e.g. "0901110000"
  impWgt          수입중량(kg)  — already kg, NO conversion
  impDlr          수입금액(USD) — already USD, NO conversion

Usage:
  python scripts/fetch_imports.py            # fetch 2024-01 → previous month
  python scripts/fetch_imports.py --debug    # print raw XML for first month and exit
"""

import os
import sys
import time
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
load_dotenv()

API_KEY   = os.getenv("CUSTOMS_API_KEY")
BASE_URL  = "http://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList"
HS_CODE   = "090111"
START_YM  = "202401"
OUTPUT    = Path("data/raw/korea_green_bean_imports_hs090111_2024_2026.csv")
NUM_ROWS  = 1000   # countries per month are well under this → single page
DELAY     = 0.3    # seconds between requests


# ── Helpers ─────────────────────────────────────────────────────────────────
def prev_month() -> str:
    """Return last month as YYYYMM (latest likely confirmed data)."""
    today = datetime.today()
    if today.month == 1:
        return f"{today.year - 1}12"
    return f"{today.year}{today.month - 1:02d}"


def month_range(start: str, end: str) -> list[str]:
    """Return list of YYYYMM strings from start to end inclusive."""
    months = []
    y, m = int(start[:4]), int(start[4:])
    ey, em = int(end[:4]), int(end[4:])
    while (y, m) <= (ey, em):
        months.append(f"{y}{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return months


def base_params(yyyymm: str) -> dict:
    return {
        "serviceKey": API_KEY,
        "strtYymm"  : yyyymm,
        "endYymm"   : yyyymm,
        "hsSgn"     : HS_CODE,
        "numOfRows" : str(NUM_ROWS),
        "pageNo"    : "1",
    }


def parse_item(item: ET.Element) -> dict | None:
    """Map one <item> to our CSV schema. Returns None for non-import / total rows."""
    def txt(tag: str) -> str:
        el = item.find(tag)
        return (el.text or "").strip() if el is not None else ""

    year = txt("year")
    stat_cd = txt("statCd")

    # Skip the aggregate/total row (year="합계", statCd="-")
    if stat_cd in ("", "-") or "." not in year:
        return None

    imp_wgt = int(float(txt("impWgt") or 0))
    imp_dlr = int(float(txt("impDlr") or 0))

    # Keep only rows with actual imports
    if imp_wgt == 0 and imp_dlr == 0:
        return None

    return {
        "year_month"      : year.replace(".", "-"),
        "hs_code"         : HS_CODE,
        "item_name"       : txt("statKor") or "Coffee not roasted not decaffeinated",
        "country"         : txt("statCdCntnKor1") or stat_cd,
        "country_code"    : stat_cd,
        "import_weight_kg": imp_wgt,
        "import_value_usd": imp_dlr,
        "source"          : "Korea Customs Service OpenAPI (data.go.kr)",
        "notes"           : "",
    }


# ── Core fetch ───────────────────────────────────────────────────────────────
def fetch_month(yyyymm: str) -> list[dict]:
    resp = requests.get(BASE_URL, params=base_params(yyyymm), timeout=20)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    result_code = (root.findtext(".//resultCode") or "").strip()
    if result_code not in ("00", "0"):
        msg = (root.findtext(".//resultMsg") or "unknown").strip()
        raise RuntimeError(f"API error {result_code}: {msg}")

    records = []
    for item in root.findall(".//item"):
        row = parse_item(item)
        if row:
            records.append(row)
    return records


def debug_mode():
    """Print raw XML response for the first month and exit."""
    print(f"[DEBUG] Calling API for {START_YM}...\n")
    resp = requests.get(BASE_URL, params=base_params(START_YM), timeout=20)
    print(f"[DEBUG] status={resp.status_code}  content-type={resp.headers.get('content-type')}\n")
    print(resp.text[:4000])
    sys.exit(0)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if "--debug" in sys.argv:
        debug_mode()

    if not API_KEY:
        sys.exit("ERROR: CUSTOMS_API_KEY not found in .env")

    end_ym = prev_month()
    months = month_range(START_YM, end_ym)
    print(f"Fetching HS {HS_CODE} import data  {START_YM} -> {end_ym}  ({len(months)} months)\n")

    all_records = []
    for yyyymm in months:
        print(f"  {yyyymm[:4]}-{yyyymm[4:]} ... ", end="", flush=True)
        try:
            rows = fetch_month(yyyymm)
            all_records.extend(rows)
            print(f"{len(rows)} rows")
        except Exception as e:
            print(f"ERROR: {e}")
        time.sleep(DELAY)

    df = pd.DataFrame(all_records, columns=[
        "year_month", "hs_code", "item_name", "country", "country_code",
        "import_weight_kg", "import_value_usd", "source", "notes",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"\nSaved {len(df)} rows -> {OUTPUT}")


if __name__ == "__main__":
    main()
