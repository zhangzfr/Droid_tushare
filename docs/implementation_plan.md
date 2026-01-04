# Rebuild VIX Calculation for Chinese Market

## Goal Description
Rebuild the VIX calculation module in a new directory `/src/vix`, replacing the direct Tushare API calls (`/utils/VIX`) with queries to the local DuckDB instance (managed by `/src/tushare_duckdb`).

## User Review Required
- **Data Source:** confirm `shibor` table in `macro` database is populated.
- **Output:** The new module will calculate VIX. storage of the result is not currently specified, will verify by printing/checking the dataframe.

## Proposed Changes

### New Directory: `/src/vix`

#### [NEW] [data_loader.py](file:///Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/src/vix/data_loader.py)
- **Functions:**
    - `fetch_option_data(start_date, end_date)`: Connects to `OPT_DB_PATH`. Joins `opt_basic` and `opt_daily` (or fetches and merges). Filters by date.
    - `fetch_shibor_data(start_date, end_date)`: Connects to `MARCO_DB_PATH`. Fetches `shibor` table.
    - `get_shibor_interpolated(start_date, end_date)`: Fetches shibor and performs cubic interpolation to daily tenors (logic adapted from `get_tushare_data.py`).
- **Dependencies:** `pandas`, `duckdb`, `scipy.interpolate`, `src.tushare_duckdb.config`.

#### [NEW] [calculator.py](file:///Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/src/vix/calculator.py)
- **Functions:**
    - `get_vix(date, ...)`: Core VIX calculation for a single date.
    - `cal_sigma_square(...)`: Helper for variance calculation.
    - `get_near_next_term(...)`: Term selection logic.
- **Provenance:** Ported and cleaned up from `utils/VIX/calc_func.py`.

#### [NEW] [run.py](file:///Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/src/vix/run.py)
- **Logic:**
    - Define date range.
    - Call `data_loader` to get Option and Shibor data.
    - Iterate through dates to calculate VIX.
    - Output the result.

#### [NEW] [__init__.py](file:///Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/src/vix/__init__.py)
- Empty marker file.

## Verification Plan

### Automated Tests
- Create `tests/test_vix_local.py` (or inside `src/vix/test_run.py`) to run a small valid date range (e.g., 1 week).
- `python src/vix/run.py --start_date 20230101 --end_date 20230110`

### Manual Verification
- Run the script and compare output shape/content with expected logic.
