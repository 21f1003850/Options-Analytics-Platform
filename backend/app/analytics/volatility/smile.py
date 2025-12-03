"""Volatility Smile Analysis

The volatility smile shows the pattern of implied volatility across strikes
for a single expiration. Typically U-shaped or skewed.
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime


def calculate_volatility_smile(
    option_chain: List[Dict],
    underlying_price: float,
    expiry_days: int
) -> Dict[str, np.ndarray]:
    """
    Calculate volatility smile for a specific expiration
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current price of underlying
        expiry_days: Days to expiration to analyze
        
    Returns:
        Dictionary with smile data for calls and puts
    """
    # Filter options for the specific expiry
    filtered_calls = []
    filtered_puts = []
    
    for option in option_chain:
        expiry = option.get('expiry')
        if not expiry:
            continue
        
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        
        days = (expiry - datetime.now()).days
        
        # Match expiry (within 1 day tolerance)
        if abs(days - expiry_days) > 1:
            continue
        
        strike = option.get('strike')
        iv = option.get('implied_volatility')
        option_type = option.get('option_type', '').lower()
        
        if strike and iv and iv > 0:
            data = {
                'strike': strike,
                'iv': iv,
                'moneyness': strike / underlying_price
            }
            
            if option_type == 'call':
                filtered_calls.append(data)
            elif option_type == 'put':
                filtered_puts.append(data)
    
    # Sort by strike
    filtered_calls.sort(key=lambda x: x['strike'])
    filtered_puts.sort(key=lambda x: x['strike'])
    
    # Extract arrays
    call_strikes = np.array([opt['strike'] for opt in filtered_calls])
    call_ivs = np.array([opt['iv'] for opt in filtered_calls])
    put_strikes = np.array([opt['strike'] for opt in filtered_puts])
    put_ivs = np.array([opt['iv'] for opt in filtered_puts])
    
    # Find ATM IV (closest to underlying price)
    all_strikes = np.concatenate([call_strikes, put_strikes])
    all_ivs = np.concatenate([call_ivs, put_ivs])
    
    atm_iv = None
    if len(all_strikes) > 0:
        atm_idx = np.argmin(np.abs(all_strikes - underlying_price))
        atm_iv = all_ivs[atm_idx]
    
    # Calculate smile characteristics
    smile_metrics = _calculate_smile_metrics(
        call_strikes, call_ivs, put_strikes, put_ivs, underlying_price, atm_iv
    )
    
    return {
        "call_strikes": call_strikes,
        "call_ivs": call_ivs,
        "put_strikes": put_strikes,
        "put_ivs": put_ivs,
        "underlying_price": underlying_price,
        "atm_iv": atm_iv,
        "expiry_days": expiry_days,
        **smile_metrics
    }


def _calculate_smile_metrics(
    call_strikes: np.ndarray,
    call_ivs: np.ndarray,
    put_strikes: np.ndarray,
    put_ivs: np.ndarray,
    underlying_price: float,
    atm_iv: Optional[float]
) -> Dict[str, float]:
    """Calculate smile characteristics"""
    metrics = {}
    
    # Wing IVs (25 delta equivalents - roughly 90% and 110% moneyness)
    otm_put_threshold = underlying_price * 0.90
    otm_call_threshold = underlying_price * 1.10
    
    # OTM Put wing (left wing)
    otm_puts = [(s, iv) for s, iv in zip(put_strikes, put_ivs) if s <= otm_put_threshold]
    if otm_puts:
        metrics['put_wing_iv'] = float(np.mean([iv for _, iv in otm_puts]))
    else:
        metrics['put_wing_iv'] = None
    
    # OTM Call wing (right wing)
    otm_calls = [(s, iv) for s, iv in zip(call_strikes, call_ivs) if s >= otm_call_threshold]
    if otm_calls:
        metrics['call_wing_iv'] = float(np.mean([iv for _, iv in otm_calls]))
    else:
        metrics['call_wing_iv'] = None
    
    # Smile slope (asymmetry)
    if metrics['put_wing_iv'] and metrics['call_wing_iv'] and atm_iv:
        left_slope = metrics['put_wing_iv'] - atm_iv
        right_slope = metrics['call_wing_iv'] - atm_iv
        metrics['smile_asymmetry'] = float(left_slope - right_slope)
        metrics['smile_curvature'] = float((left_slope + right_slope) / 2)
    else:
        metrics['smile_asymmetry'] = None
        metrics['smile_curvature'] = None
    
    return metrics


def compare_smiles_across_expirations(
    option_chain: List[Dict],
    underlying_price: float,
    expiry_days_list: List[int]
) -> Dict[int, Dict]:
    """
    Compare volatility smiles across multiple expirations
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current price of underlying
        expiry_days_list: List of expiration days to compare
        
    Returns:
        Dictionary mapping expiry_days to smile data
    """
    smiles = {}
    
    for expiry_days in expiry_days_list:
        smile = calculate_volatility_smile(option_chain, underlying_price, expiry_days)
        smiles[expiry_days] = smile
    
    return smiles


def detect_smile_pattern(
    smile_data: Dict[str, np.ndarray]
) -> str:
    """
    Detect the pattern type of the volatility smile
    
    Args:
        smile_data: Output from calculate_volatility_smile
        
    Returns:
        Pattern type: 'smile', 'skew', 'smirk', 'flat', or 'unknown'
    """
    asymmetry = smile_data.get('smile_asymmetry')
    curvature = smile_data.get('smile_curvature')
    
    if asymmetry is None or curvature is None:
        return 'unknown'
    
    # Thresholds (in IV terms, e.g., 0.05 = 5% IV)
    ASYMMETRY_THRESHOLD = 0.05
    CURVATURE_THRESHOLD = 0.03
    
    if abs(curvature) < CURVATURE_THRESHOLD:
        return 'flat'
    
    if curvature > CURVATURE_THRESHOLD:
        if abs(asymmetry) < ASYMMETRY_THRESHOLD:
            return 'smile'  # Symmetric U-shape
        elif asymmetry > ASYMMETRY_THRESHOLD:
            return 'skew'  # Left wing higher (put skew)
        else:
            return 'smirk'  # Right wing higher (call skew)
    
    return 'unknown'
