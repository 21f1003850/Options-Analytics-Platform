"""Mock broker adapter with realistic simulated data for testing"""

import asyncio
import random
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from .base import (
    IBrokerAdapter,
    OptionContract,
    Order,
    Position,
    OrderType,
    OrderSide,
    OptionType
)


class MockBrokerAdapter(IBrokerAdapter):
    """Mock broker adapter that provides simulated data for testing"""
    
    def __init__(self):
        self._connected = False
        self._positions: List[Position] = []
        self._orders: Dict[str, Order] = {}
        self._order_counter = 0
        self._subscriptions: Dict[str, Callable] = {}
        
    async def connect(self, credentials: Dict[str, Any] = None) -> bool:
        """Simulate connection to broker"""
        await asyncio.sleep(0.1)  # Simulate network delay
        self._connected = True
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from mock broker"""
        self._connected = False
        self._subscriptions.clear()
    
    async def get_option_chain(
        self, 
        underlying: str, 
        expiry: Optional[datetime] = None
    ) -> List[OptionContract]:
        """
        Generate a realistic mock option chain
        
        Args:
            underlying: Underlying symbol
            expiry: Optional specific expiry date
            
        Returns:
            List of mock option contracts with realistic Greeks
        """
        if not self._connected:
            raise RuntimeError("Not connected to broker")
        
        # Simulate current underlying price
        underlying_price = self._get_mock_underlying_price(underlying)
        
        # Generate expiry dates if not specified
        if expiry:
            expiries = [expiry]
        else:
            today = datetime.now()
            expiries = [
                today + timedelta(days=7),   # Weekly
                today + timedelta(days=14),  # 2 weeks
                today + timedelta(days=30),  # Monthly
                today + timedelta(days=60),  # 2 months
                today + timedelta(days=90),  # Quarterly
            ]
        
        # Generate strikes around current price
        strikes = self._generate_strikes(underlying_price)
        
        contracts = []
        for exp in expiries:
            days_to_expiry = (exp - datetime.now()).days
            
            for strike in strikes:
                # Calculate Greeks for both calls and puts
                for opt_type in [OptionType.CALL, OptionType.PUT]:
                    contract = self._generate_mock_contract(
                        underlying=underlying,
                        strike=strike,
                        expiry=exp,
                        option_type=opt_type,
                        underlying_price=underlying_price,
                        days_to_expiry=days_to_expiry
                    )
                    contracts.append(contract)
        
        return contracts
    
    def _get_mock_underlying_price(self, symbol: str) -> float:
        """Get mock underlying price based on symbol"""
        # Assign different base prices to common symbols
        prices = {
            "SPY": 450.0,
            "QQQ": 380.0,
            "AAPL": 175.0,
            "MSFT": 380.0,
            "TSLA": 250.0,
            "NVDA": 500.0,
            "AMZN": 145.0,
            "GOOGL": 140.0,
        }
        return prices.get(symbol, 100.0)
    
    def _generate_strikes(self, underlying_price: float) -> List[float]:
        """Generate strike prices around the underlying price"""
        # Generate strikes from 80% to 120% of underlying
        strikes = []
        strike_increment = 5 if underlying_price < 100 else 10
        
        start_strike = int(underlying_price * 0.8 / strike_increment) * strike_increment
        end_strike = int(underlying_price * 1.2 / strike_increment) * strike_increment
        
        current = start_strike
        while current <= end_strike:
            strikes.append(float(current))
            current += strike_increment
        
        return strikes
    
    def _generate_mock_contract(
        self,
        underlying: str,
        strike: float,
        expiry: datetime,
        option_type: OptionType,
        underlying_price: float,
        days_to_expiry: int
    ) -> OptionContract:
        """Generate a single mock option contract with realistic Greeks"""
        
        # Calculate moneyness
        moneyness = underlying_price / strike
        
        # Mock implied volatility (higher for OTM options - volatility smile)
        if option_type == OptionType.CALL:
            iv = 0.25 + abs(1 - moneyness) * 0.15
        else:
            iv = 0.25 + abs(1 - moneyness) * 0.20  # Higher IV for puts (skew)
        
        # Add term structure component (higher IV for shorter term)
        iv += max(0, (30 - days_to_expiry) / 200)
        
        # Intrinsic value
        if option_type == OptionType.CALL:
            intrinsic = max(0, underlying_price - strike)
        else:
            intrinsic = max(0, strike - underlying_price)
        
        # Extrinsic value (simplified)
        time_value = iv * underlying_price * (days_to_expiry / 365) ** 0.5
        
        # Price
        price = intrinsic + time_value
        bid = price * 0.98
        ask = price * 1.02
        
        # Mock Greeks (simplified but realistic)
        if option_type == OptionType.CALL:
            delta = 0.5 + (underlying_price - strike) / underlying_price * 0.5
            delta = max(0.01, min(0.99, delta))
        else:
            delta = -0.5 + (strike - underlying_price) / underlying_price * 0.5
            delta = max(-0.99, min(-0.01, delta))
        
        gamma = 0.01 * (1 - abs(moneyness - 1) * 2)
        gamma = max(0.001, gamma)
        
        theta = -price / days_to_expiry if days_to_expiry > 0 else -0.05
        vega = underlying_price * 0.01 * (days_to_expiry / 365) ** 0.5
        rho = 0.01 * strike * (days_to_expiry / 365)
        if option_type == OptionType.PUT:
            rho = -rho
        
        # Mock volume and open interest
        volume = random.randint(0, 5000)
        open_interest = random.randint(100, 50000)
        
        # Generate option symbol
        exp_str = expiry.strftime("%y%m%d")
        type_str = "C" if option_type == OptionType.CALL else "P"
        strike_str = f"{int(strike * 1000):08d}"
        symbol = f"{underlying}{exp_str}{type_str}{strike_str}"
        
        return OptionContract(
            symbol=symbol,
            underlying=underlying,
            strike=strike,
            expiry=expiry,
            option_type=option_type,
            bid=round(bid, 2),
            ask=round(ask, 2),
            last=round(price, 2),
            volume=volume,
            open_interest=open_interest,
            implied_volatility=round(iv, 4),
            delta=round(delta, 4),
            gamma=round(gamma, 4),
            theta=round(theta, 4),
            vega=round(vega, 4),
            rho=round(rho, 4)
        )
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get mock quote for a symbol"""
        if not self._connected:
            raise RuntimeError("Not connected to broker")
        
        # Generate mock quote
        base_price = self._get_mock_underlying_price(symbol)
        price = base_price + random.uniform(-5, 5)
        
        return {
            "symbol": symbol,
            "bid": round(price - 0.05, 2),
            "ask": round(price + 0.05, 2),
            "last": round(price, 2),
            "volume": random.randint(1000000, 10000000),
            "timestamp": datetime.now().isoformat()
        }
    
    async def place_order(self, order: Order) -> str:
        """Place a mock order"""
        if not self._connected:
            raise RuntimeError("Not connected to broker")
        
        self._order_counter += 1
        order_id = f"MOCK{self._order_counter:06d}"
        self._orders[order_id] = order
        
        # Simulate order fill and update positions
        await asyncio.sleep(0.05)
        
        return order_id
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a mock order"""
        if not self._connected:
            raise RuntimeError("Not connected to broker")
        
        if order_id in self._orders:
            del self._orders[order_id]
            return True
        return False
    
    async def get_positions(self) -> List[Position]:
        """Get mock positions"""
        if not self._connected:
            raise RuntimeError("Not connected to broker")
        
        return self._positions
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime, 
        timeframe: str = "1d"
    ) -> List[Dict]:
        """Generate mock historical data"""
        if not self._connected:
            raise RuntimeError("Not connected to broker")
        
        # Generate mock OHLCV data
        data = []
        current = start
        base_price = self._get_mock_underlying_price(symbol)
        
        # Determine time delta based on timeframe
        if timeframe == "1m":
            delta = timedelta(minutes=1)
        elif timeframe == "5m":
            delta = timedelta(minutes=5)
        elif timeframe == "1h":
            delta = timedelta(hours=1)
        else:  # 1d default
            delta = timedelta(days=1)
        
        price = base_price
        while current <= end:
            # Random walk with drift
            change = random.uniform(-0.02, 0.025)
            price = price * (1 + change)
            
            high = price * (1 + random.uniform(0, 0.01))
            low = price * (1 - random.uniform(0, 0.01))
            close = price * (1 + random.uniform(-0.005, 0.005))
            
            data.append({
                "timestamp": current.isoformat(),
                "open": round(price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": random.randint(1000000, 10000000)
            })
            
            price = close
            current += delta
        
        return data
    
    async def subscribe_realtime(
        self, 
        symbols: List[str], 
        callback: Callable
    ) -> None:
        """Subscribe to mock real-time updates"""
        if not self._connected:
            raise RuntimeError("Not connected to broker")
        
        for symbol in symbols:
            self._subscriptions[symbol] = callback
        
        # Start mock data stream (in a real implementation, this would be event-driven)
        asyncio.create_task(self._mock_data_stream(symbols, callback))
    
    async def _mock_data_stream(self, symbols: List[str], callback: Callable):
        """Generate mock streaming data"""
        while self._connected and symbols:
            for symbol in symbols:
                if symbol in self._subscriptions:
                    quote = await self.get_quote(symbol)
                    await callback(quote)
            await asyncio.sleep(1)  # Update every second
