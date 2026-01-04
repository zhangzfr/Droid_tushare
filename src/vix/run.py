
import argparse
import pandas as pd
from tqdm import tqdm
from .data_loader import fetch_option_data, get_shibor_interpolated
from .calculator import calculate_vix_for_date

def main():
    parser = argparse.ArgumentParser(description="Calculate VIX for Chinese Operations")
    parser.add_argument('--start_date', type=str, required=True, help='Start date YYYYMMDD')
    parser.add_argument('--end_date', type=str, required=True, help='End date YYYYMMDD')
    parser.add_argument('--underlying', type=str, default='510050.SH', help='Underlying ETF code (default 510050.SH)')
    
    args = parser.parse_args()
    
    print(f"--- Starting Chinese VIX Calculation ---")
    print(f"Period: {args.start_date} to {args.end_date}")
    
    # 1. Load Data
    print("Loading data...")
    try:
        options_all = fetch_option_data(args.start_date, args.end_date, args.underlying)
        if options_all.empty:
            print("No option data found. Exiting.")
            return

        shibor_interp = get_shibor_interpolated(args.start_date, args.end_date)
        if shibor_interp.empty:
            print("No Shibor data found. Exiting.")
            return
            
    except Exception as e:
        print(f"Data loading failed: {e}")
        return

    # 2. Iterate and Calculate
    # Unique dates
    dates = sorted(options_all['date'].unique())
    
    results = []
    
    print(f"Calculating VIX for {len(dates)} trading days...")
    
    for current_date in tqdm(dates):
        # type: current_date is pd.Timestamp from data_loader
        
        # Filter options for this date
        daily_opts = options_all[options_all['date'] == current_date]
        
        # Get Shibor rate for this date
        # shibor_interp index is date.
        try:
            daily_shibor = shibor_interp.loc[current_date]
        except KeyError:
            # print(f"Missing Shibor for {current_date.strftime('%Y-%m-%d')}, skipping.")
            continue
            
        # Calculate
        vix = calculate_vix_for_date(current_date, daily_opts, daily_shibor)
        
        if vix is not None:
            results.append({
                'date': current_date.strftime('%Y%m%d'),
                'vix': vix
            })
            
    # 3. Output
    if not results:
        print("No VIX Calculated.")
    else:
        df_result = pd.DataFrame(results)
        print("\n--- Calculation Complete ---")
        print(df_result)
        
        # Simple stats
        print("\nStatistics:")
        print(df_result['vix'].describe())
        
        # Optional: Save to file?
        output_file = f"vix_result_{args.start_date}_{args.end_date}.csv"
        df_result.to_csv(output_file, index=False)
        print(f"\nSaved results to {output_file}")

if __name__ == "__main__":
    main()
