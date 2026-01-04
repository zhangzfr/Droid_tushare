
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
    all_details = []
    
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
        result_dict = calculate_vix_for_date(current_date, daily_opts, daily_shibor)
        
        if result_dict is not None:
            # Extract details
            details_df = result_dict.pop('details')
            
            # Summary Record
            result_record = {'date': current_date.strftime('%Y%m%d')}
            result_record.update(result_dict)
            results.append(result_record)
            
            # Details Record (add to list, concat later)
            all_details.append(details_df)
            
    # 3. Output
    if not results:
        print("No VIX Calculated.")
    else:
        df_result = pd.DataFrame(results)
        print("\n--- Summary Result ---")
        print(df_result.head())
        
        # Save Summary
        import os
        os.makedirs('data', exist_ok=True)
        summary_file = f"data/vix_result_{args.start_date}_{args.end_date}.csv"
        df_result.to_csv(summary_file, index=False)
        print(f"Saved summary to {summary_file}")
        
        # Save Details
        if all_details:
            df_details = pd.concat(all_details)
            
            # Split into Near and Next for clarity/file size
            df_near = df_details[df_details['term_type'] == 'near']
            df_next = df_details[df_details['term_type'] == 'next']
            
            near_file = f"data/vix_details_near_{args.start_date}_{args.end_date}.csv"
            next_file = f"data/vix_details_next_{args.start_date}_{args.end_date}.csv"
            
            df_near.to_csv(near_file, index=False)
            df_next.to_csv(next_file, index=False)
            print(f"Saved details to:\n  - {near_file}\n  - {next_file}")

if __name__ == "__main__":
    main()
