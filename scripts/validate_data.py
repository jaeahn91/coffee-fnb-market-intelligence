"""
Tier-1 data-integrity harness for the raw datasets.

Codifies the checks we used to run by hand on every refresh so they can't be
forgotten: duplicate keys, missing values, negatives, month continuity, a
preserved start month, and a sanity band on the headline unit prices.

Run after any fetch and before committing:
  .venv/bin/python scripts/validate_data.py
Exit code 0 = all pass; 1 = at least one failure (safe to wire into a hook).
"""

import sys
from pathlib import Path
import pandas as pd

# Windows consoles default to cp949; force UTF-8 so Korean / em-dash print without crashing.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

RAW = Path("data/raw")


def months(series: pd.Series) -> list[str]:
    return sorted(series.astype(str).unique())


def is_contiguous(ym: list[str]) -> bool:
    rng = pd.period_range(ym[0], ym[-1], freq="M").strftime("%Y-%m").tolist()
    return ym == rng


# (file, key cols, non-null cols, non-negative cols, expected start month)
CHECKS = [
    {
        "file": "korea_green_bean_imports_hs090111_2024_2026.csv",
        "keys": ["year_month", "country_code"],
        "non_null": ["year_month", "country_code", "import_weight_kg", "import_value_usd"],
        "non_neg": ["import_weight_kg", "import_value_usd"],
        "start": "2024-01",
    },
    {
        "file": "coffee_prices_fred_2024_2026.csv",
        "keys": ["year_month"],
        "non_null": ["year_month", "arabica_otm_usd_per_kg", "robusta_usd_per_kg"],
        "non_neg": ["arabica_otm_usd_per_kg", "robusta_usd_per_kg"],
        "start": "2024-01",
    },
    {
        "file": "fx_usdkrw_ecb_2024_2026.csv",
        "keys": ["year_month"],
        "non_null": ["year_month", "usdkrw_avg"],
        "non_neg": ["usdkrw_avg", "n_obs"],
        "start": None,  # fx series starts 2023-12; just require contiguity
    },
    {
        "file": "korea_cpi_coffee_2024_2026.csv",
        "keys": ["year_month", "item_code"],  # 2 품목 (외식/가공식품) × months
        "non_null": ["year_month", "item_code", "value"],
        "non_neg": ["value"],
        "start": "2024-01",
    },
]


def check_file(cfg: dict, fails: list[str]) -> None:
    path = RAW / cfg["file"]
    df = pd.read_csv(path)
    tag = cfg["file"]

    dup = df.duplicated(subset=cfg["keys"]).sum()
    if dup:
        fails.append(f"{tag}: {dup} duplicate rows on {cfg['keys']}")

    for c in cfg["non_null"]:
        n = df[c].isna().sum()
        if n:
            fails.append(f"{tag}: {n} nulls in '{c}'")

    for c in cfg["non_neg"]:
        n = (df[c] < 0).sum()
        if n:
            fails.append(f"{tag}: {n} negative values in '{c}'")

    ym = months(df["year_month"])
    if not is_contiguous(ym):
        fails.append(f"{tag}: month gap in series ({ym[0]}..{ym[-1]})")
    if cfg["start"] and ym[0] != cfg["start"]:
        fails.append(f"{tag}: start month {ym[0]} != expected {cfg['start']} (history truncated?)")

    print(f"  {tag:<52} {len(df):>5} rows  {ym[0]}..{ym[-1]}")


def check_unit_price_band(fails: list[str]) -> None:
    """Aggregate monthly import unit price must stay in a plausible band."""
    df = pd.read_csv(RAW / "korea_green_bean_imports_hs090111_2024_2026.csv")
    g = df.groupby("year_month").apply(
        lambda x: x["import_value_usd"].sum() / x["import_weight_kg"].sum(), include_groups=False
    )
    out = g[(g < 2.0) | (g > 15.0)]
    if len(out):
        fails.append(f"imports: unit price outside $2-15/kg band: {out.to_dict()}")


def main() -> int:
    fails: list[str] = []
    print("Tier-1 integrity checks:")
    for cfg in CHECKS:
        check_file(cfg, fails)
    check_unit_price_band(fails)

    print()
    if fails:
        print(f"FAIL ({len(fails)}):")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("PASS — all integrity checks clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
