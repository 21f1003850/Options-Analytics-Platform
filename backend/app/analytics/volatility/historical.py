"""Historical Volatility and IV Comparisons

Compares implied volatility with historical volatility and calculates IV percentiles.
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta


def calculate_historical_volatility(
    price_data: List[Dict],
    window: int = 30,
    annualize: bool = True
) -> float:
    """
    Calculate historical volatility from price data
    
    Args:
        price_data: List of price data with 'close' prices
        window: Number of periods for calculation
        annualize: If True, annualize the volatility
        
    Returns:
        Historical volatility (annualized if specified)
    """
    if len(price_data) < window + 1:
        return 0.0
    
    # Extract close prices
    closes = np.array([p['close'] for p in price_data[-window-1:]])
    
    # Calculate log returns
    log_returns = np.diff(np.log(closes))
    
    # Calculate standard deviation
    volatility = np.std(log_returns, ddof=1)
    
    # Annualize (assuming 252 trading days)
    if annualize:
        volatility = volatility * np.sqrt(252)
    
    return float(volatility)


def calculate_multiple_hv_windows(
    price_data: List[Dict],
    windows: List[int] = [10, 20, 30, 60, 90, 252]
) -> Dict[int, float]:
    """
    Calculate historical volatility for multiple time windows
    
    Args:
        price_data: List of price data
        windows: List of window sizes in days
        
    Returns:
        Dictionary mapping window size to HV
    """
    hv_values = {}
    
    for window in windows:
        if len(price_data) >= window + 1:
            hv = calculate_historical_volatility(price_data, window=window)
            hv_values[window] = hv
    
    return hv_values


def calculate_iv_percentile(
    current_iv: float,
    iv_history: List[float],
    lookback_days: int = 252
) -> float:
    """
    Calculate IV percentile rank
    
    Args:
        current_iv: Current implied volatility
        iv_history: Historical IV values
        lookback_days: Number of days to look back
        
    Returns:
        Percentile rank (0-100)
    """
    if not iv_history:
        return 50.0
    
    # Use only lookback period
    recent_ivs = iv_history[-lookback_days:] if len(iv_history) > lookback_days else iv_history
    
    # Calculate percentile
    percentile = (np.sum(np.array(recent_ivs) < current_iv) / len(recent_ivs)) * 100
    
    return float(percentile)


def calculate_iv_rank(
    current_iv: float,
    iv_history: List[float],
    lookback_days: int = 252
) -> float:
    """
    Calculate IV rank (0-100 scale based on 52-week high/low)
    
    Args:
        current_iv: Current implied volatility
        iv_history: Historical IV values
        lookback_days: Number of days to look back
        
    Returns:
        IV rank (0-100)
    """
    if not iv_history:
        return 50.0
    
    recent_ivs = iv_history[-lookback_days:] if len(iv_history) > lookback_days else iv_history
    
    iv_min = np.min(recent_ivs)
    iv_max = np.max(recent_ivs)
    
    if iv_max == iv_min:
        return 50.0
    
    iv_rank = ((current_iv - iv_min) / (iv_max - iv_min)) * 100
    
    return float(np.clip(iv_rank, 0, 100))


def compare_iv_hv(
    current_iv: float,
    historical_volatility: float
) -> Dict[str, float]:
    """
    Compare implied volatility with historical volatility
    
    Args:
        current_iv: Current implied volatility
        historical_volatility: Calculated historical volatility
        
    Returns:
        Dictionary with comparison metrics
    """
    iv_hv_ratio = current_iv / historical_volatility if historical_volatility > 0 else None
    iv_hv_diff = current_iv - historical_volatility
    
    # Determine if IV is cheap or expensive
    status = "neutral"
    if iv_hv_ratio:
        if iv_hv_ratio < 0.8:
            status = "cheap"  # IV significantly below HV
        elif iv_hv_ratio > 1.2:
            status = "expensive"  # IV significantly above HV
    
    return {
        "current_iv": current_iv,
        "historical_volatility": historical_volatility,
        "iv_hv_ratio": iv_hv_ratio,
        "iv_hv_diff": iv_hv_diff,
        "status": status
    }


def calculate_volatility_cone(
    price_data: List[Dict],
    windows: List[int] = [10, 20, 30, 60, 90],
    percentiles: List[int] = [10, 25, 50, 75, 90]
) -> Dict[int, Dict[int, float]]:
    """
    Calculate volatility cone (HV at different windows and percentiles)
    
    The volatility cone shows the range of historical volatilities
    at different time periods.
    
    Args:
        price_data: List of price data
        windows: Window sizes to calculate
        percentiles: Percentile levels to show
        
    Returns:
        Nested dictionary: {window: {percentile: hv_value}}
    """
    cone = {}
    
    for window in windows:
        if len(price_data) < window * 3:  # Need enough data
            continue
        
        # Calculate rolling HV for this window
        hvs = []
        for i in range(window, len(price_data)):
            hv = calculate_historical_volatility(
                price_data[:i],
                window=window,
                annualize=True
            )
            hvs.append(hv)
        
        if hvs:
            cone[window] = {}
            for pct in percentiles:
                cone[window][pct] = float(np.percentile(hvs, pct))
    
    return cone


def analyze_volatility_regime(
    current_iv: float,
    iv_history: List[float],
    hv: float,
    lookback_days: int = 252
) -> Dict[str, any]:
    """
    Comprehensive volatility regime analysis
    
    Args:
        current_iv: Current implied volatility
        iv_history: Historical IV values
        hv: Current historical volatility
        lookback_days: Lookback period
        
    Returns:
        Dictionary with comprehensive analysis
    """
    iv_percentile = calculate_iv_percentile(current_iv, iv_history, lookback_days)
    iv_rank = calculate_iv_rank(current_iv, iv_history, lookback_days)
    iv_hv_comparison = compare_iv_hv(current_iv, hv)
    
    # Determine regime
    regime = "neutral"
    if iv_percentile >= 75:
        regime = "high_volatility"
    elif iv_percentile <= 25:
        regime = "low_volatility"
    
    # Determine IV vs HV bias
    if iv_hv_comparison['iv_hv_ratio']:
        if iv_hv_comparison['iv_hv_ratio'] > 1.2:
            iv_premium = "high"
        elif iv_hv_comparison['iv_hv_ratio'] < 0.8:
            iv_premium = "low"
        else:
            iv_premium = "normal"
    else:
        iv_premium = "unknown"
    
    return {
        "regime": regime,
        "iv_percentile": iv_percentile,
        "iv_rank": iv_rank,
        "iv_premium": iv_premium,
        **iv_hv_comparison
    }
