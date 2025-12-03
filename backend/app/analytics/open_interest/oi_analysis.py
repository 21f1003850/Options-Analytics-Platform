"""Open Interest Analysis

Analyzes OI changes, buildup/unwinding patterns, and concentration.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime


def analyze_oi_changes(
    current_chain: List[Dict],
    previous_chain: List[Dict]
) -> Dict[str, any]:
    """
    Analyze changes in open interest between two time periods
    
    Args:
        current_chain: Current option chain data
        previous_chain: Previous option chain data (e.g., from yesterday)
        
    Returns:
        Dictionary with OI change analysis
    """
    # Build maps of symbol -> OI
    current_oi = {}
    previous_oi = {}
    
    for option in current_chain:
        symbol = option.get('symbol')
        oi = option.get('open_interest', 0)
        if symbol:
            current_oi[symbol] = {
                'oi': oi,
                'strike': option.get('strike'),
                'option_type': option.get('option_type', '').lower()
            }
    
    for option in previous_chain:
        symbol = option.get('symbol')
        oi = option.get('open_interest', 0)
        if symbol:
            previous_oi[symbol] = {
                'oi': oi,
                'strike': option.get('strike'),
                'option_type': option.get('option_type', '').lower()
            }
    
    # Calculate changes
    changes = []
    total_increase = 0
    total_decrease = 0
    
    for symbol, current_data in current_oi.items():
        current = current_data['oi']
        previous = previous_oi.get(symbol, {}).get('oi', 0)
        
        change = current - previous
        change_pct = (change / previous * 100) if previous > 0 else (100 if change > 0 else 0)
        
        changes.append({
            'symbol': symbol,
            'strike': current_data['strike'],
            'option_type': current_data['option_type'],
            'current_oi': current,
            'previous_oi': previous,
            'change': change,
            'change_pct': change_pct
        })
        
        if change > 0:
            total_increase += change
        else:
            total_decrease += abs(change)
    
    # Sort by absolute change
    changes.sort(key=lambda x: abs(x['change']), reverse=True)
    
    # Aggregate by type
    call_changes = [c for c in changes if c['option_type'] == 'call']
    put_changes = [c for c in changes if c['option_type'] == 'put']
    
    call_net_change = sum(c['change'] for c in call_changes)
    put_net_change = sum(c['change'] for c in put_changes)
    
    return {
        "total_increase": int(total_increase),
        "total_decrease": int(total_decrease),
        "net_change": int(total_increase - total_decrease),
        "call_net_change": int(call_net_change),
        "put_net_change": int(put_net_change),
        "top_increases": changes[:10],
        "top_decreases": sorted(changes, key=lambda x: x['change'])[:10],
        "total_contracts_analyzed": len(changes)
    }


def detect_oi_buildup_unwinding(
    oi_changes: Dict[str, any],
    volume_data: Optional[List[Dict]] = None
) -> Dict[str, any]:
    """
    Detect OI buildup (new positions) or unwinding (closing positions)
    
    Buildup: OI increases with volume
    Unwinding: OI decreases with volume
    
    Args:
        oi_changes: Output from analyze_oi_changes
        volume_data: Optional volume data to compare
        
    Returns:
        Dictionary with buildup/unwinding signals
    """
    call_net_change = oi_changes.get('call_net_change', 0)
    put_net_change = oi_changes.get('put_net_change', 0)
    
    # Classify changes
    patterns = []
    
    # Call analysis
    if call_net_change > 0:
        patterns.append({
            'type': 'call_buildup',
            'magnitude': call_net_change,
            'interpretation': 'Bullish - New call buying or bearish call writing'
        })
    elif call_net_change < 0:
        patterns.append({
            'type': 'call_unwinding',
            'magnitude': abs(call_net_change),
            'interpretation': 'Neutral to Bearish - Closing call positions'
        })
    
    # Put analysis
    if put_net_change > 0:
        patterns.append({
            'type': 'put_buildup',
            'magnitude': put_net_change,
            'interpretation': 'Bearish - New put buying or bullish put writing'
        })
    elif put_net_change < 0:
        patterns.append({
            'type': 'put_unwinding',
            'magnitude': abs(put_net_change),
            'interpretation': 'Neutral to Bullish - Closing put positions'
        })
    
    # Overall sentiment
    net_change = call_net_change + put_net_change
    
    if net_change > 0:
        overall_sentiment = "buildup"
    elif net_change < 0:
        overall_sentiment = "unwinding"
    else:
        overall_sentiment = "neutral"
    
    # Specific patterns
    if call_net_change > 0 and put_net_change < 0:
        specific_pattern = "bullish_rotation"
    elif call_net_change < 0 and put_net_change > 0:
        specific_pattern = "bearish_rotation"
    elif call_net_change > 0 and put_net_change > 0:
        specific_pattern = "overall_buildup"
    elif call_net_change < 0 and put_net_change < 0:
        specific_pattern = "overall_unwinding"
    else:
        specific_pattern = "neutral"
    
    return {
        "overall_sentiment": overall_sentiment,
        "specific_pattern": specific_pattern,
        "patterns": patterns,
        "call_net_change": call_net_change,
        "put_net_change": put_net_change
    }


def calculate_oi_concentration(
    option_chain: List[Dict],
    underlying_price: float,
    top_n: int = 10
) -> Dict[str, any]:
    """
    Calculate open interest concentration at specific strikes
    
    High concentration can act as support/resistance.
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current underlying price
        top_n: Number of top strikes to return
        
    Returns:
        Dictionary with concentration analysis
    """
    # Aggregate OI by strike
    strike_oi = {}
    
    for option in option_chain:
        strike = option.get('strike')
        oi = option.get('open_interest', 0)
        option_type = option.get('option_type', '').lower()
        
        if not strike or oi <= 0:
            continue
        
        if strike not in strike_oi:
            strike_oi[strike] = {'call': 0, 'put': 0, 'total': 0}
        
        if option_type == 'call':
            strike_oi[strike]['call'] += oi
        elif option_type == 'put':
            strike_oi[strike]['put'] += oi
        
        strike_oi[strike]['total'] += oi
    
    if not strike_oi:
        return {
            "top_strikes": [],
            "concentration_pct": {}
        }
    
    # Calculate total OI
    total_oi = sum(data['total'] for data in strike_oi.values())
    
    # Sort by total OI
    sorted_strikes = sorted(
        strike_oi.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )
    
    # Get top N strikes
    top_strikes = []
    for strike, data in sorted_strikes[:top_n]:
        concentration_pct = (data['total'] / total_oi * 100) if total_oi > 0 else 0
        
        top_strikes.append({
            'strike': float(strike),
            'total_oi': int(data['total']),
            'call_oi': int(data['call']),
            'put_oi': int(data['put']),
            'concentration_pct': float(concentration_pct),
            'distance_from_price': float(abs(strike - underlying_price)),
            'distance_pct': float(abs(strike - underlying_price) / underlying_price * 100)
        })
    
    # Calculate concentration metrics
    top_5_concentration = sum(s['concentration_pct'] for s in top_strikes[:5])
    top_10_concentration = sum(s['concentration_pct'] for s in top_strikes[:10])
    
    # Find key levels (strikes near current price with high OI)
    key_levels = [
        s for s in top_strikes
        if s['distance_pct'] < 5  # Within 5% of current price
    ]
    
    return {
        "top_strikes": top_strikes,
        "total_oi": int(total_oi),
        "top_5_concentration_pct": float(top_5_concentration),
        "top_10_concentration_pct": float(top_10_concentration),
        "key_support_resistance_levels": key_levels,
        "strike_count": len(strike_oi)
    }


def identify_gamma_walls(
    option_chain: List[Dict],
    underlying_price: float,
    threshold_pct: float = 0.1
) -> Dict[str, any]:
    """
    Identify potential gamma walls (high gamma concentration points)
    
    Gamma walls can cause price to stick at certain levels.
    
    Args:
        option_chain: List of option contracts with gamma
        underlying_price: Current underlying price
        threshold_pct: Threshold for significant concentration (% of total)
        
    Returns:
        Dictionary with gamma wall analysis
    """
    # Aggregate gamma by strike
    strike_gamma = {}
    
    for option in option_chain:
        strike = option.get('strike')
        gamma = option.get('gamma', 0)
        oi = option.get('open_interest', 0)
        option_type = option.get('option_type', '').lower()
        
        if not strike or not gamma or oi <= 0:
            continue
        
        # Gamma exposure = gamma * OI * underlying_price * 100
        gamma_exposure = abs(gamma) * oi * underlying_price * 100
        
        if strike not in strike_gamma:
            strike_gamma[strike] = {'call': 0, 'put': 0, 'total': 0}
        
        if option_type == 'call':
            strike_gamma[strike]['call'] += gamma_exposure
        elif option_type == 'put':
            strike_gamma[strike]['put'] += gamma_exposure
        
        strike_gamma[strike]['total'] += gamma_exposure
    
    if not strike_gamma:
        return {
            "gamma_walls": [],
            "strongest_wall": None
        }
    
    total_gamma = sum(data['total'] for data in strike_gamma.values())
    
    # Find significant gamma concentrations
    gamma_walls = []
    
    for strike, data in strike_gamma.items():
        concentration_pct = (data['total'] / total_gamma * 100) if total_gamma > 0 else 0
        
        if concentration_pct >= threshold_pct:
            gamma_walls.append({
                'strike': float(strike),
                'gamma_exposure': float(data['total']),
                'call_gamma': float(data['call']),
                'put_gamma': float(data['put']),
                'concentration_pct': float(concentration_pct),
                'relative_to_price': 'above' if strike > underlying_price else 'below'
            })
    
    # Sort by concentration
    gamma_walls.sort(key=lambda x: x['gamma_exposure'], reverse=True)
    
    strongest_wall = gamma_walls[0] if gamma_walls else None
    
    return {
        "gamma_walls": gamma_walls,
        "strongest_wall": strongest_wall,
        "total_gamma_exposure": float(total_gamma),
        "wall_count": len(gamma_walls)
    }
