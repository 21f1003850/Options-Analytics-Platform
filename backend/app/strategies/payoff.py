"""Payoff diagram calculations for options strategies"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from .builder import StrategyBuilder, StrategyLeg, ActionType, OptionType


def calculate_payoff(
    strategy: StrategyBuilder,
    price_range: Optional[Tuple[float, float]] = None,
    num_points: int = 100
) -> Dict[str, any]:
    """
    Calculate payoff diagram for a strategy
    
    Args:
        strategy: StrategyBuilder instance
        price_range: Optional (min_price, max_price). Auto-calculated if None
        num_points: Number of price points to calculate
        
    Returns:
        Dictionary with payoff data
    """
    if not strategy.legs:
        return {
            "prices": np.array([]),
            "payoffs_at_expiry": np.array([]),
            "payoffs_now": np.array([]),
            "breakevens": [],
            "max_profit": None,
            "max_loss": None
        }
    
    # Determine price range if not provided
    if price_range is None:
        strikes = [leg.strike for leg in strategy.legs]
        min_strike = min(strikes)
        max_strike = max(strikes)
        strike_range = max_strike - min_strike
        
        if strike_range == 0:
            strike_range = min_strike * 0.2
        
        price_min = min_strike - strike_range
        price_max = max_strike + strike_range
    else:
        price_min, price_max = price_range
    
    # Generate price points
    prices = np.linspace(price_min, price_max, num_points)
    
    # Calculate payoff at expiration for each price
    payoffs_at_expiry = np.zeros(num_points)
    
    for leg in strategy.legs:
        leg_payoffs = _calculate_leg_payoff(leg, prices, at_expiry=True)
        payoffs_at_expiry += leg_payoffs
    
    # Calculate current payoff (if Greeks available - for now, simplified)
    payoffs_now = payoffs_at_expiry.copy()  # Simplified - same as expiry
    
    # Calculate breakeven points
    breakevens = calculate_breakevens(strategy, price_range=(price_min, price_max))
    
    # Calculate max profit and loss
    max_profit_loss = calculate_max_profit_loss(strategy)
    
    return {
        "prices": prices.tolist(),
        "payoffs_at_expiry": payoffs_at_expiry.tolist(),
        "payoffs_now": payoffs_now.tolist(),
        "breakevens": breakevens,
        "max_profit": max_profit_loss["max_profit"],
        "max_loss": max_profit_loss["max_loss"],
        "net_cost": strategy.get_net_cost()
    }


def _calculate_leg_payoff(
    leg: StrategyLeg,
    prices: np.ndarray,
    at_expiry: bool = True
) -> np.ndarray:
    """
    Calculate payoff for a single leg
    
    Args:
        leg: Strategy leg
        prices: Array of underlying prices
        at_expiry: If True, calculate value at expiration
        
    Returns:
        Array of payoffs
    """
    multiplier = 100  # Standard options multiplier
    
    # Intrinsic value at each price
    if leg.option_type == OptionType.CALL:
        intrinsic = np.maximum(prices - leg.strike, 0)
    else:  # PUT
        intrinsic = np.maximum(leg.strike - prices, 0)
    
    # Value of the option position
    if leg.action == ActionType.BUY:
        # Long position: intrinsic - premium paid
        payoff = (intrinsic - leg.premium) * leg.quantity * multiplier
    else:  # SELL
        # Short position: premium received - intrinsic
        payoff = (leg.premium - intrinsic) * leg.quantity * multiplier
    
    return payoff


def calculate_breakevens(
    strategy: StrategyBuilder,
    price_range: Optional[Tuple[float, float]] = None,
    tolerance: float = 0.01
) -> List[float]:
    """
    Calculate breakeven points for a strategy
    
    Args:
        strategy: StrategyBuilder instance
        price_range: Price range to search
        tolerance: Tolerance for zero crossing
        
    Returns:
        List of breakeven prices
    """
    if not strategy.legs:
        return []
    
    # Determine search range
    if price_range is None:
        strikes = [leg.strike for leg in strategy.legs]
        min_strike = min(strikes)
        max_strike = max(strikes)
        strike_range = max_strike - min_strike
        
        if strike_range == 0:
            strike_range = min_strike * 0.2
        
        price_min = min_strike - strike_range
        price_max = max_strike + strike_range
    else:
        price_min, price_max = price_range
    
    # Sample the payoff function densely
    prices = np.linspace(price_min, price_max, 1000)
    payoffs = np.zeros(len(prices))
    
    for leg in strategy.legs:
        leg_payoffs = _calculate_leg_payoff(leg, prices, at_expiry=True)
        payoffs += leg_payoffs
    
    # Find zero crossings
    breakevens = []
    for i in range(len(payoffs) - 1):
        # Check if payoff crosses zero
        if payoffs[i] * payoffs[i + 1] < 0:
            # Linear interpolation to find exact breakeven
            be = prices[i] - payoffs[i] * (prices[i + 1] - prices[i]) / (payoffs[i + 1] - payoffs[i])
            breakevens.append(float(be))
        elif abs(payoffs[i]) < tolerance:
            breakevens.append(float(prices[i]))
    
    # Remove duplicates (within tolerance)
    if breakevens:
        unique_breakevens = [breakevens[0]]
        for be in breakevens[1:]:
            if abs(be - unique_breakevens[-1]) > tolerance:
                unique_breakevens.append(be)
        return unique_breakevens
    
    return []


def calculate_max_profit_loss(
    strategy: StrategyBuilder,
    price_range: Optional[Tuple[float, float]] = None
) -> Dict[str, Optional[float]]:
    """
    Calculate maximum profit and loss for a strategy
    
    Args:
        strategy: StrategyBuilder instance
        price_range: Price range to analyze
        
    Returns:
        Dictionary with max_profit and max_loss (None if unlimited)
    """
    if not strategy.legs:
        return {"max_profit": None, "max_loss": None}
    
    # Determine if strategy has unlimited profit or loss potential
    has_naked_call = any(
        leg.action == ActionType.SELL and leg.option_type == OptionType.CALL
        for leg in strategy.legs
    )
    
    has_naked_put = any(
        leg.action == ActionType.SELL and leg.option_type == OptionType.PUT
        for leg in strategy.legs
    )
    
    # Check if naked positions are covered
    call_sells = sum(
        leg.quantity for leg in strategy.legs
        if leg.action == ActionType.SELL and leg.option_type == OptionType.CALL
    )
    call_buys = sum(
        leg.quantity for leg in strategy.legs
        if leg.action == ActionType.BUY and leg.option_type == OptionType.CALL
    )
    
    put_sells = sum(
        leg.quantity for leg in strategy.legs
        if leg.action == ActionType.SELL and leg.option_type == OptionType.PUT
    )
    put_buys = sum(
        leg.quantity for leg in strategy.legs
        if leg.action == ActionType.BUY and leg.option_type == OptionType.PUT
    )
    
    # Unlimited profit if net long calls uncovered
    unlimited_profit = (call_buys > call_sells)
    
    # Unlimited loss if net short calls uncovered
    unlimited_loss = (call_sells > call_buys)
    
    # Sample payoff function
    strikes = [leg.strike for leg in strategy.legs]
    min_strike = min(strikes)
    max_strike = max(strikes)
    
    if price_range:
        price_min, price_max = price_range
    else:
        price_min = 0  # Worst case for puts
        price_max = max_strike * 3  # Sample high for calls
    
    prices = np.linspace(price_min, price_max, 1000)
    payoffs = np.zeros(len(prices))
    
    for leg in strategy.legs:
        leg_payoffs = _calculate_leg_payoff(leg, prices, at_expiry=True)
        payoffs += leg_payoffs
    
    # Find max profit and loss from sampled points
    max_profit_sampled = float(np.max(payoffs))
    max_loss_sampled = float(np.min(payoffs))
    
    # Determine actual max/min considering unlimited scenarios
    if unlimited_profit:
        max_profit = None  # Unlimited
    else:
        max_profit = max_profit_sampled
    
    if unlimited_loss:
        max_loss = None  # Unlimited
    else:
        max_loss = max_loss_sampled
    
    return {
        "max_profit": max_profit,
        "max_loss": max_loss,
        "unlimited_profit": unlimited_profit,
        "unlimited_loss": unlimited_loss
    }


def calculate_profit_probability(
    strategy: StrategyBuilder,
    underlying_price: float,
    volatility: float,
    days_to_expiry: int
) -> Dict[str, float]:
    """
    Estimate probability of profit using Monte Carlo simulation
    
    Args:
        strategy: StrategyBuilder instance
        underlying_price: Current underlying price
        volatility: Implied volatility (annualized)
        days_to_expiry: Days until expiration
        
    Returns:
        Dictionary with probability metrics
    """
    # Simplified calculation using normal distribution
    # (For more accuracy, use Monte Carlo in backtesting module)
    
    breakevens = calculate_breakevens(strategy)
    
    if not breakevens:
        return {
            "probability_of_profit": 0.5,
            "probability_of_max_profit": 0.0,
            "probability_of_max_loss": 0.0
        }
    
    # Calculate expected move
    time_factor = np.sqrt(days_to_expiry / 365)
    expected_move = underlying_price * volatility * time_factor
    
    # For simplicity, assume normal distribution
    # P(profit) depends on where breakevens are relative to current price
    
    # This is a simplified estimation
    if len(breakevens) == 1:
        be = breakevens[0]
        # One breakeven - estimate based on distance
        distance = abs(be - underlying_price)
        z_score = distance / expected_move
        
        from scipy.stats import norm
        prob_profit = 1 - norm.cdf(z_score)
    else:
        # Multiple breakevens - more complex
        # Rough estimate: probability price stays between breakevens
        lower_be = min(breakevens)
        upper_be = max(breakevens)
        
        from scipy.stats import norm
        z_lower = (lower_be - underlying_price) / expected_move
        z_upper = (upper_be - underlying_price) / expected_move
        
        prob_profit = norm.cdf(z_upper) - norm.cdf(z_lower)
    
    return {
        "probability_of_profit": float(np.clip(prob_profit, 0, 1)),
        "expected_move": float(expected_move),
        "breakevens": breakevens
    }
