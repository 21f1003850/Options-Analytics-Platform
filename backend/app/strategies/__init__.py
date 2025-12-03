"""Strategies package initialization"""

from .builder import StrategyBuilder, StrategyLeg
from .templates import (
    long_call, long_put, short_call, short_put,
    bull_call_spread, bear_call_spread,
    bull_put_spread, bear_put_spread,
    long_straddle, short_straddle,
    long_strangle, short_strangle,
    iron_condor, iron_butterfly,
    calendar_spread, diagonal_spread
)
from .payoff import calculate_payoff, calculate_breakevens, calculate_max_profit_loss
from .greeks_aggregator import aggregate_greeks, whatif_analysis
from .risk import calculate_var, estimate_margin

__all__ = [
    "StrategyBuilder",
    "StrategyLeg",
    "long_call",
    "long_put",
    "short_call",
    "short_put",
    "bull_call_spread",
    "bear_call_spread",
    "bull_put_spread",
    "bear_put_spread",
    "long_straddle",
    "short_straddle",
    "long_strangle",
    "short_strangle",
    "iron_condor",
    "iron_butterfly",
    "calendar_spread",
    "diagonal_spread",
    "calculate_payoff",
    "calculate_breakevens",
    "calculate_max_profit_loss",
    "aggregate_greeks",
    "whatif_analysis",
    "calculate_var",
    "estimate_margin"
]
