"""Volatility Skew Analysis

Analyzes the relationship between strike price (or delta) and implied volatility.
The skew typically shows puts trading at higher IV than calls (put skew).
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime


def calculate_volatility_skew(
    option_chain: List[Dict],
    underlying_price: float,
    expiry_days: Optional[int] = None,
    by_delta: bool = False
) -> Dict[str, np.ndarray]:
    """
    Calculate volatility skew by strike or delta
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current price of underlying
        expiry_days: Optional filter for specific expiry (closest match)
        by_delta: If True, plot by delta instead of strike
        
    Returns:
        Dictionary with skew data
    """
    # Filter options
    filtered_options = []
    
    for option in option_chain:
        expiry = option.get('expiry')
        if not expiry:
            continue
        
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        
        days = (expiry - datetime.now()).days
        
        # Filter by expiry if specified
        if expiry_days is not None:
            if abs(days - expiry_days) > 3:  # Within 3 days tolerance
                continue
        
        strike = option.get('strike')
        iv = option.get('implied_volatility')
        delta = option.get('delta')
        option_type = option.get('option_type', '').lower()
        
        if strike and iv and iv > 0:
            filtered_options.append({
                'strike': strike,
                'iv': iv,
                'delta': delta if delta else 0,
                'moneyness': strike / underlying_price,
                'option_type': option_type,
                'days_to_expiry': days
            })
    
    if not filtered_options:
        return {
            "x_axis": np.array([]),
            "iv": np.array([]),
            "skew_measure": 0.0,
            "axis_type": "delta" if by_delta else "strike"
        }
    
    # Sort by delta or strike
    if by_delta:
        # Separate calls and puts
        calls = [opt for opt in filtered_options if opt['option_type'] == 'call' and opt['delta'] > 0]
        puts = [opt for opt in filtered_options if opt['option_type'] == 'put' and opt['delta'] < 0]
        
        # Sort calls by delta (ascending)
        calls.sort(key=lambda x: x['delta'])
        # Sort puts by delta (descending, so -1.0 to 0)
        puts.sort(key=lambda x: x['delta'])
        
        # Combine
        sorted_options = puts + calls
        x_axis = np.array([opt['delta'] for opt in sorted_options])
        iv_values = np.array([opt['iv'] for opt in sorted_options])
    else:
        # Sort by strike
        sorted_options = sorted(filtered_options, key=lambda x: x['strike'])
        x_axis = np.array([opt['strike'] for opt in sorted_options])
        iv_values = np.array([opt['iv'] for opt in sorted_options])
    
    # Calculate skew measure (90% - 110% moneyness IV difference)
    otm_puts = [opt for opt in filtered_options if 0.85 <= opt['moneyness'] <= 0.95]
    otm_calls = [opt for opt in filtered_options if 1.05 <= opt['moneyness'] <= 1.15]
    
    skew_measure = 0.0
    if otm_puts and otm_calls:
        avg_put_iv = np.mean([opt['iv'] for opt in otm_puts])
        avg_call_iv = np.mean([opt['iv'] for opt in otm_calls])
        skew_measure = avg_put_iv - avg_call_iv
    
    return {
        "x_axis": x_axis,
        "iv": iv_values,
        "skew_measure": float(skew_measure),
        "axis_type": "delta" if by_delta else "strike",
        "underlying_price": underlying_price,
        "option_count": len(sorted_options)
    }


def calculate_skew_by_moneyness(
    option_chain: List[Dict],
    underlying_price: float,
    expiry_days: Optional[int] = None
) -> Dict[str, np.ndarray]:
    """
    Calculate volatility skew by moneyness (strike/spot ratio)
    
    This normalizes strikes across different underlying prices.
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current price of underlying
        expiry_days: Optional filter for specific expiry
        
    Returns:
        Dictionary with moneyness skew data
    """
    filtered_options = []
    
    for option in option_chain:
        expiry = option.get('expiry')
        if not expiry:
            continue
        
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        
        days = (expiry - datetime.now()).days
        
        if expiry_days is not None and abs(days - expiry_days) > 3:
            continue
        
        strike = option.get('strike')
        iv = option.get('implied_volatility')
        
        if strike and iv and iv > 0:
            moneyness = strike / underlying_price
            filtered_options.append({
                'moneyness': moneyness,
                'iv': iv
            })
    
    if not filtered_options:
        return {
            "moneyness": np.array([]),
            "iv": np.array([])
        }
    
    # Sort by moneyness
    sorted_options = sorted(filtered_options, key=lambda x: x['moneyness'])
    
    moneyness = np.array([opt['moneyness'] for opt in sorted_options])
    iv_values = np.array([opt['iv'] for opt in sorted_options])
    
    return {
        "moneyness": moneyness,
        "iv": iv_values
    }


def fit_skew_model(
    skew_data: Dict[str, np.ndarray],
    model: str = "polynomial"
) -> Dict:
    """
    Fit a model to the volatility skew
    
    Args:
        skew_data: Output from calculate_volatility_skew
        model: 'polynomial' or 'spline'
        
    Returns:
        Dictionary with fitted parameters and predictions
    """
    x = skew_data['x_axis']
    y = skew_data['iv']
    
    if len(x) < 3:
        return {"fitted": False}
    
    if model == "polynomial":
        # Fit 2nd degree polynomial
        coeffs = np.polyfit(x, y, 2)
        poly = np.poly1d(coeffs)
        
        x_fit = np.linspace(x.min(), x.max(), 100)
        y_fit = poly(x_fit)
        
        return {
            "fitted": True,
            "model": "polynomial",
            "coefficients": coeffs.tolist(),
            "x_fit": x_fit,
            "y_fit": y_fit
        }
    
    elif model == "spline":
        from scipy.interpolate import UnivariateSpline
        
        # Fit cubic spline
        spline = UnivariateSpline(x, y, k=3, s=0.01)
        
        x_fit = np.linspace(x.min(), x.max(), 100)
        y_fit = spline(x_fit)
        
        return {
            "fitted": True,
            "model": "spline",
            "x_fit": x_fit,
            "y_fit": y_fit
        }
    
    return {"fitted": False}
