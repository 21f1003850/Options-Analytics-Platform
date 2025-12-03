"""Pydantic models for API request/response schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class OptionTypeEnum(str, Enum):
    CALL = "call"
    PUT = "put"


class OrderSideEnum(str, Enum):
    BUY = "buy"
    SELL = "sell"
    BUY_TO_OPEN = "buy_to_open"
    SELL_TO_CLOSE = "sell_to_close"


# Option Models
class OptionContractResponse(BaseModel):
    symbol: str
    underlying: str
    strike: float
    expiry: datetime
    option_type: OptionTypeEnum
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


class OptionChainRequest(BaseModel):
    underlying: str = Field(..., description="Underlying symbol (e.g., SPY, AAPL)")
    expiry: Optional[datetime] = Field(None, description="Optional specific expiration date")


class OptionChainResponse(BaseModel):
    underlying: str
    underlying_price: Optional[float]
    contracts: List[OptionContractResponse]
    timestamp: datetime


# Volatility Models
class VolatilitySurfaceResponse(BaseModel):
    strikes: List[float]
    expiries: List[int]  # days to expiry
    iv_surface: List[List[float]]
    moneyness: List[float]
    underlying_price: float


class VolatilitySkewResponse(BaseModel):
    x_axis: List[float]
    iv: List[float]
    skew_measure: float
    axis_type: str
    underlying_price: float


class IVTermStructureResponse(BaseModel):
    days_to_expiry: List[int]
    iv: List[float]
    moneyness_target: float


# Open Interest Models
class PCRResponse(BaseModel):
    pcr: Optional[float]
    total_put: int
    total_call: int
    metric: str  # 'oi' or 'volume'
    sentiment: str


class MaxPainResponse(BaseModel):
    max_pain_strike: Optional[float]
    max_pain_value: Optional[float]
    pain_by_strike: Dict[float, float]
    total_call_oi: int
    total_put_oi: int


# Strategy Models
class StrategyLegModel(BaseModel):
    action: str  # 'buy' or 'sell'
    option_type: str  # 'call' or 'put'
    strike: float
    expiry: datetime
    quantity: int = 1
    premium: float = 0.0
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None


class StrategyRequest(BaseModel):
    name: str = "Custom Strategy"
    underlying_price: Optional[float] = None
    legs: List[StrategyLegModel]


class StrategyResponse(BaseModel):
    name: str
    underlying_price: Optional[float]
    legs: List[Dict]
    net_cost: float
    validation: Dict[str, Any]
    greeks: Dict[str, float]


class PayoffRequest(BaseModel):
    strategy: StrategyRequest
    price_range: Optional[List[float]] = None
    num_points: int = 100


class PayoffResponse(BaseModel):
    prices: List[float]
    payoffs_at_expiry: List[float]
    payoffs_now: List[float]
    breakevens: List[float]
    max_profit: Optional[float]
    max_loss: Optional[float]
    net_cost: float


# Backtesting Models
class BacktestConfigModel(BaseModel):
    initial_capital: float = 100000.0
    commission_per_contract: float = 0.65
    slippage_pct: float = 0.01
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BacktestRequest(BaseModel):
    strategy_name: str
    config: BacktestConfigModel
    symbols: List[str]
    # Additional strategy-specific parameters can be added


class BacktestResponse(BaseModel):
    final_equity: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    equity_curve: List[Dict]
    performance: Dict[str, Any]


# Monte Carlo Models
class MonteCarloRequest(BaseModel):
    initial_price: float
    volatility: float
    days_to_expiry: int
    num_simulations: int = 1000
    drift: float = 0.0


class MonteCarloResponse(BaseModel):
    mean_pnl: float
    median_pnl: float
    std_pnl: float
    prob_profit: float
    percentiles: Dict[int, float]
    var_95: float
    cvar_95: float
    min_pnl: float
    max_pnl: float


# WebSocket Models
class WSMessage(BaseModel):
    type: str  # 'subscribe', 'unsubscribe', 'quote', 'trade'
    symbol: Optional[str] = None
    data: Optional[Dict] = None
    timestamp: Optional[datetime] = None


# Health and Status
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]
