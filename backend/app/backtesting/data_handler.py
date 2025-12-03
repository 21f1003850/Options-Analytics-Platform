"""Data handler for backtesting"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np


class DataHandler:
    """Handles historical data for backtesting"""
    
    def __init__(self, data: Dict[str, List[Dict]]):
        """
        Initialize data handler
        
        Args:
            data: Dictionary mapping symbols to OHLCV data
                  Each entry: {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
        """
        self.data = data
        self._index = {}
        self._initialize_index()
    
    def _initialize_index(self):
        """Create index for fast data lookup"""
        for symbol, bars in self.data.items():
            self._index[symbol] = {}
            for i, bar in enumerate(bars):
                timestamp = bar['timestamp']
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                self._index[symbol][timestamp] = i
    
    def get_bar(self, symbol: str, timestamp: datetime) -> Optional[Dict]:
        """Get specific bar for symbol at timestamp"""
        if symbol not in self._index:
            return None
        
        if timestamp not in self._index[symbol]:
            return None
        
        idx = self._index[symbol][timestamp]
        return self.data[symbol][idx]
    
    def get_historical_bars(
        self,
        symbol: str,
        end_date: datetime,
        lookback_days: int
    ) -> List[Dict]:
        """
        Get historical bars for a symbol
        
        Args:
            symbol: Symbol to retrieve
            end_date: End date
            lookback_days: Number of days to look back
            
        Returns:
            List of bars
        """
        if symbol not in self.data:
            return []
        
        start_date = end_date - timedelta(days=lookback_days)
        
        bars = []
        for bar in self.data[symbol]:
            timestamp = bar['timestamp']
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            if start_date <= timestamp <= end_date:
                bars.append(bar)
        
        return bars
    
    def get_symbols(self) -> List[str]:
        """Get list of available symbols"""
        return list(self.data.keys())
    
    def get_date_range(self) -> tuple:
        """Get overall date range of data"""
        all_dates = []
        
        for symbol_data in self.data.values():
            for bar in symbol_data:
                timestamp = bar['timestamp']
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                all_dates.append(timestamp)
        
        if not all_dates:
            return None, None
        
        return min(all_dates), max(all_dates)


def resample_data(
    data: List[Dict],
    target_timeframe: str = "1d"
) -> List[Dict]:
    """
    Resample OHLCV data to different timeframe
    
    Args:
        data: List of OHLCV bars
        target_timeframe: Target timeframe ('1h', '4h', '1d', '1w')
        
    Returns:
        Resampled data
    """
    if not data:
        return []
    
    # Determine grouping based on timeframe
    if target_timeframe == "1h":
        group_by = lambda dt: (dt.year, dt.month, dt.day, dt.hour)
    elif target_timeframe == "4h":
        group_by = lambda dt: (dt.year, dt.month, dt.day, dt.hour // 4)
    elif target_timeframe == "1d":
        group_by = lambda dt: (dt.year, dt.month, dt.day)
    elif target_timeframe == "1w":
        group_by = lambda dt: (dt.year, dt.isocalendar()[1])
    else:
        return data  # Unknown timeframe, return as is
    
    # Group bars
    groups = {}
    for bar in data:
        timestamp = bar['timestamp']
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        key = group_by(timestamp)
        if key not in groups:
            groups[key] = []
        groups[key].append(bar)
    
    # Aggregate each group
    resampled = []
    for key in sorted(groups.keys()):
        bars = groups[key]
        
        # OHLCV aggregation
        opens = [b['open'] for b in bars]
        highs = [b['high'] for b in bars]
        lows = [b['low'] for b in bars]
        closes = [b['close'] for b in bars]
        volumes = [b.get('volume', 0) for b in bars]
        
        # Use timestamp of first bar in group
        timestamp = bars[0]['timestamp']
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        resampled.append({
            'timestamp': timestamp,
            'open': opens[0],
            'high': max(highs),
            'low': min(lows),
            'close': closes[-1],
            'volume': sum(volumes)
        })
    
    return resampled


def generate_synthetic_option_data(
    underlying_data: List[Dict],
    strike: float,
    expiry: datetime,
    option_type: str = "call",
    volatility: float = 0.25
) -> List[Dict]:
    """
    Generate synthetic option price data from underlying data
    
    Uses Black-Scholes for pricing
    
    Args:
        underlying_data: Underlying price data
        strike: Strike price
        expiry: Expiration date
        option_type: 'call' or 'put'
        volatility: Implied volatility
        
    Returns:
        List of option price bars
    """
    from ..analytics.greeks.black_scholes import black_scholes_price
    
    option_data = []
    risk_free_rate = 0.05  # Assume 5% risk-free rate
    
    for bar in underlying_data:
        timestamp = bar['timestamp']
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        # Skip if past expiry
        if timestamp >= expiry:
            continue
        
        # Calculate time to expiry
        days_to_expiry = (expiry - timestamp).days
        T = max(days_to_expiry / 365, 0.001)  # Avoid division by zero
        
        # Calculate option price using BS
        S = bar['close']
        
        try:
            price = black_scholes_price(
                S=S,
                K=strike,
                T=T,
                r=risk_free_rate,
                sigma=volatility,
                option_type=option_type
            )
            
            # Estimate bid/ask spread
            spread = price * 0.02  # 2% spread
            
            option_data.append({
                'timestamp': timestamp,
                'open': price,
                'high': price * 1.05,
                'low': price * 0.95,
                'close': price,
                'bid': price - spread / 2,
                'ask': price + spread / 2,
                'volume': bar.get('volume', 0) // 100  # Scale down
            })
        except (ValueError, ZeroDivisionError):
            continue
    
    return option_data
