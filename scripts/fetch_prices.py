"""
Fetch international coffee price series from FRED (St. Louis Fed).

Series (IMF Primary Commodity Prices, monthly, US cents per pound):
  PCOFFOTMUSDM  Global price of Coffee, Other Mild Arabicas
  PCOFFROBUSDM  Global price of Coffee, Robusta

No API key needed — FRED exposes a public CSV endpoint:
  https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>

Output adds a USD/kg conversion so prices are directly comparable to the
import unit price in data/processed/monthly_import_summary.csv.
  USD/kg = (US cents/lb) * 0.0220462   # = 1 / (100 cents * 0.453592 kg/lb)

Usage:
  python scripts/fetch_prices.py
"""

import requests
import pandas as pd
from io import StringIO
from pathlib import Path

SERIES = {
    "PCOFFOTMUSDM": "arabica_otm",   # Other Mild Arabicas
    "PCOFFROBUSDM": "robusta",
}
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
START_YM = "2024-01"
OUTPUT   = Path("data/raw/coffee_prices_fred_2024_2026.csv")
USC_LB_TO_USD_KG = 0.0220462


def fetch_series(sid: str) -> pd.Series:
    url = FRED_CSV.format(sid=sid)
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    s = df.set_index("date")["value"]
    s.name = sid
    return s


def main():
    cols = {}
    for sid, label in SERIES.items():
        print(f"  {sid} ... ", end="", flush=True)
        s = fetch_series(sid)
        cols[label] = s
        print(f"{len(s)} obs, latest {s.index.max():%Y-%m}")

    df = pd.DataFrame(cols)
    df.index.name = "date"
    df = df.reset_index()
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    df = df[df["year_month"] >= START_YM].copy()

    # cents/lb -> USD/kg
    df["arabica_otm_usd_per_kg"] = (df["arabica_otm"] * USC_LB_TO_USD_KG).round(3)
    df["robusta_usd_per_kg"]     = (df["robusta"]     * USC_LB_TO_USD_KG).round(3)

    out = df[[
        "year_month",
        "arabica_otm", "robusta",                         # US cents/lb
        "arabica_otm_usd_per_kg", "robusta_usd_per_kg",   # USD/kg
    ]].rename(columns={
        "arabica_otm": "arabica_otm_usc_lb",
        "robusta": "robusta_usc_lb",
    })
    out["source"] = "FRED (IMF Primary Commodity Prices)"

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"\nSaved {len(out)} rows ({out.year_month.min()} -> {out.year_month.max()}) -> {OUTPUT}")


if __name__ == "__main__":
    main()
