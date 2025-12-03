"""Portfolio Greeks aggregation and what-if analysis"""

import numpy as np
from typing import Dict, List, Optional
from .builder import StrategyBuilder, StrategyLeg, ActionType


def aggregate_greeks(strategy: StrategyBuilder) -> Dict[str, float]:
    """
    Aggregate Greeks for entire strategy
    
    Args:
        strategy: StrategyBuilder instance
        
    Returns:
        Dictionary with aggregated Greeks
    """
    total_delta = 0.0
    total_gamma = 0.0
    total_theta = 0.0
    total_vega = 0.0
    total_rho = 0.0
    
    multiplier = 100  # Options contract multiplier
    
    for leg in strategy.legs:
        # Get leg Greeks (default to 0 if not set)
        delta = leg.delta if leg.delta is not None else 0.0
        gamma = leg.gamma if leg.gamma is not None else 0.0
        theta = leg.theta if leg.theta is not None else 0.0
        vega = leg.vega if leg.vega is not None else 0.0
        rho = leg.rho if leg.rho is not None else 0.0
        
        # Sign adjustment based on position
        sign = 1 if leg.action == ActionType.BUY else -1
        
        # Aggregate (weighted by quantity and multiplier)
        total_delta += sign * delta * leg.quantity * multiplier
        total_gamma += sign * gamma * leg.quantity * multiplier
        total_theta += sign * theta * leg.quantity * multiplier
        total_vega += sign * vega * leg.quantity * multiplier
        total_rho += sign * rho * leg.quantity * multiplier
    
    return {
        "delta": total_delta,
        "gamma": total_gamma,
        "theta": total_theta,
        "vega": total_vega,
        "rho": total_rho,
        "net_delta_dollars": total_delta * (strategy.underlying_price or 1)
    }


def whatif_analysis(
    strategy: StrategyBuilder,
    underlying_price: float,
    scenarios: Optional[List[Dict[str, float]]] = None
) -> List[Dict[str, any]]:
    """
    Perform what-if analysis on strategy
    
    Args:
        strategy: StrategyBuilder instance
        underlying_price: Current underlying price
        scenarios: List of scenario dictionaries with keys:
                   - price_change_pct: % change in underlying
                   - iv_change: absolute change in IV
                   - days_passed: days until expiration
                   
    Returns:
        List of scenario results
    """
    if scenarios is None:
        # Default scenarios
        scenarios = [
            {"price_change_pct": -10, "iv_change": 0.05, "days_passed": 0},
            {"price_change_pct": -5, "iv_change": 0, "days_passed": 0},
            {"price_change_pct": 0, "iv_change": 0, "days_passed": 7},
            {"price_change_pct": 5, "iv_change": 0, "days_passed": 0},
            {"price_change_pct": 10, "iv_change": -0.05, "days_passed": 0},
        ]
    
    greeks = aggregate_greeks(strategy)
    results = []
    
    for scenario in scenarios:
        price_change_pct = scenario.get("price_change_pct", 0)
        iv_change = scenario.get("iv_change", 0)
        days_passed = scenario.get("days_passed", 0)
        
        # Calculate new underlying price
        new_price = underlying_price * (1 + price_change_pct / 100)
        price_change = new_price - underlying_price
        
        # Estimate P&L using Greeks (first-order approximation)
        delta_pnl = greeks["delta"] * price_change
        gamma_pnl = 0.5 * greeks["gamma"] * (price_change ** 2)
        theta_pnl = greeks["theta"] * days_passed
        vega_pnl = greeks["vega"] * iv_change * 100  # Vega per 1% IV change
        
        total_pnl = delta_pnl + gamma_pnl + theta_pnl + vega_pnl
        
        results.append({
            "scenario": scenario,
            "new_price": new_price,
            "price_change": price_change,
            "delta_pnl": delta_pnl,
            "gamma_pnl": gamma_pnl,
            "theta_pnl": theta_pnl,
            "vega_pnl": vega_pnl,
            "total_pnl": total_pnl,
            "total_pnl_pct": (total_pnl / abs(strategy.get_net_cost()) * 100) if strategy.get_net_cost() != 0 else 0
        })
    
    return results


def calculate_portfolio_risk_metrics(
    strategy: StrategyBuilder,
    underlying_price: float,
    volatility: float
) -> Dict[str, float]:
    """
    Calculate risk metrics for the portfolio
    
    Args:
        strategy: StrategyBuilder instance
        underlying_price: Current underlying price
        volatility: Implied volatility
        
    Returns:
        Dictionary with risk metrics
    """
    greeks = aggregate_greeks(strategy)
    
    # Delta-adjusted exposure
    delta_exposure = abs(greeks["delta"] * underlying_price)
    
    # Gamma risk (potential delta change for 1% move)
    one_pct_move = underlying_price * 0.01
    gamma_risk = abs(greeks["gamma"] * one_pct_move)
    
    # Theta decay (daily P&L from time decay)
    daily_theta = greeks["theta"]
    
    # Vega risk (P&L change for 1% IV move)
    vega_risk = abs(greeks["vega"])
    
    # Estimate daily volatility
    daily_vol = volatility / np.sqrt(252)
    expected_daily_move = underlying_price * daily_vol
    
    # Expected daily P&L range (1 std dev)
    daily_pnl_from_move = abs(greeks["delta"]) * expected_daily_move
    
    return {
        "delta_exposure": delta_exposure,
        "gamma_risk": gamma_risk,
        "daily_theta": daily_theta,
        "vega_risk": vega_risk,
        "expected_daily_move": expected_daily_move,
        "expected_daily_pnl_range": daily_pnl_from_move,
        "net_position_delta": greeks["delta"]
    }


def analyze_greek_contributions(
    strategy: StrategyBuilder
) -> List[Dict[str, any]]:
    """
    Analyze individual leg contributions to portfolio Greeks
    
    Args:
        strategy: StrategyBuilder instance
        
    Returns:
        List of leg contributions
    """
    multiplier = 100
    contributions = []
    
    for i, leg in enumerate(strategy.legs):
        sign = 1 if leg.action == ActionType.BUY else -1
        
        delta = (leg.delta or 0) * sign * leg.quantity * multiplier
        gamma = (leg.gamma or 0) * sign * leg.quantity * multiplier
        theta = (leg.theta or 0) * sign * leg.quantity * multiplier
        vega = (leg.vega or 0) * sign * leg.quantity * multiplier
        rho = (leg.rho or 0) * sign * leg.quantity * multiplier
        
        contributions.append({
            "leg_index": i,
            "leg_description": str(leg),
            "delta_contribution": delta,
            "gamma_contribution": gamma,
            "theta_contribution": theta,
            "vega_contribution": vega,
            "rho_contribution": rho
        })
    
    return contributions


def calculate_position_neutrality(
    strategy: StrategyBuilder,
    threshold: float = 0.1
) -> Dict[str, any]:
    """
    Analyze if strategy is delta/gamma/theta neutral
    
    Args:
        strategy: StrategyBuilder instance
        threshold: Threshold for considering neutral (as fraction)
        
    Returns:
        Dictionary with neutrality analysis
    """
    greeks = aggregate_greeks(strategy)
    
    # Calculate total exposure
    total_delta = abs(greeks["delta"])
    total_gamma = abs(greeks["gamma"])
    total_theta = abs(greeks["theta"])
    total_vega = abs(greeks["vega"])
    
    # Determine neutrality (within threshold)
    delta_neutral = total_delta < threshold * 100  # Within threshold * 100 delta
    gamma_neutral = total_gamma < threshold * 10   # Within threshold * 10 gamma
    theta_neutral = total_theta < threshold * 10   # Within threshold * 10 theta
    vega_neutral = total_vega < threshold * 100    # Within threshold * 100 vega
    
    return {
        "delta_neutral": delta_neutral,
        "gamma_neutral": gamma_neutral,
        "theta_neutral": theta_neutral,
        "vega_neutral": vega_neutral,
        "delta": greeks["delta"],
        "gamma": greeks["gamma"],
        "theta": greeks["theta"],
        "vega": greeks["vega"]
    }


def suggest_adjustments(
    strategy: StrategyBuilder,
    underlying_price: float,
    target: str = "delta_neutral"
) -> Dict[str, any]:
    """
    Suggest adjustments to achieve target Greek profile
    
    Args:
        strategy: StrategyBuilder instance
        underlying_price: Current underlying price
        target: 'delta_neutral', 'gamma_neutral', 'theta_positive', etc.
        
    Returns:
        Dictionary with adjustment suggestions
    """
    greeks = aggregate_greeks(strategy)
    suggestions = []
    
    if target == "delta_neutral":
        current_delta = greeks["delta"]
        
        if abs(current_delta) < 10:
            suggestions.append("Position is already approximately delta neutral")
        elif current_delta > 0:
            # Need to sell delta
            contracts_to_sell = int(abs(current_delta) / 50)  # Rough estimate
            suggestions.append(
                f"Consider selling {contracts_to_sell} ATM call(s) or buying {contracts_to_sell} ATM put(s) to neutralize delta"
            )
        else:
            # Need to buy delta
            contracts_to_buy = int(abs(current_delta) / 50)
            suggestions.append(
                f"Consider buying {contracts_to_buy} ATM call(s) or selling {contracts_to_buy} ATM put(s) to neutralize delta"
            )
    
    elif target == "theta_positive":
        current_theta = greeks["theta"]
        
        if current_theta >= 0:
            suggestions.append("Position already has positive theta (time decay)")
        else:
            suggestions.append(
                "Consider selling options to add positive theta. "
                "Short straddles, strangles, or credit spreads can help."
            )
    
    elif target == "vega_positive":
        current_vega = greeks["vega"]
        
        if current_vega >= 0:
            suggestions.append("Position already has positive vega (benefits from IV increase)")
        else:
            suggestions.append(
                "Consider buying options to add positive vega. "
                "Long straddles, strangles, or debit spreads can help."
            )
    
    return {
        "target": target,
        "current_greeks": greeks,
        "suggestions": suggestions
    }
