"""
Cross-check chart for report Section 6 (국내 전가 검증):
upstream 수입 원화 원가 vs 국내 소비자물가(외식 커피 · 가공식품 커피),
all indexed to 2024-01 = 100 so the pass-through gap is visible at a glance.

Inputs:
  data/processed/fx_and_cost_decomposition.csv   (import_krw_per_kg)   ← 원가 (frozen v0 window)
  data/raw/korea_cpi_coffee_2024_2026.csv        (KOSIS CPI, 전국)      ← 소매 물가

Output:
  reports/figures/07_import_cost_vs_cpi_coffee.png

Both series are indexed to their common start (2024-01). The cost series is the
v0-frozen processed layer (ends 2026-03); the chart uses the overlapping window
so the two lines share an axis. Reproducible: same shape as the fetch scripts.

Usage:
  python scripts/plot_cost_vs_cpi.py
"""

from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Korean labels need a CJK-capable font; Malgun Gothic ships with Windows.
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

PROC = Path("data/processed")
RAW = Path("data/raw")
OUT = Path("reports/figures/07_import_cost_vs_cpi_coffee.png")

COFFEE_OUTSIK = "F01K01133"   # 커피(외식)
COFFEE_PROC = "B01A02101"     # 커피(가공식품)


def indexed(series: pd.Series) -> pd.Series:
    """Index a monthly series to its first value = 100."""
    return series / series.iloc[0] * 100


def main():
    cost = pd.read_csv(PROC / "fx_and_cost_decomposition.csv")[
        ["year_month", "import_krw_per_kg"]
    ]

    cpi = pd.read_csv(RAW / "korea_cpi_coffee_2024_2026.csv")
    cpi["value"] = pd.to_numeric(cpi["value"], errors="coerce")
    outsik = cpi[cpi["item_code"] == COFFEE_OUTSIK][["year_month", "value"]].rename(
        columns={"value": "cpi_outsik"})
    proc = cpi[cpi["item_code"] == COFFEE_PROC][["year_month", "value"]].rename(
        columns={"value": "cpi_proc"})

    # Common window = overlap of cost (→2026-03) and CPI (→2026-06).
    df = cost.merge(outsik, on="year_month").merge(proc, on="year_month")
    df = df.sort_values("year_month").reset_index(drop=True)

    df["cost_idx"] = indexed(df["import_krw_per_kg"])
    df["outsik_idx"] = indexed(df["cpi_outsik"])
    df["proc_idx"] = indexed(df["cpi_proc"])

    x = range(len(df))
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(x, df["cost_idx"], color="#c0392b", lw=2.4, marker="o", ms=3,
            label="수입 생두 원화 원가 (원/kg)")
    ax.plot(x, df["proc_idx"], color="#e67e22", lw=2.0, marker="s", ms=3,
            label="커피 CPI · 가공식품(원두/인스턴트 소매)")
    ax.plot(x, df["outsik_idx"], color="#2c3e50", lw=2.2, marker="^", ms=3,
            label="커피 CPI · 외식(카페 한 잔)")

    ax.axhline(100, color="#999999", lw=0.8, ls="--")

    # Endpoint labels
    last = len(df) - 1
    for col, txt, dy in [("cost_idx", "원가", 4), ("proc_idx", "가공식품", 0),
                          ("outsik_idx", "외식", -2)]:
        v = df[col].iloc[last]
        ax.annotate(f"{txt} {v:.0f}", (last, v), textcoords="offset points",
                    xytext=(8, dy), fontsize=9, va="center")

    step = max(1, len(df) // 12)
    ax.set_xticks(list(x)[::step])
    ax.set_xticklabels(df["year_month"][::step], rotation=45, ha="right", fontsize=8)

    ax.set_title("상류 원가는 2배, 소매 '한 잔' 값은 거의 그대로\n"
                 "수입 원화 원가 vs 국내 커피 소비자물가 (2024-01 = 100)",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("지수 (2024-01 = 100)")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.25)

    cut = df["year_month"].iloc[last]
    ax.text(0.99, 0.02,
            f"원가: 본 리포트 Section 4 (frozen, ~{cut}) · CPI: KOSIS 전국 (2020=100)",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7, color="#666666")

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150)
    print(f"Saved -> {OUT}")
    print(df[["year_month", "cost_idx", "proc_idx", "outsik_idx"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
