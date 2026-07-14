"""
Consolidates all raw CPCB CCR CSV downloads (one file per station per year,
with browser (1)/(2) duplicate suffixes) into a single tidy master CSV.

Expects filenames like:
    raw_data_data_thimmalapura,_tumakuru_-_kspcb_1D.csv
    raw_data_data_thimmalapura,_tumakuru_-_kspcb_1D (2).csv

Usage:
    pip install pandas
    python consolidate_aqi.py

Edit RAW_FOLDER below to point at wherever you moved the downloaded CSVs.
"""

import pandas as pd
import re
from pathlib import Path

RAW_FOLDER = "../raw_data/raw_aqi"          # <-- change this to your actual folder path
OUTPUT_FILE = "../processed_data/karnataka_aqi_master.csv"

# Map the messy CPCB column headers to clean, consistent names.
# Add/remove entries here if your file has slightly different header text.
COLUMN_MAP = {
    "Timestamp": "date",
    "PM2.5 (µg/m³)": "pm25",
    "PM10 (µg/m³)": "pm10",
    "NO2 (µg/m³)": "no2",
    "SO2 (µg/m³)": "so2",
    "CO (mg/m³)": "co",
    "Ozone (µg/m³)": "o3",
    "NH3 (µg/m³)": "nh3",
    "AT (°C)": "temp",
    "RH (%)": "humidity",
    "WS (m/s)": "wind_speed",
    "WD (deg)": "wind_dir",
    "RF (mm)": "rainfall",
}

def parse_filename(fname: str):
    """Extract station and city from a CPCB CCR export filename."""
    stem = Path(fname).stem
    stem = re.sub(r"\s\(\d+\)$", "", stem)          # strip browser " (1)", " (2)" suffix
    stem = stem.replace("raw_data_data_", "")
    match = re.match(r"(.+?)_-_(\w+)_1D", stem)
    if not match:
        return None, None, None
    left, provider = match.group(1), match.group(2)
    parts = left.split(",_")
    if len(parts) != 2:
        return None, None, None
    station = parts[0].replace("_", " ").strip()
    city = parts[1].replace("_", " ").strip()
    return station, city, provider

def load_one_file(path: Path):
    try:
        df = pd.read_csv(path)
    except Exception as e:
        print(f"  [skip] Could not read {path.name}: {e}")
        return None

    rename_map = {c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP}
    if "Timestamp" not in df.columns:
        print(f"  [warn] {path.name} has no Timestamp column — skipping.")
        return None

    df = df.rename(columns=rename_map)
    keep_cols = ["date"] + [v for v in COLUMN_MAP.values() if v in df.columns and v != "date"]
    df = df[keep_cols]

    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%y", errors="coerce")

    # Fallback: if that format didn't work for most rows, try a couple of
    # other common CPCB export formats before giving up.
    if df["date"].isna().mean() > 0.5:
        raw = pd.read_csv(path, usecols=["Timestamp"])["Timestamp"]
        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%d-%m-%y", "%Y-%m-%d"]:
            parsed = pd.to_datetime(raw, format=fmt, errors="coerce")
            if parsed.isna().mean() < 0.5:
                df["date"] = parsed
                break
        else:
            # last resort: let pandas infer, dayfirst since this is Indian data
            df["date"] = pd.to_datetime(raw, dayfirst=True, errors="coerce")

    if df["date"].isna().mean() > 0.1:
        print(f"  [warn] {path.name}: {df['date'].isna().mean():.0%} of dates failed to parse. "
              f"Sample raw values: {pd.read_csv(path, usecols=['Timestamp'])['Timestamp'].head(3).tolist()}")

    station, city, provider = parse_filename(path.name)
    df["station"] = station
    df["city"] = city
    df["provider"] = provider

    return df

def main():
    folder = Path(RAW_FOLDER)
    csv_files = list(folder.glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files in {folder.resolve()}\n")

    all_dfs = []
    for f in csv_files:
        try:
            df = load_one_file(f)
        except Exception as e:
            print(f"  [ERROR] {f.name} raised an exception: {e}")
            continue

        if df is None:
            continue
        if len(df) == 0:
            print(f"  [warn] {f.name} loaded but has 0 rows after processing — skipping. "
                  f"Raw columns were: {pd.read_csv(f, nrows=0).columns.tolist()}")
            continue

        all_dfs.append(df)
        print(f"  Loaded {f.name}: {len(df)} rows, station={df['station'].iloc[0]}, city={df['city'].iloc[0]}")

    if not all_dfs:
        print("\nNo valid data loaded — check RAW_FOLDER path and filenames.")
        return

    master = pd.concat(all_dfs, ignore_index=True)

    before = len(master)
    master = master.drop_duplicates(subset=["station", "city", "date"], keep="first")
    print(f"\nDropped {before - len(master)} duplicate rows.")

    master = master.sort_values(["city", "station", "date"]).reset_index(drop=True)
    master.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved {len(master)} rows across {master['station'].nunique()} stations to {OUTPUT_FILE}")
    print("\nDate range per station:")
    print(master.groupby("station")["date"].agg(["min", "max", "count"]))
    EXCLUDED_STATIONS = {"hebbal 1st stage"}

if __name__ == "__main__":
    main()