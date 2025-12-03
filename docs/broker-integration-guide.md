# Broker Integration Guide

This guide explains how to integrate new brokers into the Options Analytics Platform.

## Overview

The platform uses the **Adapter Pattern** to provide a unified interface across different brokers. All brokers must implement the `IBrokerAdapter` interface defined in `backend/app/brokers/base.py`.

## Quick Start

### 1. Create a New Adapter File

Create a new file in `backend/app/brokers/` named after your broker (e.g., `my_broker_adapter.py`).

### 2. Implement the Interface

```python
from .base import IBrokerAdapter, OptionContract, Order, Position
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime

class MyBrokerAdapter(IBrokerAdapter):
    def __init__(self):
        self._connected = False
        # Initialize broker-specific client here
    
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Connect to broker API"""
        # Implement connection logic
        self._connected = True
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from broker"""
        self._connected = False
    
    # Implement all other required methods...
```

### 3. Register with Factory

Update `backend/app/brokers/factory.py`:

```python
from .my_broker_adapter import MyBrokerAdapter

class BrokerFactory:
    _adapters: Dict[str, type] = {
        "mock": MockBrokerAdapter,
        "mybroker": MyBrokerAdapter,  # Add your adapter
    }
```

### 4. Test Your Adapter

```python
# Test script
import asyncio
from app.brokers.factory import BrokerFactory

async def test_broker():
    broker = BrokerFactory.create("mybroker")
    
    # Test connection
    await broker.connect({
        "api_key": "your_key",
        "secret": "your_secret"
    })
    
    # Test option chain
    contracts = await broker.get_option_chain("SPY")
    print(f"Retrieved {len(contracts)} contracts")
    
    await broker.disconnect()

asyncio.run(test_broker())
```

## Interface Reference

### Required Methods

#### 1. `connect(credentials: Dict[str, Any]) -> bool`

**Purpose**: Establish connection to broker API

**Parameters**:
- `credentials`: Dictionary with broker-specific auth info
  - Examples: API key, secret, tokens, username/password

**Returns**: `True` if successful, `False` otherwise

**Example**:
```python
async def connect(self, credentials: Dict[str, Any]) -> bool:
    self.api_key = credentials.get('api_key')
    self.secret = credentials.get('secret')
    
    # Initialize broker client
    self.client = BrokerClient(self.api_key, self.secret)
    
    try:
        await self.client.authenticate()
        self._connected = True
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
```

#### 2. `disconnect() -> None`

**Purpose**: Clean up connection and resources

**Example**:
```python
async def disconnect(self) -> None:
    if self.client:
        await self.client.close()
    self._connected = False
```

#### 3. `get_option_chain(underlying: str, expiry: Optional[datetime]) -> List[OptionContract]`

**Purpose**: Retrieve option chain for an underlying

**Parameters**:
- `underlying`: Stock symbol (e.g., "SPY", "AAPL")
- `expiry`: Optional specific expiration date

**Returns**: List of `OptionContract` objects with full Greeks

**Important**:
- If broker doesn't provide Greeks, calculate them using Black-Scholes
- Include both calls and puts
- Set `open_interest` and `volume` to 0 if unavailable

**Example**:
```python
async def get_option_chain(self, underlying: str, expiry: Optional[datetime] = None) -> List[OptionContract]:
    # Get options from broker API
    raw_options = await self.client.get_options(underlying)
    
    contracts = []
    for opt in raw_options:
        # Convert broker's format to OptionContract
        contract = OptionContract(
            symbol=opt['symbol'],
            underlying=underlying,
            strike=opt['strike'],
            expiry=datetime.fromisoformat(opt['expiration']),
            option_type=OptionType.CALL if opt['type'] == 'call' else OptionType.PUT,
            bid=opt['bid'],
            ask=opt['ask'],
            last=opt['last'],
            volume=opt.get('volume', 0),
            open_interest=opt.get('open_interest', 0),
            implied_volatility=opt.get('iv', 0.25),  # Default if not provided
            delta=opt.get('delta', 0),
            gamma=opt.get('gamma', 0),
            theta=opt.get('theta', 0),
            vega=opt.get('vega', 0),
            rho=opt.get('rho', 0)
        )
        
        contracts.append(contract)
    
    return contracts
```

#### 4. `get_quote(symbol: str) -> Dict[str, Any]`

**Purpose**: Get real-time quote

**Returns**: Dictionary with at minimum:
- `bid`: Bid price
- `ask`: Ask price
- `last`: Last trade price
- `volume`: Volume

**Example**:
```python
async def get_quote(self, symbol: str) -> Dict[str, Any]:
    quote = await self.client.get_quote(symbol)
    
    return {
        "symbol": symbol,
        "bid": quote['bid'],
        "ask": quote['ask'],
        "last": quote['last'],
        "volume": quote['volume'],
        "timestamp": datetime.now().isoformat()
    }
```

#### 5. `place_order(order: Order) -> str`

**Purpose**: Place a trading order

**Returns**: Order ID from broker

**Example**:
```python
async def place_order(self, order: Order) -> str:
    broker_order = {
        'symbol': order.symbol,
        'side': order.side.value,
        'quantity': order.quantity,
        'order_type': order.order_type.value,
        'limit_price': order.limit_price
    }
    
    response = await self.client.submit_order(**broker_order)
    return response['order_id']
```

#### 6. `cancel_order(order_id: str) -> bool`

**Purpose**: Cancel an existing order

**Example**:
```python
async def cancel_order(self, order_id: str) -> bool:
    try:
        await self.client.cancel(order_id)
        return True
    except Exception:
        return False
```

#### 7. `get_positions() -> List[Position]`

**Purpose**: Get current account positions

**Example**:
```python
async def get_positions(self) -> List[Position]:
    raw_positions = await self.client.get_positions()
    
    positions = []
    for pos in raw_positions:
        position = Position(
            symbol=pos['symbol'],
            quantity=pos['quantity'],
            avg_cost=pos['avg_price'],
            current_price=pos['current_price'],
            unrealized_pnl=pos['unrealized_pnl']
        )
        positions.append(position)
    
    return positions
```

#### 8. `get_historical_data(symbol, start, end, timeframe) -> List[Dict]`

**Purpose**: Get OHLCV historical data

**Parameters**:
- `timeframe`: '1m', '5m', '1h', '1d', etc.

**Returns**: List of dictionaries with:
- `timestamp`: Datetime
- `open`, `high`, `low`, `close`: Prices
- `volume`: Volume

**Example**:
```python
async def get_historical_data(self, symbol: str, start: datetime, end: datetime, timeframe: str = "1d") -> List[Dict]:
    bars = await self.client.get_bars(
        symbol=symbol,
        start=start,
        end=end,
        timeframe=timeframe
    )
    
    return [
        {
            'timestamp': bar['time'],
            'open': bar['o'],
            'high': bar['h'],
            'low': bar['l'],
            'close': bar['c'],
            'volume': bar['v']
        }
        for bar in bars
    ]
```

#### 9. `subscribe_realtime(symbols, callback) -> None`

**Purpose**: Subscribe to real-time updates

**Example**:
```python
async def subscribe_realtime(self, symbols: List[str], callback: Callable) -> None:
    # Set up WebSocket or streaming connection
    async def on_quote(quote_data):
        await callback({
            'symbol': quote_data['symbol'],
            'price': quote_data['price'],
            'timestamp': quote_data['time']
        })
    
    await self.client.stream.subscribe_quotes(symbols, on_quote)
```

## Common Patterns

### Handling Missing Greeks

If your broker doesn't provide Greeks, calculate them:

```python
from app.analytics.greeks.black_scholes import calculate_all_greeks

async def get_option_chain(self, underlying: str, expiry: Optional[datetime] = None):
    # Get options without Greeks
    raw_options = await self.client.get_options(underlying)
    
    # Get underlying price
    quote = await self.get_quote(underlying)
    S = quote['last']
    
    contracts = []
    for opt in raw_options:
        # Calculate Greeks
        T = (opt['expiry'] - datetime.now()).days / 365
        greeks = calculate_all_greeks(
            S=S,
            K=opt['strike'],
            T=T,
            r=0.05,  # Risk-free rate
            sigma=opt.get('iv', 0.25),
            option_type='call' if opt['type'] == 'C' else 'put'
        )
        
        # Create contract with calculated Greeks
        contract = OptionContract(
            # ... other fields ...
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            rho=greeks['rho']
        )
        contracts.append(contract)
    
    return contracts
```

### Error Handling

Always handle broker-specific errors gracefully:

```python
async def get_option_chain(self, underlying: str, expiry: Optional[datetime] = None):
    try:
        contracts = await self.client.get_options(underlying)
        return self._convert_contracts(contracts)
    except BrokerAPIError as e:
        print(f"Broker API error: {e}")
        return []  # Return empty list instead of raising
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise  # Re-raise unexpected errors
```

### Rate Limiting

Implement rate limiting to respect broker limits:

```python
from asyncio import sleep
from datetime import datetime, timedelta

class MyBrokerAdapter(IBrokerAdapter):
    def __init__(self):
        self._last_request = {}
        self._min_interval = 0.1  # 100ms between requests
    
    async def _rate_limit(self, endpoint: str):
        """Enforce rate limiting per endpoint"""
        now = datetime.now()
        if endpoint in self._last_request:
            elapsed = (now - self._last_request[endpoint]).total_seconds()
            if elapsed < self._min_interval:
                await sleep(self._min_interval - elapsed)
        self._last_request[endpoint] = now
    
    async def get_quote(self, symbol: str):
        await self._rate_limit('quote')
        return await self.client.get_quote(symbol)
```

## Testing Your Adapter

### Unit Tests

```python
import pytest
from app.brokers.factory import BrokerFactory

@pytest.mark.asyncio
async def test_connection():
    broker = BrokerFactory.create("mybroker")
    connected = await broker.connect({
        "api_key": "test_key"
    })
    assert connected is True
    await broker.disconnect()

@pytest.mark.asyncio
async def test_option_chain():
    broker = BrokerFactory.create("mybroker")
    await broker.connect({})
    
    contracts = await broker.get_option_chain("SPY")
    
    assert len(contracts) > 0
    assert all(hasattr(c, 'delta') for c in contracts)
    
    await broker.disconnect()
```

### Integration Tests

Test with real broker API (use paper trading):

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_broker():
    broker = BrokerFactory.create("mybroker")
    
    # Use test credentials
    await broker.connect({
        "api_key": os.getenv("TEST_API_KEY"),
        "secret": os.getenv("TEST_SECRET")
    })
    
    # Test basic operations
    quote = await broker.get_quote("SPY")
    assert quote['last'] > 0
    
    contracts = await broker.get_option_chain("SPY")
    assert len(contracts) > 0
    
    await broker.disconnect()
```

## Broker-Specific Examples

### Interactive Brokers (IBKR)

```python
# Uses ib_insync library
from ib_insync import IB, Stock, Option

class IBKRAdapter(IBrokerAdapter):
    def __init__(self):
        self.ib = IB()
    
    async def connect(self, credentials):
        self.ib.connect(
            host=credentials.get('host', '127.0.0.1'),
            port=credentials.get('port', 7497),
            clientId=credentials.get('client_id', 1)
        )
        return self.ib.isConnected()
```

### Zerodha Kite

```python
# Uses kiteconnect library
from kiteconnect import KiteConnect

class ZerodhaAdapter(IBrokerAdapter):
    def __init__(self):
        self.kite = None
    
    async def connect(self, credentials):
        self.kite = KiteConnect(api_key=credentials['api_key'])
        self.kite.set_access_token(credentials['access_token'])
        return True
```

## Best Practices

1. **Always validate inputs** before making broker API calls
2. **Cache expensive calls** (e.g., option chains) using Redis
3. **Log all API interactions** for debugging
4. **Handle connection timeouts** gracefully
5. **Test with paper trading** before live integration
6. **Document broker-specific quirks** in code comments
7. **Version check** if broker API changes frequently
8. **Implement retry logic** for transient failures

## Troubleshooting

### Common Issues

**Issue**: "Connection timeout"
- **Solution**: Check network, firewall, broker status

**Issue**: "Invalid credentials"
- **Solution**: Verify API keys, check expiration

**Issue**: "Rate limit exceeded"
- **Solution**: Implement rate limiting, reduce request frequency

**Issue**: "Missing Greeks"
- **Solution**: Calculate using Black-Scholes as shown above

## Support

For help with broker integration:
1. Check existing adapter implementations
2. Review broker's API documentation
3. Open an issue on GitHub

---

Happy integrating! 🚀
