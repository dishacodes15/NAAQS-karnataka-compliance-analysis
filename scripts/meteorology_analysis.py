"""
Meteorology -> pollution relationship analysis for Karnataka AQI stations.

Quantifies how wind speed, humidity, and rainfall relate to PM2.5, and
shows the seasonal (winter vs monsoon) pollution pattern.

Requires karnataka_aqi_master.csv to have been regenerated with the
updated consolidate_aqi.py (which now keeps temp/humidity/wind_speed/
wind_dir/rainfall columns).

Usage:
    pip install pandas numpy
    python meteorology_analysis.py
"""

import pandas as pd
import numpy as np

INPUT_FILE = "../processed_data/karnataka_aqi_master.csv"

# Karnataka's rough seasonal calendar for framing the analysis
WINTER_MONTHS = [11, 12, 1, 2]     # low wind, inversions, pollution builds up
MONSOON_MONTHS = [6, 7, 8, 9]      # rainfall scrubs the air

def simple_regression(x, y):
    """Returns slope, intercept, and R for a clean x/y pair (drops NaNs)."""
    mask = x.notna() & y.notna()
    x, y = x[mask], y[mask]
    if len(x) < 10:
        return None
    slope, intercept = np.polyfit(x, y, 1)
    r = np.corrcoef(x, y)[0, 1]
    return {"slope": slope, "intercept": intercept, "r": r, "n": len(x)}

def main():
    df = pd.read_csv(INPUT_FILE, parse_dates=["date"])
    required = ["wind_speed", "humidity", "rainfall", "temp"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[ERROR] Missing columns: {missing}. "
              f"Did you re-run the updated consolidate_aqi.py first?")
        return

    df["month"] = df["date"].dt.month

    print("=== 1. Correlation: PM2.5 vs meteorology (all stations pooled) ===")
    for var in ["wind_speed", "humidity", "rainfall", "temp"]:
        res = simple_regression(df[var], df["pm25"])
        if res:
            direction = "increase" if res["slope"] > 0 else "decrease"
            print(f"  {var:12s}: r={res['r']:+.2f}, n={res['n']:5d}  "
                  f"-> each +1 unit of {var} is associated with a "
                  f"{abs(res['slope']):.2f} µg/m³ {direction} in PM2.5")

    print("\n=== 2. Per-station wind speed -> PM2.5 relationship ===")
    print("(This is the headline stat: 'each 1 m/s increase in wind speed")
    print(" is associated with an X% drop in PM2.5', per station)\n")
    station_results = []
    for station, group in df.groupby("station"):
        res = simple_regression(group["wind_speed"], group["pm25"])
        if res and group["pm25"].mean():
            pct_change_per_unit = (res["slope"] / group["pm25"].mean()) * 100
            station_results.append({
                "station": station,
                "city": group["city"].iloc[0],
                "n_days": res["n"],
                "correlation_r": round(res["r"], 2),
                "pm25_avg": round(group["pm25"].mean(), 1),
                "pct_pm25_change_per_1ms_wind": round(pct_change_per_unit, 1),
            })
    station_df = pd.DataFrame(station_results).sort_values("correlation_r")
    print(station_df.to_string(index=False))
    station_df.to_csv("wind_pm25_relationship.csv", index=False)

    print("\n=== 3. Seasonal comparison: winter vs monsoon PM2.5 ===")
    winter = df[df["month"].isin(WINTER_MONTHS)]
    monsoon = df[df["month"].isin(MONSOON_MONTHS)]
    seasonal_rows = []
    for station, group in df.groupby("station"):
        w = group[group["month"].isin(WINTER_MONTHS)]["pm25"].mean()
        m = group[group["month"].isin(MONSOON_MONTHS)]["pm25"].mean()
        if pd.notna(w) and pd.notna(m) and m > 0:
            seasonal_rows.append({
                "station": station,
                "winter_avg_pm25": round(w, 1),
                "monsoon_avg_pm25": round(m, 1),
                "pct_higher_in_winter": round((w - m) / m * 100, 1),
            })
    seasonal_df = pd.DataFrame(seasonal_rows).sort_values("pct_higher_in_winter", ascending=False)
    print(seasonal_df.to_string(index=False))
    seasonal_df.to_csv("seasonal_pm25_comparison.csv", index=False)

    print(f"\nOverall: winter avg PM2.5 = {winter['pm25'].mean():.1f} µg/m³, "
          f"monsoon avg PM2.5 = {monsoon['pm25'].mean():.1f} µg/m³ "
          f"({(winter['pm25'].mean()/monsoon['pm25'].mean()-1)*100:.0f}% higher in winter)")

    print("\nSaved: wind_pm25_relationship.csv, seasonal_pm25_comparison.csv")

if __name__ == "__main__":
    main()