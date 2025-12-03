"""Alpaca adapter stub

This is a stub implementation. To use Alpaca, you need to:
1. Install alpaca-trade-api: pip install alpaca-trade-api
2. Sign up at https://alpaca.markets/
3. Get your API key and secret
4. Implement the methods below using Alpaca API

Documentation:
- Alpaca API: https://alpaca.markets/docs/
- Python SDK: https://github.com/alpacahq/alpaca-trade-api-python

Note: Alpaca primarily supports stock and crypto trading.
Options support is limited and requires special approval.
"""

from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
from .base import (
    IBrokerAdapter,
    OptionContract,
    Order,
    Position
)


class AlpacaAdapter(IBrokerAdapter):
    """Alpaca adapter (stub implementation)"""
    
    def __init__(self):
        self._connected = False
        # In a real implementation:
        # from alpaca_trade_api import REST, Stream
        # self.api = None
        # self.stream = None
    
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to Alpaca
        
        Credentials should include:
        - api_key: str
        - secret_key: str
        - base_url: str (paper: https://paper-api.alpaca.markets, live: https://api.alpaca.markets)
        
        Example:
            await adapter.connect({
                'api_key': 'your_api_key',
                'secret_key': 'your_secret_key',
                'base_url': 'https://paper-api.alpaca.markets'
            })
        """
        raise NotImplementedError(
            "Alpaca adapter not implemented. "
            "Install alpaca-trade-api and implement this method."
        )
    
    async def disconnect(self) -> None:
        """Disconnect from Alpaca"""
        raise NotImplementedError("Alpaca adapter not implemented")
    
    async def get_option_chain(
        self, 
        underlying: str, 
        expiry: Optional[datetime] = None
    ) -> List[OptionContract]:
        """
        Get option chain from Alpaca
        
        NOTE: Options trading on Alpaca requires special approval.
        Check: https://alpaca.markets/docs/trading/options/
        
        Implementation hint:
        1. Use get_option_contracts() to get available contracts
        2. Filter by underlying and expiry
        3. Get quotes for each contract
        4. Calculate Greeks (not provided by Alpaca)
        """
        raise NotImplementedError(
            "Alpaca adapter not implemented. "
            "Note: Options support requires special approval."
        )
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get quote from Alpaca
        
        Implementation hint:
        Use api.get_latest_trade(symbol) or api.get_latest_quote(symbol)
        """
        raise NotImplementedError("Alpaca adapter not implemented")
    
    async def place_order(self, order: Order) -> str:
        """
        Place order with Alpaca
        
        Implementation hint:
        Use api.submit_order() with:
        - symbol: symbol
        - qty: quantity
        - side: 'buy' or 'sell'
        - type: 'market', 'limit', 'stop', 'stop_limit'
        - time_in_force: 'day', 'gtc', 'ioc', 'fok'
        """
        raise NotImplementedError("Alpaca adapter not implemented")
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel order with Alpaca
        
        Implementation hint:
        Use api.cancel_order(order_id)
        """
        raise NotImplementedError("Alpaca adapter not implemented")
    
    async def get_positions(self) -> List[Position]:
        """
        Get positions from Alpaca
        
        Implementation hint:
        Use api.list_positions()
        """
        raise NotImplementedError("Alpaca adapter not implemented")
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime, 
        timeframe: str = "1d"
    ) -> List[Dict]:
        """
        Get historical data from Alpaca
        
        Implementation hint:
        Use api.get_bars() with:
        - symbol: symbol
        - timeframe: TimeFrame object ('1Min', '5Min', '1Hour', '1Day')
        - start: start datetime
        - end: end datetime
        """
        raise NotImplementedError("Alpaca adapter not implemented")
    
    async def subscribe_realtime(
        self, 
        symbols: List[str], 
        callback: Callable
    ) -> None:
        """
        Subscribe to real-time data from Alpaca
        
        Implementation hint:
        Use Stream class for WebSocket streaming:
        1. Create Stream instance
        2. Subscribe to trades/quotes with @stream.on_trade or @stream.on_quote
        3. Start stream with stream.run()
        
        See: https://alpaca.markets/docs/market-data/streaming/
        """
        raise NotImplementedError("Alpaca adapter not implemented")
