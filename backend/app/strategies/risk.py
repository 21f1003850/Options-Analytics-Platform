"""Risk management calculations for options strategies"""

import numpy as np
from typing import Dict, Optional, List
from scipy.stats import norm
from .builder import StrategyBuilder, ActionType, OptionType


def calculate_var(
    strategy: StrategyBuilder,
    underlying_price: float,
    volatility: float,
    confidence_level: float = 0.95,
    time_horizon_days: int = 1
) -> Dict[str, float]:
    """
    Calculate Value at Risk (VaR) for a strategy
    
    VaR estimates the potential loss in value over a given time period
    at a given confidence level.
    
    Args:
        strategy: StrategyBuilder instance
        underlying_price: Current underlying price
        volatility: Implied volatility (annualized)
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        time_horizon_days: Time horizon in days
        
    Returns:
        Dictionary with VaR metrics
    """
    from .greeks_aggregator import aggregate_greeks
    
    # Get portfolio Greeks
    greeks = aggregate_greeks(strategy)
    
    # Calculate time scaling
    time_factor = np.sqrt(time_horizon_days / 252)
    
    # Expected move at confidence level
    z_score = norm.ppf(1 - confidence_level)
    expected_move = abs(z_score) * volatility * underlying_price * time_factor
    
    # Estimate P&L change using delta-gamma approximation
    delta = greeks["delta"]
    gamma = greeks["gamma"]
    
    # Worst case move (downside for long delta, upside for short delta)
    if delta >= 0:
        worst_move = -expected_move
    else:
        worst_move = expected_move
    
    # P&L from delta and gamma
    delta_pnl = delta * worst_move
    gamma_pnl = 0.5 * gamma * (worst_move ** 2)
    
    var_estimate = abs(delta_pnl + gamma_pnl)
    
    # Also consider theta decay
    theta_pnl = greeks["theta"] * time_horizon_days
    
    return {
        "var": var_estimate,
        "confidence_level": confidence_level,
        "time_horizon_days": time_horizon_days,
        "expected_move": expected_move,
        "worst_case_pnl": delta_pnl + gamma_pnl + theta_pnl,
        "var_as_pct_of_capital": (var_estimate / abs(strategy.get_net_cost()) * 100) if strategy.get_net_cost() != 0 else 0
    }


def estimate_margin(
    strategy: StrategyBuilder,
    underlying_price: float,
    margin_type: str = "reg_t"
) -> Dict[str, float]:
    """
    Estimate margin requirements for a strategy
    
    Note: This is a simplified estimation. Actual margin requirements
    depend on broker and account type.
    
    Args:
        strategy: StrategyBuilder instance
        underlying_price: Current underlying price
        margin_type: 'reg_t' (Regulation T) or 'portfolio' (portfolio margin)
        
    Returns:
        Dictionary with margin estimates
    """
    total_margin = 0.0
    maintenance_margin = 0.0
    
    # Group legs by type
    short_calls = []
    short_puts = []
    long_calls = []
    long_puts = []
    
    for leg in strategy.legs:
        if leg.action == ActionType.SELL:
            if leg.option_type == OptionType.CALL:
                short_calls.append(leg)
            else:
                short_puts.append(leg)
        else:  # BUY
            if leg.option_type == OptionType.CALL:
                long_calls.append(leg)
            else:
                long_puts.append(leg)
    
    multiplier = 100
    
    if margin_type == "reg_t":
        # Regulation T margin calculations (simplified)
        
        # Naked short calls: 20% of underlying + premium - OTM amount
        for leg in short_calls:
            premium_received = leg.premium * leg.quantity * multiplier
            otm_amount = max(0, leg.strike - underlying_price) * leg.quantity * multiplier
            margin = max(
                0.20 * underlying_price * leg.quantity * multiplier + premium_received - otm_amount,
                premium_received + 0.10 * underlying_price * leg.quantity * multiplier
            )
            total_margin += margin
        
        # Naked short puts: 20% of underlying + premium - OTM amount
        for leg in short_puts:
            premium_received = leg.premium * leg.quantity * multiplier
            otm_amount = max(0, underlying_price - leg.strike) * leg.quantity * multiplier
            margin = max(
                0.20 * leg.strike * leg.quantity * multiplier + premium_received - otm_amount,
                premium_received + 0.10 * leg.strike * leg.quantity * multiplier
            )
            total_margin += margin
        
        # Long options: full premium paid (no margin, but ties up capital)
        for leg in long_calls + long_puts:
            cost = leg.premium * leg.quantity * multiplier
            total_margin += cost
        
        # Check for defined risk spreads (reduced margin)
        if short_calls and long_calls:
            # Potential call spread
            short_strikes = sorted([leg.strike for leg in short_calls])
            long_strikes = sorted([leg.strike for leg in long_calls])
            
            # If there's a long call above a short call, it's a spread
            for short_strike in short_strikes:
                covering_longs = [s for s in long_strikes if s > short_strike]
                if covering_longs:
                    # Spread margin is width - credit
                    width = (min(covering_longs) - short_strike) * multiplier
                    credit = sum(leg.premium * leg.quantity * multiplier for leg in short_calls if leg.strike == short_strike)
                    spread_margin = width - credit
                    # Reduce total margin (simplified)
                    total_margin = min(total_margin, spread_margin)
        
        if short_puts and long_puts:
            # Potential put spread
            short_strikes = sorted([leg.strike for leg in short_puts], reverse=True)
            long_strikes = sorted([leg.strike for leg in long_puts], reverse=True)
            
            for short_strike in short_strikes:
                covering_longs = [s for s in long_strikes if s < short_strike]
                if covering_longs:
                    width = (short_strike - max(covering_longs)) * multiplier
                    credit = sum(leg.premium * leg.quantity * multiplier for leg in short_puts if leg.strike == short_strike)
                    spread_margin = width - credit
                    total_margin = min(total_margin, spread_margin)
    
    else:  # portfolio margin
        # Portfolio margin is risk-based (simplified estimation)
        # Estimate max loss across price range
        from .payoff import calculate_max_profit_loss
        
        max_pl = calculate_max_profit_loss(strategy)
        max_loss = max_pl.get("max_loss")
        
        if max_loss is not None:
            # Portfolio margin is roughly the max loss
            total_margin = abs(max_loss)
        else:
            # Unlimited risk - fall back to reg T
            total_margin = estimate_margin(strategy, underlying_price, "reg_t")["total_margin"]
    
    # Maintenance margin is typically 75% of initial (simplified)
    maintenance_margin = total_margin * 0.75
    
    return {
        "total_margin": total_margin,
        "maintenance_margin": maintenance_margin,
        "margin_type": margin_type,
        "buying_power_effect": -total_margin  # Negative since it reduces buying power
    }


def calculate_risk_reward_ratio(
    strategy: StrategyBuilder
) -> Dict[str, Optional[float]]:
    """
    Calculate risk/reward ratio for a strategy
    
    Args:
        strategy: StrategyBuilder instance
        
    Returns:
        Dictionary with risk/reward metrics
    """
    from .payoff import calculate_max_profit_loss
    
    max_pl = calculate_max_profit_loss(strategy)
    max_profit = max_pl.get("max_profit")
    max_loss = max_pl.get("max_loss")
    
    if max_profit is None or max_loss is None:
        return {
            "risk_reward_ratio": None,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "undefined": True
        }
    
    if max_loss == 0:
        risk_reward_ratio = None
    else:
        risk_reward_ratio = abs(max_profit / max_loss)
    
    return {
        "risk_reward_ratio": risk_reward_ratio,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "undefined": False
    }


def assess_strategy_risk_profile(
    strategy: StrategyBuilder,
    underlying_price: float,
    volatility: float
) -> Dict[str, any]:
    """
    Comprehensive risk assessment for a strategy
    
    Args:
        strategy: StrategyBuilder instance
        underlying_price: Current underlying price
        volatility: Implied volatility
        
    Returns:
        Dictionary with comprehensive risk profile
    """
    from .greeks_aggregator import aggregate_greeks, calculate_portfolio_risk_metrics
    from .payoff import calculate_breakevens, calculate_max_profit_loss
    
    # Get Greeks
    greeks = aggregate_greeks(strategy)
    
    # Get risk metrics
    risk_metrics = calculate_portfolio_risk_metrics(strategy, underlying_price, volatility)
    
    # Get max profit/loss
    max_pl = calculate_max_profit_loss(strategy)
    
    # Get breakevens
    breakevens = calculate_breakevens(strategy)
    
    # Get VaR
    var_95 = calculate_var(strategy, underlying_price, volatility, 0.95, 1)
    
    # Get margin
    margin = estimate_margin(strategy, underlying_price, "reg_t")
    
    # Get risk/reward
    risk_reward = calculate_risk_reward_ratio(strategy)
    
    # Classify risk profile
    if max_pl.get("unlimited_loss"):
        risk_level = "high"
    elif max_pl.get("max_loss") and abs(max_pl["max_loss"]) > abs(strategy.get_net_cost()) * 3:
        risk_level = "high"
    elif max_pl.get("max_loss") and abs(max_pl["max_loss"]) > abs(strategy.get_net_cost()):
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Directional bias
    if greeks["delta"] > 50:
        bias = "bullish"
    elif greeks["delta"] < -50:
        bias = "bearish"
    else:
        bias = "neutral"
    
    return {
        "risk_level": risk_level,
        "directional_bias": bias,
        "greeks": greeks,
        "risk_metrics": risk_metrics,
        "max_profit": max_pl.get("max_profit"),
        "max_loss": max_pl.get("max_loss"),
        "breakevens": breakevens,
        "var_95_1day": var_95["var"],
        "margin_requirement": margin["total_margin"],
        "risk_reward_ratio": risk_reward.get("risk_reward_ratio"),
        "capital_at_risk": abs(strategy.get_net_cost())
    }
