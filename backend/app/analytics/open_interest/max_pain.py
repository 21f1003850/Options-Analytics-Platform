"""Max Pain calculation

Max Pain theory suggests that the price tends to move toward the strike
where option sellers would experience the least losses (or maximum profit).
"""

import numpy as np
from typing import List, Dict, Optional


def calculate_max_pain(
    option_chain: List[Dict],
    strike_range: Optional[tuple] = None
) -> Dict[str, any]:
    """
    Calculate the Max Pain strike price
    
    Max Pain is the strike price where the total dollar value of 
    call and put open interest would result in the least losses for option writers.
    
    Args:
        option_chain: List of option contracts with strike, OI, and option_type
        strike_range: Optional (min_strike, max_strike) to limit calculation
        
    Returns:
        Dictionary with max pain strike and pain values for all strikes
    """
    if not option_chain:
        return {
            "max_pain_strike": None,
            "pain_by_strike": {},
            "total_call_oi": 0,
            "total_put_oi": 0
        }
    
    # Collect all strikes and their call/put OI
    strike_data = {}
    
    for option in option_chain:
        strike = option.get('strike')
        oi = option.get('open_interest', 0)
        option_type = option.get('option_type', '').lower()
        
        if not strike or oi <= 0:
            continue
        
        if strike_range:
            if strike < strike_range[0] or strike > strike_range[1]:
                continue
        
        if strike not in strike_data:
            strike_data[strike] = {'call_oi': 0, 'put_oi': 0}
        
        if option_type == 'call':
            strike_data[strike]['call_oi'] += oi
        elif option_type == 'put':
            strike_data[strike]['put_oi'] += oi
    
    if not strike_data:
        return {
            "max_pain_strike": None,
            "pain_by_strike": {},
            "total_call_oi": 0,
            "total_put_oi": 0
        }
    
    # Calculate total pain at each potential price point
    strikes = sorted(strike_data.keys())
    pain_by_strike = {}
    
    for test_price in strikes:
        total_pain = 0
        
        # Calculate pain for all call options
        for strike, data in strike_data.items():
            call_oi = data['call_oi']
            put_oi = data['put_oi']
            
            # Call pain: intrinsic value * OI (only if ITM)
            if test_price > strike:
                call_pain = (test_price - strike) * call_oi
                total_pain += call_pain
            
            # Put pain: intrinsic value * OI (only if ITM)
            if test_price < strike:
                put_pain = (strike - test_price) * put_oi
                total_pain += put_pain
        
        pain_by_strike[test_price] = total_pain
    
    # Find strike with minimum pain (max pain point)
    max_pain_strike = min(pain_by_strike.items(), key=lambda x: x[1])[0]
    
    # Calculate totals
    total_call_oi = sum(data['call_oi'] for data in strike_data.values())
    total_put_oi = sum(data['put_oi'] for data in strike_data.values())
    
    return {
        "max_pain_strike": float(max_pain_strike),
        "max_pain_value": float(pain_by_strike[max_pain_strike]),
        "pain_by_strike": {float(k): float(v) for k, v in pain_by_strike.items()},
        "total_call_oi": int(total_call_oi),
        "total_put_oi": int(total_put_oi),
        "strike_count": len(strikes)
    }


def calculate_max_pain_by_expiry(
    option_chain: List[Dict]
) -> Dict[int, Dict]:
    """
    Calculate max pain for each expiration date
    
    Args:
        option_chain: List of option contracts
        
    Returns:
        Dictionary mapping days to expiry to max pain data
    """
    from datetime import datetime
    
    # Group by expiry
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
    
    max_pain_by_expiry = {}
    
    for days, options in sorted(expiry_groups.items()):
        mp = calculate_max_pain(options)
        mp['days_to_expiry'] = days
        max_pain_by_expiry[days] = mp
    
    return max_pain_by_expiry


def calculate_pain_distribution(
    max_pain_data: Dict[str, any],
    underlying_price: float
) -> Dict[str, any]:
    """
    Analyze the distribution of pain values
    
    Args:
        max_pain_data: Output from calculate_max_pain
        underlying_price: Current underlying price
        
    Returns:
        Dictionary with distribution analysis
    """
    pain_by_strike = max_pain_data.get('pain_by_strike', {})
    max_pain_strike = max_pain_data.get('max_pain_strike')
    
    if not pain_by_strike or max_pain_strike is None:
        return {}
    
    strikes = np.array(list(pain_by_strike.keys()))
    pains = np.array(list(pain_by_strike.values()))
    
    # Normalize pain values (0 to 1)
    if pains.max() > pains.min():
        normalized_pains = (pains - pains.min()) / (pains.max() - pains.min())
    else:
        normalized_pains = np.zeros_like(pains)
    
    # Calculate distance metrics
    max_pain_distance = abs(underlying_price - max_pain_strike)
    max_pain_direction = "above" if underlying_price > max_pain_strike else "below"
    
    # Find support/resistance (strikes with high pain = more OI)
    high_pain_threshold = np.percentile(pains, 75)
    support_resistance_strikes = [
        float(strike) for strike, pain in pain_by_strike.items()
        if pain >= high_pain_threshold
    ]
    
    return {
        "max_pain_distance": float(max_pain_distance),
        "max_pain_distance_pct": float(max_pain_distance / underlying_price * 100),
        "max_pain_direction": max_pain_direction,
        "pain_range": float(pains.max() - pains.min()),
        "avg_pain": float(np.mean(pains)),
        "support_resistance_strikes": sorted(support_resistance_strikes)
    }


def track_max_pain_movement(
    max_pain_history: List[Dict]
) -> Dict[str, any]:
    """
    Track how max pain has moved over time
    
    Args:
        max_pain_history: List of historical max pain data with timestamp and max_pain_strike
        
    Returns:
        Dictionary with movement analysis
    """
    if len(max_pain_history) < 2:
        return {
            "movement": "insufficient_data",
            "change": None,
            "velocity": None
        }
    
    strikes = [entry.get('max_pain_strike') for entry in max_pain_history]
    strikes = [s for s in strikes if s is not None]
    
    if len(strikes) < 2:
        return {
            "movement": "insufficient_data",
            "change": None,
            "velocity": None
        }
    
    # Calculate change
    recent_change = strikes[-1] - strikes[-2]
    total_change = strikes[-1] - strikes[0]
    
    # Calculate velocity (average change per period)
    velocity = total_change / len(strikes)
    
    # Determine movement trend
    if abs(recent_change) < 0.01:
        movement = "stable"
    elif recent_change > 0:
        movement = "upward"
    else:
        movement = "downward"
    
    return {
        "movement": movement,
        "recent_change": float(recent_change),
        "total_change": float(total_change),
        "velocity": float(velocity),
        "current_strike": float(strikes[-1]),
        "initial_strike": float(strikes[0])
    }
