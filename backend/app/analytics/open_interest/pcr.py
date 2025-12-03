"""Put-Call Ratio (PCR) calculations

PCR is a sentiment indicator. High PCR suggests bearish sentiment, low PCR suggests bullish.
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime


def calculate_pcr(
    option_chain: List[Dict],
    metric: str = "oi"
) -> Dict[str, float]:
    """
    Calculate Put-Call Ratio
    
    Args:
        option_chain: List of option contracts
        metric: 'oi' for open interest based, 'volume' for volume based
        
    Returns:
        Dictionary with PCR metrics
    """
    total_put_value = 0
    total_call_value = 0
    
    for option in option_chain:
        option_type = option.get('option_type', '').lower()
        
        if metric == 'oi':
            value = option.get('open_interest', 0)
        elif metric == 'volume':
            value = option.get('volume', 0)
        else:
            raise ValueError("metric must be 'oi' or 'volume'")
        
        if option_type == 'put':
            total_put_value += value
        elif option_type == 'call':
            total_call_value += value
    
    # Calculate PCR
    if total_call_value == 0:
        pcr = None
    else:
        pcr = total_put_value / total_call_value
    
    # Interpret sentiment
    sentiment = "neutral"
    if pcr is not None:
        if pcr > 1.5:
            sentiment = "bearish"
        elif pcr < 0.7:
            sentiment = "bullish"
    
    return {
        "pcr": pcr,
        "total_put": total_put_value,
        "total_call": total_call_value,
        "metric": metric,
        "sentiment": sentiment
    }


def calculate_pcr_by_expiry(
    option_chain: List[Dict],
    metric: str = "oi"
) -> Dict[str, Dict]:
    """
    Calculate PCR for each expiration date separately
    
    Args:
        option_chain: List of option contracts
        metric: 'oi' or 'volume'
        
    Returns:
        Dictionary mapping expiry dates to PCR data
    """
    expiry_groups = {}
    
    for option in option_chain:
        expiry = option.get('expiry')
        if not expiry:
            continue
        
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        
        days = (expiry - datetime.now()).days
        if days <= 0:
            continue
        
        if days not in expiry_groups:
            expiry_groups[days] = []
        
        expiry_groups[days].append(option)
    
    pcr_by_expiry = {}
    
    for days, options in sorted(expiry_groups.items()):
        pcr_data = calculate_pcr(options, metric=metric)
        pcr_data['days_to_expiry'] = days
        pcr_by_expiry[days] = pcr_data
    
    return pcr_by_expiry


def calculate_pcr_by_strike_range(
    option_chain: List[Dict],
    underlying_price: float,
    metric: str = "oi",
    ranges: List[tuple] = None
) -> Dict[str, Dict]:
    """
    Calculate PCR for different strike ranges (OTM, ATM, ITM)
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current underlying price
        metric: 'oi' or 'volume'
        ranges: List of (min_moneyness, max_moneyness) tuples
        
    Returns:
        Dictionary with PCR for each range
    """
    if ranges is None:
        ranges = [
            (0.0, 0.95, "OTM_Put"),
            (0.95, 1.05, "ATM"),
            (1.05, 2.0, "OTM_Call")
        ]
    
    pcr_by_range = {}
    
    for min_m, max_m, label in ranges:
        filtered_options = []
        
        for option in option_chain:
            strike = option.get('strike')
            if not strike:
                continue
            
            moneyness = strike / underlying_price
            
            if min_m <= moneyness < max_m:
                filtered_options.append(option)
        
        if filtered_options:
            pcr_data = calculate_pcr(filtered_options, metric=metric)
            pcr_data['moneyness_range'] = (min_m, max_m)
            pcr_by_range[label] = pcr_data
    
    return pcr_by_range


def calculate_weighted_pcr(
    option_chain: List[Dict],
    underlying_price: float,
    metric: str = "oi",
    weight_by: str = "distance"
) -> Dict[str, float]:
    """
    Calculate weighted PCR (giving more weight to ATM options)
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current underlying price
        metric: 'oi' or 'volume'
        weight_by: 'distance' (from ATM) or 'gamma' (by gamma exposure)
        
    Returns:
        Dictionary with weighted PCR
    """
    weighted_put = 0
    weighted_call = 0
    
    for option in option_chain:
        strike = option.get('strike')
        option_type = option.get('option_type', '').lower()
        
        if not strike:
            continue
        
        if metric == 'oi':
            value = option.get('open_interest', 0)
        else:
            value = option.get('volume', 0)
        
        # Calculate weight
        if weight_by == "distance":
            # Weight inversely proportional to distance from ATM
            distance = abs(strike - underlying_price) / underlying_price
            weight = 1 / (1 + distance * 5)  # Decay factor of 5
        elif weight_by == "gamma":
            # Weight by gamma (ATM options have highest gamma)
            gamma = option.get('gamma', 0)
            weight = abs(gamma) if gamma else 0
        else:
            weight = 1
        
        weighted_value = value * weight
        
        if option_type == 'put':
            weighted_put += weighted_value
        elif option_type == 'call':
            weighted_call += weighted_value
    
    if weighted_call == 0:
        weighted_pcr = None
    else:
        weighted_pcr = weighted_put / weighted_call
    
    return {
        "weighted_pcr": weighted_pcr,
        "weighted_put": weighted_put,
        "weighted_call": weighted_call,
        "weight_by": weight_by
    }


def track_pcr_trend(
    pcr_history: List[Dict],
    window: int = 5
) -> Dict[str, any]:
    """
    Analyze PCR trend over time
    
    Args:
        pcr_history: List of historical PCR data with 'timestamp' and 'pcr'
        window: Moving average window
        
    Returns:
        Dictionary with trend analysis
    """
    if len(pcr_history) < 2:
        return {
            "trend": "insufficient_data",
            "ma": None,
            "change": None
        }
    
    pcr_values = [entry['pcr'] for entry in pcr_history if entry.get('pcr') is not None]
    
    if len(pcr_values) < 2:
        return {
            "trend": "insufficient_data",
            "ma": None,
            "change": None
        }
    
    # Calculate moving average
    if len(pcr_values) >= window:
        ma = np.mean(pcr_values[-window:])
    else:
        ma = np.mean(pcr_values)
    
    # Calculate change
    recent_change = pcr_values[-1] - pcr_values[-2]
    
    # Determine trend
    if len(pcr_values) >= 3:
        if all(pcr_values[i] < pcr_values[i+1] for i in range(-3, -1)):
            trend = "increasing"
        elif all(pcr_values[i] > pcr_values[i+1] for i in range(-3, -1)):
            trend = "decreasing"
        else:
            trend = "mixed"
    else:
        trend = "neutral"
    
    return {
        "trend": trend,
        "current_pcr": pcr_values[-1],
        "ma": ma,
        "change": recent_change,
        "window": window
    }
