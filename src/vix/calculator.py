
import numpy as np
import pandas as pd
import warnings
from typing import Dict, Tuple, Optional

# Constants
YEARS = 365.0

def calculate_vix_for_date(date: pd.Timestamp, 
                           daily_options: pd.DataFrame, 
                           shibor_interpolated: pd.Series) -> Optional[Dict]:
    """
    Calculates VIX for a specific date and returns detailed intermediate results.
    
    Returns:
        Dict: VIX and intermediate values, or None if calculation fails.
    """
    if daily_options.empty:
        return None
        
    # 1. Select Near and Next Term Expirations
    valid_options = daily_options[daily_options['maturity'] >= (7.0 / YEARS)]
    
    if valid_options.empty:
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
        sigma_sq_near, F_near, K0_near, details_near = _calculate_sigma_square(valid_options, near_term, r_near)
        sigma_sq_next, F_next, K0_next, details_next = _calculate_sigma_square(valid_options, next_term, r_next)
        
        # Add labels to details
        details_near['term_type'] = 'near'
        details_near['term_maturity'] = near_term
        details_next['term_type'] = 'next'
        details_next['term_maturity'] = next_term
        
        details_df = pd.concat([details_near, details_next])
        details_df['date'] = date
        
    except Exception as e:
        print(f"Error calculating sigma for {date}: {e}")
        return None
        
    # 4. Calculate VIX
    t30 = 30.0 / YEARS
    weight = (next_term - t30) / (next_term - near_term)
    
    weighted_variance = (near_term * sigma_sq_near * weight + 
                         next_term * sigma_sq_next * (1.0 - weight))
    
    if weighted_variance < 0:
        return None
        
    vix = 100.0 * np.sqrt(weighted_variance * (YEARS / 30.0))
    
    return {
        'vix': vix,
        'near_term': near_term,
        'next_term': next_term,
        'r_near': r_near,
        'r_next': r_next,
        'sigma_sq_near': sigma_sq_near,
        'sigma_sq_next': sigma_sq_next,
        'F_near': F_near,
        'F_next': F_next,
        'K0_near': K0_near,
        'K0_next': K0_next,
        'weight': weight,
        'weighted_variance': weighted_variance,
        'details': details_df
    }


def _get_risk_free_rate(shibor_ser: pd.Series, term_years: float) -> float:
    """Gets the risk free rate from interpolated series."""
    days = max(1, int(round(term_years * YEARS)))
    if days > shibor_ser.index.max():
        return shibor_ser.iloc[-1]
    if days < shibor_ser.index.min():
        return shibor_ser.iloc[0]
        
    try:
        rate = shibor_ser.loc[days]
        if pd.isna(rate):
             return 0.03 # Default fallback
        return rate
    except KeyError:
        return 0.03

def _calculate_sigma_square(options: pd.DataFrame, term: float, r: float) -> Tuple[float, float, float, pd.DataFrame]:
    """Calculates the variance (sigma^2) for a specific term."""
    term_options = options[np.isclose(options['maturity'], term)].copy()
    
    if term_options.empty:
        raise ValueError(f"No options for term {term}")
        
    term_options = term_options.drop_duplicates(subset=['exercise_price', 'contract_type'])
    strike_matrix = term_options.pivot(index='exercise_price', columns='contract_type', values='close')
    
    if 'call' not in strike_matrix.columns or 'put' not in strike_matrix.columns:
        raise ValueError("Missing call or put columns")
        
    strike_matrix.sort_index(inplace=True)
    
    # Calculate Diff (delta_K)
    strikes = strike_matrix.index.values
    diff = np.zeros(len(strikes))
    if len(strikes) > 1:
        diff[0] = strikes[1] - strikes[0]
        diff[-1] = strikes[-1] - strikes[-2]
        diff[1:-1] = (strikes[2:] - strikes[0:-2]) / 2.0
    else:
        diff[0] = 0.0
        
    strike_matrix['diff'] = diff
    
    # Determine F (Forward Price)
    abs_diff = np.abs(strike_matrix['call'] - strike_matrix['put'])
    min_diff_k = abs_diff.idxmin()
    min_row = strike_matrix.loc[min_diff_k]
    
    F = min_diff_k + np.exp(r * term) * (min_row['call'] - min_row['put'])
    
    # Determine K0
    below_F = strikes[strikes < F]
    if len(below_F) > 0:
        K0 = below_F.max()
    else:
        K0 = strikes.min()
        
    # Select Options for Calculation (Q(K))
    def get_Q(row):
        K = row.name
        if K < K0:
            return row['put']
        elif K > K0:
            return row['call']
        else:
            return (row['call'] + row['put']) / 2.0
            
    Q_K = strike_matrix.apply(get_Q, axis=1)
    
    contribution = (strike_matrix['diff'] / (strikes ** 2)) * np.exp(r * term) * Q_K
    sum_contribution = contribution.sum()
    
    term1 = (2.0 / term) * sum_contribution
    term2 = (1.0 / term) * ((F / K0 - 1.0) ** 2)
    
    sigma_sq = term1 - term2
    
    # Prepare Detail DataFrame
    # Enrich strike_matrix with info
    strike_matrix['Q_K'] = Q_K
    strike_matrix['contribution'] = contribution
    strike_matrix['F'] = F
    strike_matrix['K0'] = K0
    strike_matrix['risk_free_rate'] = r
    strike_matrix['maturity'] = term
    strike_matrix.reset_index(inplace=True) # make exercise_price a column
    
    return sigma_sq, F, K0, strike_matrix

