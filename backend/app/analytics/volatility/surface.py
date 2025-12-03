"""3D Volatility Surface Generation

Creates a 3D surface of implied volatility across strikes and expirations.
"""

import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime


def generate_volatility_surface(
    option_chain: List[Dict],
    underlying_price: float
) -> Dict[str, np.ndarray]:
    """
    Generate 3D volatility surface from option chain data
    
    Args:
        option_chain: List of option contracts with IV, strike, expiry
        underlying_price: Current price of underlying
        
    Returns:
        Dictionary with:
        - strikes: array of strike prices
        - expiries: array of days to expiration
        - iv_surface: 2D array of implied volatilities
        - moneyness: array of moneyness ratios (strike/spot)
    """
    if not option_chain:
        return {
            "strikes": np.array([]),
            "expiries": np.array([]),
            "iv_surface": np.array([[]]),
            "moneyness": np.array([])
        }
    
    # Group by expiry
    expiry_groups = {}
    for option in option_chain:
        expiry = option.get('expiry')
        if expiry is None:
            continue
        
        # Convert to datetime if string
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        
        # Calculate days to expiry
        days_to_expiry = (expiry - datetime.now()).days
        
        if days_to_expiry <= 0:
            continue
        
        if days_to_expiry not in expiry_groups:
            expiry_groups[days_to_expiry] = []
        
        strike = option.get('strike')
        iv = option.get('implied_volatility')
        
        if strike and iv and iv > 0:
            expiry_groups[days_to_expiry].append({
                'strike': strike,
                'iv': iv
            })
    
    if not expiry_groups:
        return {
            "strikes": np.array([]),
            "expiries": np.array([]),
            "iv_surface": np.array([[]]),
            "moneyness": np.array([])
        }
    
    # Get unique sorted expiries and strikes
    expiries = sorted(expiry_groups.keys())
    all_strikes = set()
    for options in expiry_groups.values():
        all_strikes.update(opt['strike'] for opt in options)
    strikes = sorted(all_strikes)
    
    # Create surface grid
    iv_surface = np.full((len(expiries), len(strikes)), np.nan)
    
    for i, expiry in enumerate(expiries):
        options = expiry_groups[expiry]
        strike_iv_map = {opt['strike']: opt['iv'] for opt in options}
        
        for j, strike in enumerate(strikes):
            if strike in strike_iv_map:
                iv_surface[i, j] = strike_iv_map[strike]
    
    # Interpolate missing values
    from scipy.interpolate import griddata
    
    # Get valid points
    valid_mask = ~np.isnan(iv_surface)
    if valid_mask.sum() > 3:  # Need at least 3 points for interpolation
        valid_points = np.argwhere(valid_mask)
        valid_values = iv_surface[valid_mask]
        
        # Create all grid points
        all_points = np.array([[i, j] for i in range(len(expiries)) for j in range(len(strikes))])
        
        # Interpolate
        interpolated = griddata(
            valid_points,
            valid_values,
            all_points,
            method='linear',
            fill_value=np.nan
        )
        
        iv_surface = interpolated.reshape(len(expiries), len(strikes))
    
    # Calculate moneyness
    moneyness = np.array(strikes) / underlying_price
    
    return {
        "strikes": np.array(strikes),
        "expiries": np.array(expiries),
        "iv_surface": iv_surface,
        "moneyness": moneyness
    }


def extract_surface_slice(
    surface_data: Dict[str, np.ndarray],
    expiry_days: int = None,
    strike: float = None
) -> Dict[str, np.ndarray]:
    """
    Extract a slice of the volatility surface
    
    Args:
        surface_data: Output from generate_volatility_surface
        expiry_days: If provided, extract volatility smile at this expiry
        strike: If provided, extract term structure at this strike
        
    Returns:
        Dictionary with slice data
    """
    strikes = surface_data['strikes']
    expiries = surface_data['expiries']
    iv_surface = surface_data['iv_surface']
    
    if expiry_days is not None:
        # Find closest expiry
        idx = np.argmin(np.abs(expiries - expiry_days))
        return {
            "strikes": strikes,
            "iv": iv_surface[idx, :],
            "expiry_days": expiries[idx]
        }
    
    if strike is not None:
        # Find closest strike
        idx = np.argmin(np.abs(strikes - strike))
        return {
            "expiries": expiries,
            "iv": iv_surface[:, idx],
            "strike": strikes[idx]
        }
    
    return {}


def calculate_surface_metrics(
    surface_data: Dict[str, np.ndarray]
) -> Dict[str, float]:
    """
    Calculate summary metrics for the volatility surface
    
    Args:
        surface_data: Output from generate_volatility_surface
        
    Returns:
        Dictionary with metrics like avg_iv, iv_std, skew, etc.
    """
    iv_surface = surface_data['iv_surface']
    valid_ivs = iv_surface[~np.isnan(iv_surface)]
    
    if len(valid_ivs) == 0:
        return {}
    
    return {
        "avg_iv": float(np.mean(valid_ivs)),
        "min_iv": float(np.min(valid_ivs)),
        "max_iv": float(np.max(valid_ivs)),
        "iv_std": float(np.std(valid_ivs)),
        "iv_range": float(np.max(valid_ivs) - np.min(valid_ivs))
    }
