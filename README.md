# Karnataka Air Quality — NAAQS Compliance Analysis

A data pipeline and interactive dashboard analyzing 2023–2025 air quality data from 22 CPCB/KSPCB monitoring stations across Karnataka, checking daily readings against India's National Ambient Air Quality Standards (NAAQS) and examining how weather drives pollution.

**Live Dashboard -> https://dishacodes15.github.io/NAAQS-karnataka-compliance-analysis/**
## What this is

Karnataka's pollution control boards publish daily station-level air quality readings, but there's no ready-made view of *which districts breach national safety limits, how often, and why*. This project builds that view from scratch: pulling raw government data, checking it against legal thresholds, and layering in the meteorology that explains the seasonal swings.

## Key findings

- **PM10, not PM2.5, is Karnataka's dominant exceedance driver** — several stations breach the daily PM10 limit on 25–47% of monitored days, while PM2.5 breaches are comparatively rare. This points to a coarse-particulate problem (dust, construction, road surface) more than a combustion/vehicle-emissions one.
- **Winter pollution is dramatically worse than monsoon** — pooled across stations, average PM2.5 is roughly **69% higher in winter months (Nov–Feb)** than during monsoon (Jun–Sep), consistent with low wind speeds and temperature inversions trapping particulates, versus rainfall scrubbing the air.
- **Wind speed's effect varies significantly by station** — some locations show a clear, strong negative relationship between wind speed and PM2.5 (as physically expected); others show a weak or inconsistent relationship, often explained by smaller sample sizes or local dust resuspension.
- **Station coverage is uneven** — only ~9 of Karnataka's 30 districts have an active CPCB/KSPCB monitor, and even among those, data completeness varies (one station has under 15% day-coverage over the study period). This is treated as an explicit limitation throughout, not smoothed over.

## Repo structure

```
karnataka-air-quality/
├── raw_data/
│   └── raw_aqi/                    # Original CPCB CCR CSV exports, station-year files, untouched
├── scripts/
│   ├── consolidate_aqi.py          # Merges raw station CSVs into one clean daily dataset
│   ├── naaqs_compliance.py         # Computes NAAQS exceedance rates per station/pollutant/year
│   └── meteorology_analysis.py     # Wind/humidity/rainfall vs pollution relationships
├── processed_data/
│   ├── karnataka_aqi_master.csv        # Consolidated daily readings, all stations
│   ├── naaqs_compliance_summary.csv    # Per-station exceedance breakdown
│   ├── naaqs_yearly_trend.csv          # Year-over-year PM2.5 exceedance trend
│   ├── wind_pm25_relationship.csv      # Wind speed vs PM2.5 sensitivity per station
│   └── seasonal_pm25_comparison.csv    # Winter vs monsoon PM2.5 averages
└── frontend/
    └── index.html                  # Interactive dashboard (Chart.js + Leaflet)
```

## How to reproduce

1. **Data source**: raw CSVs were manually exported from CPCB's [CCR data repository](https://airquality.cpcb.gov.in) (State → City → Station → year), since CPCB doesn't currently offer historical data via public API. See `raw_data/raw_aqi/` for the exact files used.
2. **Run the pipeline**, in order:
   ```bash
   python3 scripts/consolidate_aqi.py
   python3 scripts/naaqs_compliance.py
   python3 scripts/meteorology_analysis.py
   ```
   Each script resolves its input/output paths relative to its own file location, so it works regardless of which directory you run it from.
3. **View the dashboard**: copy the four dashboard CSVs from `processed_data/` into `frontend/`, then serve locally:
   ```bash
   cd frontend
   python3 -m http.server
   ```
   Open `http://localhost:8000` — opening `index.html` directly (`file://`) won't work due to browser CORS restrictions on local file fetches.

## Methodology notes

- **NAAQS thresholds** used are the CPCB 2009 24-hour limits (PM2.5: 60 µg/m³, PM10: 100 µg/m³, NO2/SO2: 80 µg/m³, NH3: 400 µg/m³; CO and O3 use their respective 8-hour reference limits as a proxy against daily-averaged data).
- **Seasonal analysis** compares Nov–Feb ("winter") against Jun–Sep ("monsoon") averages per station — a simple but standard framing for Indian air quality seasonality.
- **Wind-speed relationship** is a single-variable linear regression per station, not a controlled multivariate model — it's a descriptive/exploratory signal, not a causal estimate. Humidity, rainfall, and wind are themselves correlated, so effects aren't fully isolated.
- One station (Hebbal 1st Stage, Mysuru) was excluded from the meteorology analysis after its data was found to be suspiciously identical to another station's readings across two independent download attempts — documented as a data-quality exclusion rather than silently dropped.

## Limitations

- Station coverage represents ~9 of Karnataka's 30 districts — findings describe *monitored* locations, not statewide air quality.
- This is a descriptive/exploratory analysis, not a validated predictive or causal model.

## Future scope

- Multivariate regression (wind + humidity + rainfall + month) to isolate individual meteorological effects
- District-level health outcome correlation (attempted via HMIS/IDSP; found to have limited public granularity for this period — see project notes)
- Diwali/festival-period and weekday/weekend pollution spike analysis
- Time-series forecasting (ARIMA/Prophet) for next-week PM2.5 prediction
- Comparison against a second state's CPCB data for policy context

## Data source

Central Pollution Control Board (CPCB), Continuous Ambient Air Quality Monitoring Station (CAAQMS) network, via the [CPCB CCR data repository](https://airquality.cpcb.gov.in).

---
Disha Madhusudana · 2026
