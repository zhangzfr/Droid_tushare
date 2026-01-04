# VIX Calculation Rebuild Walkthrough

I have rebuilt the VIX calculation module in `/src/vix` to use the local DuckDB data source instead of direct Tushare API calls. This ensures the calculation runs offline and leverages the local data infrastructure.

## Improvements
- **Local Data Source**: Uses `src.vix.config` to locate DuckDB files based on `settings.yaml`.
- **Dependency Free**: Removed dependencies on `tushare` (using raw SQL) and `scipy` (replaced with `numpy` interpolation) to ensure stability across environments.
- **Filtering**: Added strict filtering for `50ETF` options on `SSE` to ensure correct VIX calculation inputs.
- **Refactored Logic**: Cleaned up calculation logic in `calculator.py` into a cohesive module.

## Files Created
- [data_loader.py](file:///Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/src/vix/data_loader.py): Handles data fetching from DuckDB and Shibor interpolation.
- [calculator.py](file:///Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/src/vix/calculator.py): Contains the core VIX math (Sigma, Forward Price, etc.).
- [run.py](file:///Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/src/vix/run.py): CLI entry point.
- [config.py](file:///Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/src/vix/config.py): Local configuration loader.

## Usage

Run the module as a script from the project root:

```bash
python -m src.vix.run --start_date 20230101 --end_date 20230110
```

### Output Example
```text
--- Starting Chinese VIX Calculation ---
Period: 20230101 to 20230110
Loading data...
Connecting to Option DB at .../tushare_duck_opt.db...
Interpolating Shibor data...
Calculating VIX for 6 trading days...
100%|██████████| 6/6 [00:00<00:00, 250.04it/s]

--- Calculation Complete ---
       date        vix  near_term  next_term  ...  weighted_variance
0  20230103  16.910842   0.073973   0.136986  ...           0.002350
1  20230104  16.742240   0.071233   0.134247  ...           0.002304
...
```

The output `data/vix_result_YYYYMMDD_YYYYMMDD.csv` now contains detailed intermediate results for traceability, including forward prices (F), strike cutoffs (K0), and term variances (sigma_sq).
