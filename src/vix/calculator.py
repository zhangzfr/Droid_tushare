
import numpy as np
import pandas as pd
import warnings
from typing import Dict, Tuple, Optional

# Constants
YEARS = 365.0

def calculate_vix_for_date(date: pd.Timestamp, 
                           daily_options: pd.DataFrame, 
                           shibor_interpolated: pd.Series) -> Optional[float]:
    """
    Calculates VIX for a specific date.
    
    Args:
        date: The calculation date.
        daily_options: DataFrame of options for this date. 
                       Columns: [date, exercise_date, close, contract_type, exercise_price, maturity]
        shibor_interpolated: Series of interpolated Shibor rates for this date.
                             Index is days (1 to 365), values are rates (decimals).
                             
    Returns:
        float: The VIX value (e.g., 20.5 for 20.5%), or None if calculation fails.
    """
    if daily_options.empty:
        return None
        
    # 1. Select Near and Next Term Expirations
    # Filter maturities >= 7 days
    valid_options = daily_options[daily_options['maturity'] >= (7.0 / YEARS)]
    
    if valid_options.empty:
        # Fallback logic? Original code filters >= 7 days.
        # If no options >= 7 days, maybe look at all? But VIX standard usually requires > 1 week.
        return None
        
    maturities = np.sort(valid_options['maturity'].unique())
    # print(f"DEBUG {date}: Options={len(daily_options)}, Valid={len(valid_options)}, Maturities={len(maturities)}")
    if len(maturities) < 2:
        return None
        
    near_term = maturities[0]
    next_term = maturities[1]
    
    # 2. Get Risk Free Rates for these terms
    try:
        r_near = _get_risk_free_rate(shibor_interpolated, near_term)
        r_next = _get_risk_free_rate(shibor_interpolated, next_term)
    except Exception as e:
        print(f"Error getting risk free rate for {date}: {e}")
        return None
        
    # 3. Calculate Sigma Squares
    try:
        sigma_sq_near = _calculate_sigma_square(valid_options, near_term, r_near)
        sigma_sq_next = _calculate_sigma_square(valid_options, next_term, r_next)
    except Exception as e:
        print(f"Error calculating sigma for {date}: {e}")
        return None
        
    # 4. Calculate VIX
    # Formula: VIX = 100 * sqrt( (T1*sigma1^2 * [(T2-T30)/(T2-T1)] + T2*sigma2^2 * [(T30-T1)/(T2-T1)]) * (365/30) )
    # But wait, original code `calc_vix` formula:
    # weight = (t2 - t30) / (t2 - t1)
    # sqrt( (near_term * near_sigma * weight + next_term * next_sigma * (1 - weight)) * (YEARS / 30) )
    # Wait, the original code `calc_sigma` calculates `sigma` but implementation seems to return something that is already processed?
    # Original `calc_sigma` returns a float. Let's look at it.
    # return (2 / T) * sum(...) - (1 / T) * ...
    # This looks like sigma squared? Or variance?
    # Standard VIX whitepaper: sigma^2 = (2/T) sum(...) - (1/T)[F/K0 - 1]^2
    # So `calc_sigma` actually returns sigma^2 (variance).
    
    # Let's verify original code `calc_vix`:
    # np.sqrt((near_term * near_sigma * weight + next_term * next_sigma * (1 - weight)) * (YEARS / 30))
    # If `near_sigma` is variance, then `near_term * variance` is time-weighted variance.
    # The formula looks correct for VIX if inputs are variances.
    
    t30 = 30.0 / YEARS
    weight = (next_term - t30) / (next_term - near_term)
    
    # Weighted variance
    # Note: original code calculates `sigma` but passed it as `near_sigma`.
    # I'll assume it returns variance.
    
    weighted_variance = (near_term * sigma_sq_near * weight + 
                         next_term * sigma_sq_next * (1.0 - weight))
    
    if weighted_variance < 0:
        # Should not happen theoretically unless messy data
        return None
        
    vix = 100.0 * np.sqrt(weighted_variance * (YEARS / 30.0))
    return vix


def _get_risk_free_rate(shibor_ser: pd.Series, term_years: float) -> float:
    """Gets the risk free rate from interpolated series."""
    days = max(1, int(round(term_years * YEARS)))
    # shibor_ser index is integer days (1 to 365)
    # Use reindex/get to handle out of bounds safely?
    # If days > 365, use 365 (flat curve assumption at end) or last available
    if days > shibor_ser.index.max():
        return shibor_ser.iloc[-1]
    if days < shibor_ser.index.min():
        return shibor_ser.iloc[0]
        
    try:
        rate = shibor_ser.loc[days]
        if pd.isna(rate):
             # fallback to nearest? interpolated series shouldn't have NaNs if properly filled
             return 0.03 # Default fallback?
        return rate
    except KeyError:
        return 0.03

def _calculate_sigma_square(options: pd.DataFrame, term: float, r: float) -> float:
    """Calculates the variance (sigma^2) for a specific term."""
    # Filter for this term
    # Note: 'maturity' is float years. Exact match might be float sensitive. 
    # Use a small epsilon or rely on exact values if they come from same source.
    # The `maturities` array came from unique(), so filtering by it should work.
    term_options = options[np.isclose(options['maturity'], term)].copy()
    
    if term_options.empty:
        raise ValueError(f"No options for term {term}")
        
    # Pivot to get calls and puts side by side
    # Pivot on exercise_price
    # Check duplicates?
    term_options = term_options.drop_duplicates(subset=['exercise_price', 'contract_type'])
    
    strike_matrix = term_options.pivot(index='exercise_price', columns='contract_type', values='close')
    # Columns: 'call', 'put'
    if 'call' not in strike_matrix.columns or 'put' not in strike_matrix.columns:
        # maybe only calls or only puts exist?
        raise ValueError("Missing call or put columns")
        
    strike_matrix.sort_index(inplace=True)
    
    # Calculate Diff (delta_K)
    # delta_K_i = (K_{i+1} - K_{i-1}) / 2
    # Ends: K_second - K_first, ...
    
    strikes = strike_matrix.index.values
    if len(strikes) < 3:
        # Need at least a few strikes
        # Maybe handle?
        pass
        
    diff = np.zeros(len(strikes))
    if len(strikes) > 1:
        diff[0] = strikes[1] - strikes[0]
        diff[-1] = strikes[-1] - strikes[-2]
        diff[1:-1] = (strikes[2:] - strikes[0:-2]) / 2.0
    else:
        diff[0] = 0.0 # Should not happen with < 2 check logic potentially
        
    strike_matrix['diff'] = diff
    
    # Determine F (Forward Price)
    # Find strike where abs(Call - Put) is smallest
    abs_diff = np.abs(strike_matrix['call'] - strike_matrix['put'])
    min_diff_k = abs_diff.idxmin()
    min_row = strike_matrix.loc[min_diff_k]
    
    # F = Strike + e^RT * (Call - Put)
    F = min_diff_k + np.exp(r * term) * (min_row['call'] - min_row['put'])
    
    # Determine K0: The strike immediately below F
    # If F < lowest strike, K0 is lowest strike.
    below_F = strikes[strikes < F]
    if len(below_F) > 0:
        K0 = below_F.max()
    else:
        K0 = strikes.min()
        
    # Select Options for Calculation (Q(K))
    # Out-of-the-money options:
    # If K < K0: Put
    # If K > K0: Call
    # If K == K0: Average of Call and Put
    
    def get_Q(row):
        K = row.name
        if K < K0:
            return row['put']
        elif K > K0:
            return row['call']
        else:
            return (row['call'] + row['put']) / 2.0
            
    Q_K = strike_matrix.apply(get_Q, axis=1)
    
    # Calculate Contribution ~ (delta_K / K^2) * e^RT * Q(K)
    # Sigma^2 = (2/T) * sum(...) - (1/T) * (F/K0 - 1)^2
    
    contribution = (strike_matrix['diff'] / (strikes ** 2)) * np.exp(r * term) * Q_K
    sum_contribution = contribution.sum()
    
    term1 = (2.0 / term) * sum_contribution
    term2 = (1.0 / term) * ((F / K0 - 1.0) ** 2)
    
    sigma_sq = term1 - term2
    return sigma_sq

