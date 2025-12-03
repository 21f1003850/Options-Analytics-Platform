"""Implied Volatility Term Structure

Analyzes how IV changes across different expiration dates.
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime


def calculate_iv_term_structure(
    option_chain: List[Dict],
    underlying_price: float,
    moneyness_target: float = 1.0
) -> Dict[str, np.ndarray]:
    """
    Calculate IV term structure (IV across expirations)
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current price of underlying
        moneyness_target: Target moneyness (1.0 = ATM, 0.95 = 5% OTM put, etc.)
        
    Returns:
        Dictionary with term structure data
    """
    # Group by expiry
    expiry_data = {}
    
    for option in option_chain:
        expiry = option.get('expiry')
        if not expiry:
            continue
        
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        
        days = (expiry - datetime.now()).days
        if days <= 0:
            continue
        
        strike = option.get('strike')
        iv = option.get('implied_volatility')
        
        if not strike or not iv or iv <= 0:
            continue
        
        moneyness = strike / underlying_price
        
        if days not in expiry_data:
            expiry_data[days] = []
        
        expiry_data[days].append({
            'strike': strike,
            'moneyness': moneyness,
            'iv': iv
        })
    
    # For each expiry, find IV at target moneyness
    term_structure = []
    
    for days in sorted(expiry_data.keys()):
        options = expiry_data[days]
        
        # Find closest to target moneyness
        closest_option = min(
            options,
            key=lambda x: abs(x['moneyness'] - moneyness_target)
        )
        
        # Only include if reasonably close to target
        if abs(closest_option['moneyness'] - moneyness_target) < 0.1:
            term_structure.append({
                'days_to_expiry': days,
                'iv': closest_option['iv'],
                'strike': closest_option['strike'],
                'moneyness': closest_option['moneyness']
            })
    
    if not term_structure:
        return {
            "days_to_expiry": np.array([]),
            "iv": np.array([]),
            "strikes": np.array([])
        }
    
    days_array = np.array([item['days_to_expiry'] for item in term_structure])
    iv_array = np.array([item['iv'] for item in term_structure])
    strikes_array = np.array([item['strike'] for item in term_structure])
    
    return {
        "days_to_expiry": days_array,
        "iv": iv_array,
        "strikes": strikes_array,
        "moneyness_target": moneyness_target
    }


def calculate_term_structure_by_delta(
    option_chain: List[Dict],
    target_delta: float = 0.5
) -> Dict[str, np.ndarray]:
    """
    Calculate IV term structure by delta instead of moneyness
    
    Args:
        option_chain: List of option contracts
        target_delta: Target delta (0.5 = ATM, 0.25 = 25-delta call, etc.)
        
    Returns:
        Dictionary with term structure data
    """
    expiry_data = {}
    
    for option in option_chain:
        expiry = option.get('expiry')
        delta = option.get('delta')
        iv = option.get('implied_volatility')
        
        if not expiry or not delta or not iv or iv <= 0:
            continue
        
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        
        days = (expiry - datetime.now()).days
        if days <= 0:
            continue
        
        if days not in expiry_data:
            expiry_data[days] = []
        
        expiry_data[days].append({
            'delta': delta,
            'iv': iv
        })
    
    term_structure = []
    
    for days in sorted(expiry_data.keys()):
        options = expiry_data[days]
        
        # Find closest to target delta
        closest_option = min(
            options,
            key=lambda x: abs(x['delta'] - target_delta)
        )
        
        if abs(closest_option['delta'] - target_delta) < 0.15:
            term_structure.append({
                'days_to_expiry': days,
                'iv': closest_option['iv'],
                'delta': closest_option['delta']
            })
    
    if not term_structure:
        return {
            "days_to_expiry": np.array([]),
            "iv": np.array([])
        }
    
    return {
        "days_to_expiry": np.array([item['days_to_expiry'] for item in term_structure]),
        "iv": np.array([item['iv'] for item in term_structure]),
        "target_delta": target_delta
    }


def detect_term_structure_pattern(
    term_structure: Dict[str, np.ndarray]
) -> Dict[str, any]:
    """
    Detect the pattern in IV term structure
    
    Args:
        term_structure: Output from calculate_iv_term_structure
        
    Returns:
        Dictionary with pattern analysis
    """
    days = term_structure['days_to_expiry']
    ivs = term_structure['iv']
    
    if len(days) < 2:
        return {
            "pattern": "unknown",
            "slope": None,
            "contango": None
        }
    
    # Calculate slope (linear regression)
    slope, intercept = np.polyfit(days, ivs, 1)
    
    # Determine pattern
    if abs(slope) < 0.0001:
        pattern = "flat"
    elif slope > 0:
        pattern = "contango"  # IV increases with time (normal)
    else:
        pattern = "backwardation"  # IV decreases with time (unusual)
    
    # Calculate contango/backwardation magnitude
    if len(ivs) >= 2:
        front_iv = ivs[0]
        back_iv = ivs[-1]
        magnitude = back_iv - front_iv
    else:
        magnitude = 0
    
    return {
        "pattern": pattern,
        "slope": float(slope),
        "magnitude": float(magnitude),
        "front_month_iv": float(ivs[0]) if len(ivs) > 0 else None,
        "back_month_iv": float(ivs[-1]) if len(ivs) > 0 else None
    }


def compare_atm_otm_term_structures(
    option_chain: List[Dict],
    underlying_price: float
) -> Dict[str, Dict]:
    """
    Compare term structures for ATM and OTM options
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current price of underlying
        
    Returns:
        Dictionary with ATM and OTM term structures
    """
    # ATM (100% moneyness)
    atm_ts = calculate_iv_term_structure(
        option_chain, underlying_price, moneyness_target=1.0
    )
    
    # OTM Put (90% moneyness)
    otm_put_ts = calculate_iv_term_structure(
        option_chain, underlying_price, moneyness_target=0.90
    )
    
    # OTM Call (110% moneyness)
    otm_call_ts = calculate_iv_term_structure(
        option_chain, underlying_price, moneyness_target=1.10
    )
    
    return {
        "atm": atm_ts,
        "otm_put_90": otm_put_ts,
        "otm_call_110": otm_call_ts
    }
