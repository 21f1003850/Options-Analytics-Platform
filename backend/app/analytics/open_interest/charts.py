"""Data generators for Open Interest charts

Generates data structures optimized for various chart visualizations.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime


def generate_oi_heatmap_data(
    option_chain: List[Dict],
    underlying_price: float
) -> Dict[str, any]:
    """
    Generate data for OI heatmap (strike x expiry)
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current underlying price
        
    Returns:
        Dictionary with heatmap data structure
    """
    # Group by expiry and strike
    heatmap_data = {}
    
    for option in option_chain:
        expiry = option.get('expiry')
        strike = option.get('strike')
        oi = option.get('open_interest', 0)
        option_type = option.get('option_type', '').lower()
        
        if not expiry or not strike or oi <= 0:
            continue
        
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        
        days = (expiry - datetime.now()).days
        if days <= 0:
            continue
        
        if days not in heatmap_data:
            heatmap_data[days] = {}
        
        if strike not in heatmap_data[days]:
            heatmap_data[days][strike] = {'call': 0, 'put': 0}
        
        if option_type == 'call':
            heatmap_data[days][strike]['call'] += oi
        elif option_type == 'put':
            heatmap_data[days][strike]['put'] += oi
    
    # Convert to array format
    expiries = sorted(heatmap_data.keys())
    all_strikes = set()
    for strikes_dict in heatmap_data.values():
        all_strikes.update(strikes_dict.keys())
    strikes = sorted(all_strikes)
    
    # Create matrices for calls and puts
    call_matrix = np.zeros((len(expiries), len(strikes)))
    put_matrix = np.zeros((len(expiries), len(strikes)))
    
    for i, expiry in enumerate(expiries):
        for j, strike in enumerate(strikes):
            data = heatmap_data[expiry].get(strike, {'call': 0, 'put': 0})
            call_matrix[i, j] = data['call']
            put_matrix[i, j] = data['put']
    
    # Calculate combined (net) matrix
    # Positive = call dominance, Negative = put dominance
    net_matrix = call_matrix - put_matrix
    
    return {
        "expiries": expiries,
        "strikes": strikes,
        "call_oi": call_matrix.tolist(),
        "put_oi": put_matrix.tolist(),
        "net_oi": net_matrix.tolist(),
        "underlying_price": underlying_price
    }


def generate_oi_distribution_data(
    option_chain: List[Dict],
    underlying_price: float,
    expiry_days: Optional[int] = None
) -> Dict[str, any]:
    """
    Generate data for OI distribution chart (bar chart by strike)
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current underlying price
        expiry_days: Optional filter for specific expiry
        
    Returns:
        Dictionary with distribution data
    """
    strike_oi = {}
    
    for option in option_chain:
        expiry = option.get('expiry')
        strike = option.get('strike')
        oi = option.get('open_interest', 0)
        option_type = option.get('option_type', '').lower()
        
        if not strike or oi <= 0:
            continue
        
        # Filter by expiry if specified
        if expiry_days is not None:
            if isinstance(expiry, str):
                expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
            
            days = (expiry - datetime.now()).days
            if abs(days - expiry_days) > 1:
                continue
        
        if strike not in strike_oi:
            strike_oi[strike] = {'call': 0, 'put': 0}
        
        if option_type == 'call':
            strike_oi[strike]['call'] += oi
        elif option_type == 'put':
            strike_oi[strike]['put'] += oi
    
    # Sort by strike
    strikes = sorted(strike_oi.keys())
    call_ois = [strike_oi[s]['call'] for s in strikes]
    put_ois = [strike_oi[s]['put'] for s in strikes]
    
    # Mark ATM strike
    atm_idx = np.argmin([abs(s - underlying_price) for s in strikes]) if strikes else None
    atm_strike = strikes[atm_idx] if atm_idx is not None else None
    
    return {
        "strikes": strikes,
        "call_oi": call_ois,
        "put_oi": put_ois,
        "underlying_price": underlying_price,
        "atm_strike": atm_strike,
        "expiry_days": expiry_days
    }


def generate_oi_waterfall_data(
    current_chain: List[Dict],
    previous_chain: List[Dict],
    underlying_price: float,
    top_n: int = 20
) -> Dict[str, any]:
    """
    Generate data for OI waterfall chart (showing changes)
    
    Args:
        current_chain: Current option chain
        previous_chain: Previous option chain
        underlying_price: Current underlying price
        top_n: Number of top changes to show
        
    Returns:
        Dictionary with waterfall data
    """
    # Build maps
    current_oi = {}
    previous_oi = {}
    
    for option in current_chain:
        symbol = option.get('symbol')
        if symbol:
            current_oi[symbol] = {
                'strike': option.get('strike'),
                'oi': option.get('open_interest', 0),
                'option_type': option.get('option_type', '').lower()
            }
    
    for option in previous_chain:
        symbol = option.get('symbol')
        if symbol:
            previous_oi[symbol] = {
                'strike': option.get('strike'),
                'oi': option.get('open_interest', 0),
                'option_type': option.get('option_type', '').lower()
            }
    
    # Calculate changes
    changes = []
    
    for symbol, current_data in current_oi.items():
        previous_data = previous_oi.get(symbol, {})
        previous = previous_data.get('oi', 0)
        current = current_data['oi']
        
        change = current - previous
        
        if change != 0:
            changes.append({
                'symbol': symbol,
                'strike': current_data['strike'],
                'option_type': current_data['option_type'],
                'change': change,
                'current': current,
                'previous': previous
            })
    
    # Sort by absolute change and take top N
    changes.sort(key=lambda x: abs(x['change']), reverse=True)
    top_changes = changes[:top_n]
    
    # Separate increases and decreases
    increases = [c for c in top_changes if c['change'] > 0]
    decreases = [c for c in top_changes if c['change'] < 0]
    
    return {
        "increases": increases,
        "decreases": decreases,
        "net_change": sum(c['change'] for c in changes),
        "underlying_price": underlying_price
    }


def generate_oi_by_moneyness_data(
    option_chain: List[Dict],
    underlying_price: float,
    bins: int = 10
) -> Dict[str, any]:
    """
    Generate OI distribution by moneyness buckets
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current underlying price
        bins: Number of moneyness bins
        
    Returns:
        Dictionary with moneyness distribution
    """
    # Define moneyness ranges (e.g., 0.9-0.95, 0.95-1.0, 1.0-1.05, etc.)
    moneyness_ranges = np.linspace(0.7, 1.3, bins + 1)
    
    # Initialize buckets
    buckets = {
        f"{moneyness_ranges[i]:.2f}-{moneyness_ranges[i+1]:.2f}": {'call': 0, 'put': 0}
        for i in range(len(moneyness_ranges) - 1)
    }
    
    for option in option_chain:
        strike = option.get('strike')
        oi = option.get('open_interest', 0)
        option_type = option.get('option_type', '').lower()
        
        if not strike or oi <= 0:
            continue
        
        moneyness = strike / underlying_price
        
        # Find appropriate bucket
        for i in range(len(moneyness_ranges) - 1):
            if moneyness_ranges[i] <= moneyness < moneyness_ranges[i + 1]:
                bucket_key = f"{moneyness_ranges[i]:.2f}-{moneyness_ranges[i+1]:.2f}"
                
                if option_type == 'call':
                    buckets[bucket_key]['call'] += oi
                elif option_type == 'put':
                    buckets[bucket_key]['put'] += oi
                break
    
    # Convert to lists
    bucket_labels = list(buckets.keys())
    call_ois = [buckets[label]['call'] for label in bucket_labels]
    put_ois = [buckets[label]['put'] for label in bucket_labels]
    
    return {
        "moneyness_ranges": bucket_labels,
        "call_oi": call_ois,
        "put_oi": put_ois,
        "underlying_price": underlying_price
    }


def generate_oi_volume_comparison_data(
    option_chain: List[Dict],
    underlying_price: float,
    top_n: int = 20
) -> Dict[str, any]:
    """
    Generate data comparing OI vs Volume for top contracts
    
    Helps identify active vs dormant contracts.
    
    Args:
        option_chain: List of option contracts
        underlying_price: Current underlying price
        top_n: Number of top contracts to show
        
    Returns:
        Dictionary with OI/Volume comparison
    """
    contracts = []
    
    for option in option_chain:
        symbol = option.get('symbol')
        strike = option.get('strike')
        oi = option.get('open_interest', 0)
        volume = option.get('volume', 0)
        option_type = option.get('option_type', '').lower()
        
        if not symbol or not strike:
            continue
        
        # Calculate volume/OI ratio
        vol_oi_ratio = (volume / oi) if oi > 0 else 0
        
        contracts.append({
            'symbol': symbol,
            'strike': strike,
            'option_type': option_type,
            'oi': oi,
            'volume': volume,
            'vol_oi_ratio': vol_oi_ratio,
            'moneyness': strike / underlying_price
        })
    
    # Sort by OI and take top N
    contracts.sort(key=lambda x: x['oi'], reverse=True)
    top_contracts = contracts[:top_n]
    
    return {
        "contracts": top_contracts,
        "underlying_price": underlying_price,
        "avg_vol_oi_ratio": np.mean([c['vol_oi_ratio'] for c in top_contracts])
    }


def generate_oi_timeline_data(
    historical_chains: List[Tuple[datetime, List[Dict]]],
    strike: float,
    option_type: str
) -> Dict[str, any]:
    """
    Generate timeline data for a specific option contract
    
    Args:
        historical_chains: List of (timestamp, option_chain) tuples
        strike: Strike price to track
        option_type: 'call' or 'put'
        
    Returns:
        Dictionary with timeline data
    """
    timeline = []
    
    for timestamp, chain in historical_chains:
        # Find the specific contract
        for option in chain:
            if (option.get('strike') == strike and 
                option.get('option_type', '').lower() == option_type.lower()):
                
                timeline.append({
                    'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
                    'oi': option.get('open_interest', 0),
                    'volume': option.get('volume', 0),
                    'price': option.get('last', 0),
                    'iv': option.get('implied_volatility', 0)
                })
                break
    
    if not timeline:
        return {
            "timeline": [],
            "strike": strike,
            "option_type": option_type
        }
    
    return {
        "timeline": timeline,
        "strike": strike,
        "option_type": option_type,
        "oi_change": timeline[-1]['oi'] - timeline[0]['oi'] if len(timeline) > 1 else 0
    }
