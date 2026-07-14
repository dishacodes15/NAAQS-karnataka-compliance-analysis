"""
NAAQS Compliance & Exceedance Analysis for Karnataka AQI stations.

Reads your consolidated karnataka_aqi_master.csv and computes, per station:
  - % of monitored days exceeding India's 24-hr NAAQS limit, per pollutant
  - An overall "worst offender" ranking across all pollutants
  - A yearly trend (is it getting better or worse?)

Usage:
    pip install pandas matplotlib
    python naaqs_compliance.py
"""

import pandas as pd
from pathlib import Path
 
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "../processed_data/karnataka_aqi_master.csv"
OUTPUT_FILE = BASE_DIR / "../processed_data/naaqs_compliance_summary.csv"

# CPCB NAAQS 2009 — 24-hour (or 8-hr proxy for CO/O3) limits, µg/m3 unless noted
NAAQS_24HR = {
    "pm25": 60,
    "pm10": 100,
    "no2": 80,
    "so2": 80,
    "co": 2,      # mg/m3
    "o3": 100,
    "nh3": 400,
}

def main():
    df = pd.read_csv(INPUT_FILE, parse_dates=["date"])
    print(f"Loaded {len(df)} rows, {df['station'].nunique()} stations, "
          f"date range {df['date'].min().date()} to {df['date'].max().date()}\n")

    results = []
    for (station, city), group in df.groupby(["station", "city"]):
        row = {"station": station, "city": city, "total_monitored_days": len(group)}
        exceedance_flags = []

        for pollutant, limit in NAAQS_24HR.items():
            if pollutant not in group.columns:
                continue
            valid = group[pollutant].dropna()
            if len(valid) == 0:
                continue
            exceed_pct = (valid > limit).mean() * 100
            row[f"{pollutant}_pct_exceed_days"] = round(exceed_pct, 1)
            row[f"{pollutant}_avg"] = round(valid.mean(), 1)
            row[f"{pollutant}_max"] = round(valid.max(), 1)
            exceedance_flags.append(exceed_pct)

        # Overall "badness score" — average exceedance % across all pollutants measured
        row["overall_exceedance_score"] = round(sum(exceedance_flags) / len(exceedance_flags), 1) if exceedance_flags else None
        results.append(row)

    summary = pd.DataFrame(results).sort_values("overall_exceedance_score", ascending=False)
    summary.to_csv(OUTPUT_FILE, index=False)

    print("=== Top 10 worst stations by overall NAAQS exceedance ===")
    display_cols = ["station", "city", "overall_exceedance_score",
                     "pm25_pct_exceed_days", "pm10_pct_exceed_days", "no2_pct_exceed_days"]
    display_cols = [c for c in display_cols if c in summary.columns]
    print(summary[display_cols].head(10).to_string(index=False))

    print(f"\nFull detailed breakdown saved to {OUTPUT_FILE}")

    # Yearly trend: is each station's PM2.5 exceedance getting better or worse?
    print("\n=== Yearly PM2.5 exceedance trend (is it improving?) ===")
    df["year"] = df["date"].dt.year
    yearly = df.groupby(["station", "year"])["pm25"].apply(
        lambda x: (x.dropna() > NAAQS_24HR["pm25"]).mean() * 100
    ).reset_index(name="pm25_pct_exceed")
    pivot_yearly = yearly.pivot(index="station", columns="year", values="pm25_pct_exceed")
    print(pivot_yearly.round(1).to_string())
    pivot_yearly.to_csv("naaqs_yearly_trend.csv")
    print("\nYearly trend saved to naaqs_yearly_trend.csv")

if __name__ == "__main__":
    main()