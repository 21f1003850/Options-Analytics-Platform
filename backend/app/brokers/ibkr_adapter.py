"""Interactive Brokers (IBKR) adapter stub

This is a stub implementation. To use IBKR, you need to:
1. Install ib_insync: pip install ib_insync
2. Have IBKR TWS or IB Gateway running
3. Configure API settings in TWS/Gateway
4. Implement the methods below using ib_insync API

Documentation:
- ib_insync: https://ib-insync.readthedocs.io/
- IBKR API: https://interactivebrokers.github.io/tws-api/
"""

from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
from .base import (
    IBrokerAdapter,
    OptionContract,
    Order,
    Position
)


class IBKRAdapter(IBrokerAdapter):
    """Interactive Brokers adapter (stub implementation)"""
    
    def __init__(self):
        self._connected = False
        # In a real implementation:
        # from ib_insync import IB
        # self.ib = IB()
    
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to IBKR TWS or IB Gateway
        
        Credentials should include:
        - host: str (default '127.0.0.1')
        - port: int (7497 for TWS paper, 7496 for TWS live, 4002 for Gateway)
        - client_id: int (unique client identifier)
        
        Example:
            await adapter.connect({
                'host': '127.0.0.1',
                'port': 7497,
                'client_id': 1
            })
        """
        raise NotImplementedError(
            "IBKR adapter not implemented. "
            "Install ib_insync and implement this method."
        )
    
    async def disconnect(self) -> None:
        """Disconnect from IBKR"""
        raise NotImplementedError("IBKR adapter not implemented")
    
    async def get_option_chain(
        self, 
        underlying: str, 
        expiry: Optional[datetime] = None
    ) -> List[OptionContract]:
        """
        Get option chain from IBKR
        
        Implementation hint:
        1. Create Contract object for underlying
        2. Use reqSecDefOptParams to get expirations and strikes
        3. For each strike/expiry, create option contracts
        4. Use reqMktData to get market data and Greeks
        """
        raise NotImplementedError("IBKR adapter not implemented")
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote from IBKR"""
        raise NotImplementedError("IBKR adapter not implemented")
    
    async def place_order(self, order: Order) -> str:
        """
        Place order with IBKR
        
        Implementation hint:
        1. Create Contract object
        2. Create Order object with orderType, action, totalQuantity
        3. Use placeOrder method
        4. Return order ID
        """
        raise NotImplementedError("IBKR adapter not implemented")
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order with IBKR"""
        raise NotImplementedError("IBKR adapter not implemented")
    
    async def get_positions(self) -> List[Position]:
        """
        Get positions from IBKR
        
        Implementation hint:
        Use reqPositions or positions() method
        """
        raise NotImplementedError("IBKR adapter not implemented")
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime, 
        timeframe: str = "1d"
    ) -> List[Dict]:
        """
        Get historical data from IBKR
        
        Implementation hint:
        Use reqHistoricalData with appropriate bar size and duration
        """
        raise NotImplementedError("IBKR adapter not implemented")
    
    async def subscribe_realtime(
        self, 
        symbols: List[str], 
        callback: Callable
    ) -> None:
        """
        Subscribe to real-time data from IBKR
        
        Implementation hint:
        Use reqMktData with streaming=True for each symbol
        """
        raise NotImplementedError("IBKR adapter not implemented")
