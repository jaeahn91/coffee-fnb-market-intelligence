"""
Fetch USD/KRW exchange rate from the Frankfurter API (ECB reference rates).

  https://api.frankfurter.dev/v1/<start>..<end>?base=USD&symbols=KRW

Frankfurter serves the European Central Bank's daily reference rates
(published once per business day, ~16:00 CET). We pull the daily USD->KRW
series and resample to a monthly average so it aligns month-for-month with
the monthly price/import series in data/processed/.

Source choice: FRED (DEXKOUS) is the more common pick, but its CSV endpoint
was unreachable from this environment; ECB reference rates are an equally
authoritative, key-free alternative. Caveat: the ECB rate is a daily fixing,
not a volume-weighted market average — fine for monthly trend analysis.

No API key needed.

Usage:
  python scripts/fetch_fx.py
"""

import datetime as dt

import requests
import pandas as pd
from pathlib import Path

BASE      = "USD"
SYMBOL    = "KRW"
START_DAY = "2024-01-01"
API = "https://api.frankfurter.dev/v1/{start}..{end}?base={base}&symbols={sym}"
OUTPUT    = Path("data/raw/fx_usdkrw_ecb_2024_2026.csv")


def fetch_daily() -> pd.Series:
    end = dt.date.today().isoformat()
    url = API.format(start=START_DAY, end=end, base=BASE, sym=SYMBOL)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    rates = resp.json()["rates"]               # {"2024-01-02": {"KRW": 1313.23}, ...}
    s = pd.Series({d: v[SYMBOL] for d, v in rates.items()}, dtype="float64")
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def main():
    print(f"  {BASE}->{SYMBOL} (ECB via Frankfurter) ... ", end="", flush=True)
    daily = fetch_daily()
    print(f"{len(daily)} daily obs, latest {daily.index.max():%Y-%m-%d}")

    # daily -> monthly average; n_obs = #business days behind each average
    monthly = daily.resample("MS").agg(["mean", "count"])
    monthly.columns = ["usdkrw_avg", "n_obs"]
    monthly = monthly.reset_index()
    monthly.columns = ["date", "usdkrw_avg", "n_obs"]
    monthly["year_month"] = monthly["date"].dt.strftime("%Y-%m")

    out = monthly[["year_month", "usdkrw_avg", "n_obs"]].copy()
    out["usdkrw_avg"] = out["usdkrw_avg"].round(2)
    out["source"] = "ECB reference rate (Frankfurter API), daily -> monthly avg"

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"Saved {len(out)} rows ({out.year_month.min()} -> {out.year_month.max()}) -> {OUTPUT}")


if __name__ == "__main__":
    main()
