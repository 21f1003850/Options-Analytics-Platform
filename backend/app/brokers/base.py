"""Abstract base interface for broker adapters"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class OrderType(Enum):
    """Order types supported by brokers"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order sides for trading"""
    BUY = "buy"
    SELL = "sell"
    BUY_TO_OPEN = "buy_to_open"
    SELL_TO_CLOSE = "sell_to_close"


class OptionType(Enum):
    """Option contract types"""
    CALL = "call"
    PUT = "put"


@dataclass
class OptionContract:
    """Represents an option contract with full Greeks"""
    symbol: str
    underlying: str
    strike: float
    expiry: datetime
    option_type: OptionType
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


@dataclass 
class Order:
    """Represents a trading order"""
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    limit_price: Optional[float] = None


@dataclass
class Position:
    """Represents a current position"""
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float
    unrealized_pnl: float


class IBrokerAdapter(ABC):
    """Abstract interface that all broker adapters must implement"""
    
    @abstractmethod
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to the broker API
        
        Args:
            credentials: Dictionary containing broker-specific credentials
            
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the broker API"""
        pass
    
    @abstractmethod
    async def get_option_chain(
        self, 
        underlying: str, 
        expiry: Optional[datetime] = None
    ) -> List[OptionContract]:
        """
        Get option chain for an underlying symbol
        
        Args:
            underlying: The underlying symbol (e.g., 'SPY', 'AAPL')
            expiry: Optional specific expiry date. If None, returns all expirations
            
        Returns:
            List of OptionContract objects
        """
        pass
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote for a symbol
        
        Args:
            symbol: The symbol to quote
            
        Returns:
            Dictionary with quote data (bid, ask, last, volume, etc.)
        """
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> str:
        """
        Place a trading order
        
        Args:
            order: Order object with details
            
        Returns:
            Order ID assigned by the broker
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order
        
        Args:
            order_id: The broker's order ID
            
        Returns:
            True if cancellation successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """
        Get current account positions
        
        Returns:
            List of Position objects
        """
        pass
    
    @abstractmethod
    async def get_historical_data(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime, 
        timeframe: str = "1d"
    ) -> List[Dict]:
        """
        Get historical price data
        
        Args:
            symbol: The symbol to retrieve data for
            start: Start datetime
            end: End datetime
            timeframe: Timeframe (e.g., '1m', '5m', '1h', '1d')
            
        Returns:
            List of dictionaries with OHLCV data
        """
        pass
    
    @abstractmethod
    async def subscribe_realtime(
        self, 
        symbols: List[str], 
        callback: Callable
    ) -> None:
        """
        Subscribe to real-time data updates
        
        Args:
            symbols: List of symbols to subscribe to
            callback: Callback function to receive updates
        """
        pass
