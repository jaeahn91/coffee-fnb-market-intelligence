"""
Tier-2 golden-figure harness.

The frozen report cites pinned numbers (원가 5,150 -> 11,030, corr 0.87,
가격/환율 85/15, ET 프리미엄 +$1.07 ...). When the processed layer is
regenerated, those numbers must NOT drift silently. This recomputes each headline
figure from the data — every window-dependent metric is computed only over rows
up to its `data_cut`, so adding a new month never false-alarms; only a genuine
change in history or logic does.

  .venv/bin/python scripts/check_figures.py            # verify against golden
  .venv/bin/python scripts/check_figures.py --update   # recapture golden (intentional, e.g. v1)

Exit 0 = all within tolerance; 1 = drift detected.
"""

import sys
import json
import math
from pathlib import Path
import pandas as pd

PROC = Path("data/processed")
RAW = Path("data/raw")
GOLDEN = Path("tests/expected_figures.json")


def _imports():
    return pd.read_csv(RAW / "korea_green_bean_imports_hs090111_2024_2026.csv")


def _summary():
    return pd.read_csv(PROC / "monthly_import_summary.csv")


def _price():
    return pd.read_csv(PROC / "price_vs_import_unitprice.csv")


def _fx():
    return pd.read_csv(PROC / "fx_and_cost_decomposition.csv")


def _cut(df, ym):
    return df[df["year_month"].astype(str) <= ym]


def _cell(df, ym, col):
    return float(df.loc[df["year_month"] == ym, col].iloc[0])


# Each metric: id -> (compute_fn, data_cut, tolerance, human description)
METRICS = {
    "import_unitprice_2024_01": (lambda: _cell(_summary(), "2024-01", "avg_unit_price_usd_per_kg"),
                                 "2024-01", 0.01, "수입 평균단가 $/kg @2024-01"),
    "import_unitprice_2026_03": (lambda: _cell(_summary(), "2026-03", "avg_unit_price_usd_per_kg"),
                                 "2026-03", 0.01, "수입 평균단가 $/kg @2026-03"),
    "import_krw_2024_01": (lambda: _cell(_fx(), "2024-01", "import_krw_per_kg"),
                           "2024-01", 1.0, "원화 수입원가 원/kg @2024-01"),
    "import_krw_2026_03": (lambda: _cell(_fx(), "2026-03", "import_krw_per_kg"),
                           "2026-03", 1.0, "원화 수입원가 원/kg @2026-03"),
    "krw_cost_peak_to_cut_pct": (lambda: 100 * (_cell(_fx(), "2026-03", "import_krw_per_kg")
                                                / _cell(_fx(), "2025-05", "import_krw_per_kg") - 1),
                                 "2026-03", 0.2, "FX 상쇄: 원가 변화 % (2025-05 정점->2026-03)"),
    "corr_level_arabica": (lambda: _cut(_price(), "2026-03")[
        ["korea_import_usd_per_kg", "arabica_otm_usd_per_kg"]].corr().iloc[0, 1],
        "2026-03", 0.01, "수입단가 vs 아라비카 레벨 상관"),
    "corr_level_robusta": (lambda: _cut(_price(), "2026-03")[
        ["korea_import_usd_per_kg", "robusta_usd_per_kg"]].corr().iloc[0, 1],
        "2026-03", 0.01, "수입단가 vs 로부스타 레벨 상관"),
    "price_contribution_pct": (lambda: _decomp("2026-03")[0],
                               "2026-03", 1.0, "원가 변동 중 가격 기여 %"),
    "fx_contribution_pct": (lambda: _decomp("2026-03")[1],
                            "2026-03", 1.0, "원가 변동 중 환율 기여 %"),
    "import_ton_2024_avg": (lambda: _year_avg_ton("2024"),
                            "2024-12", 1.0, "월평균 수입 톤 (2024)"),
    "import_ton_2025_avg": (lambda: _year_avg_ton("2025"),
                            "2025-12", 1.0, "월평균 수입 톤 (2025)"),
    "import_ton_2026_to_apr_avg": (lambda: _range_avg_ton("2026-01", "2026-04"),
                                   "2026-04", 1.0, "월평균 수입 톤 (2026-01~04)"),
    "et_premium_2026_04": (lambda: _et_premium("2026-04"),
                           "2026-04", 0.02, "에티오피아 단가 프리미엄 $/kg @2026-04"),
}


def _decomp(cut):
    fx = _fx()
    a = fx[fx["year_month"] == "2024-01"].iloc[0]
    b = fx[fx["year_month"] == cut].iloc[0]
    d_total = math.log(b["import_krw_per_kg"] / a["import_krw_per_kg"])
    d_price = math.log(b["korea_import_usd_per_kg"] / a["korea_import_usd_per_kg"])
    d_fx = math.log(b["usdkrw_avg"] / a["usdkrw_avg"])
    return 100 * d_price / d_total, 100 * d_fx / d_total


def _year_avg_ton(year):
    s = _summary()
    return s[s["year_month"].str.startswith(year)]["total_weight_ton"].mean()


def _range_avg_ton(lo, hi):
    s = _summary()
    m = (s["year_month"] >= lo) & (s["year_month"] <= hi)
    return s[m]["total_weight_ton"].mean()


def _et_premium(ym):
    imp = _imports()
    month = imp[imp["year_month"] == ym]
    overall = month["import_value_usd"].sum() / month["import_weight_kg"].sum()
    et = month[month["country_code"] == "ET"]
    et_price = et["import_value_usd"].sum() / et["import_weight_kg"].sum()
    return et_price - overall


def compute_all() -> dict:
    return {k: {"value": round(float(fn()), 4), "data_cut": cut, "tol": tol, "desc": desc}
            for k, (fn, cut, tol, desc) in METRICS.items()}


def update():
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(json.dumps(compute_all(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(METRICS)} golden figures -> {GOLDEN}")


def verify() -> int:
    if not GOLDEN.exists():
        print(f"No golden file at {GOLDEN}; run with --update first.")
        return 1
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    fails = []
    print("Tier-2 golden-figure checks:")
    for k, (fn, cut, tol, desc) in METRICS.items():
        got = float(fn())
        exp = expected.get(k, {}).get("value")
        if exp is None:
            fails.append(f"{k}: missing from golden file")
            continue
        ok = abs(got - exp) <= tol
        flag = "ok " if ok else "DRIFT"
        print(f"  [{flag}] {k:<32} got={got:<12.4f} golden={exp:<12.4f} (±{tol})  {desc}")
        if not ok:
            fails.append(f"{k}: {got:.4f} vs golden {exp:.4f} (tol ±{tol})")
    print()
    if fails:
        print(f"FAIL ({len(fails)}) — figures drifted from golden:")
        for f in fails:
            print(f"  - {f}")
        print("If this change is intentional (e.g. v1 data-cut), rerun with --update.")
        return 1
    print("PASS — all figures match golden within tolerance.")
    return 0


if __name__ == "__main__":
    if "--update" in sys.argv:
        update()
        sys.exit(0)
    sys.exit(verify())
