"""Monte Carlo simulation for options strategies"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta


def run_monte_carlo_simulation(
    initial_price: float,
    volatility: float,
    drift: float,
    days: int,
    num_simulations: int = 1000,
    dt: float = 1/252,  # Daily steps
    random_seed: Optional[int] = None
) -> np.ndarray:
    """
    Run Monte Carlo simulation for underlying price paths
    
    Uses Geometric Brownian Motion (GBM)
    
    Args:
        initial_price: Starting price
        volatility: Annual volatility
        drift: Annual drift (expected return)
        days: Number of days to simulate
        num_simulations: Number of simulation paths
        dt: Time step (1/252 for daily)
        random_seed: Optional seed for reproducibility
        
    Returns:
        Array of shape (num_simulations, days+1) with price paths
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    num_steps = days
    
    # Generate random returns
    random_returns = np.random.normal(
        (drift - 0.5 * volatility**2) * dt,
        volatility * np.sqrt(dt),
        size=(num_simulations, num_steps)
    )
    
    # Calculate cumulative returns
    cumulative_returns = np.cumsum(random_returns, axis=1)
    
    # Calculate price paths
    price_paths = initial_price * np.exp(cumulative_returns)
    
    # Add initial price
    price_paths = np.column_stack([np.full(num_simulations, initial_price), price_paths])
    
    return price_paths


def simulate_strategy_outcomes(
    strategy_func: callable,
    initial_price: float,
    volatility: float,
    days_to_expiry: int,
    num_simulations: int = 1000,
    drift: float = 0.0
) -> Dict:
    """
    Simulate outcomes for an options strategy
    
    Args:
        strategy_func: Function that calculates P&L given final price
        initial_price: Current underlying price
        volatility: Implied volatility
        days_to_expiry: Days until expiration
        num_simulations: Number of simulations
        drift: Expected return (default 0 for risk-neutral)
        
    Returns:
        Dictionary with simulation results
    """
    # Run Monte Carlo
    price_paths = run_monte_carlo_simulation(
        initial_price=initial_price,
        volatility=volatility,
        drift=drift,
        days=days_to_expiry,
        num_simulations=num_simulations
    )
    
    # Get final prices
    final_prices = price_paths[:, -1]
    
    # Calculate P&L for each simulation
    pnls = np.array([strategy_func(price) for price in final_prices])
    
    # Calculate statistics
    mean_pnl = np.mean(pnls)
    median_pnl = np.median(pnls)
    std_pnl = np.std(pnls)
    
    # Probability of profit
    prob_profit = np.mean(pnls > 0)
    
    # Percentiles
    percentiles = {
        5: np.percentile(pnls, 5),
        25: np.percentile(pnls, 25),
        50: np.percentile(pnls, 50),
        75: np.percentile(pnls, 75),
        95: np.percentile(pnls, 95)
    }
    
    # Value at Risk (VaR) at 95% confidence
    var_95 = np.percentile(pnls, 5)
    
    # Conditional Value at Risk (CVaR) - expected loss beyond VaR
    cvar_95 = np.mean(pnls[pnls <= var_95])
    
    return {
        'mean_pnl': float(mean_pnl),
        'median_pnl': float(median_pnl),
        'std_pnl': float(std_pnl),
        'prob_profit': float(prob_profit),
        'percentiles': {k: float(v) for k, v in percentiles.items()},
        'var_95': float(var_95),
        'cvar_95': float(cvar_95),
        'min_pnl': float(np.min(pnls)),
        'max_pnl': float(np.max(pnls)),
        'num_simulations': num_simulations,
        'final_prices': final_prices.tolist(),
        'pnls': pnls.tolist()
    }


def simulate_portfolio_var(
    portfolio_value: float,
    positions: Dict[str, Dict],
    volatility: float,
    correlation_matrix: Optional[np.ndarray] = None,
    confidence_level: float = 0.95,
    time_horizon_days: int = 1
) -> Dict:
    """
    Calculate portfolio VaR using Monte Carlo
    
    Args:
        portfolio_value: Current portfolio value
        positions: Dictionary of positions with deltas
        volatility: Portfolio volatility
        correlation_matrix: Optional correlation matrix for multi-asset
        confidence_level: Confidence level for VaR
        time_horizon_days: Time horizon
        
    Returns:
        Dictionary with VaR results
    """
    num_simulations = 10000
    
    # Simulate portfolio returns
    daily_vol = volatility / np.sqrt(252)
    horizon_vol = daily_vol * np.sqrt(time_horizon_days)
    
    # Generate random returns
    returns = np.random.normal(0, horizon_vol, num_simulations)
    
    # Calculate portfolio value changes
    portfolio_changes = portfolio_value * returns
    
    # Calculate VaR
    var_percentile = (1 - confidence_level) * 100
    var = np.percentile(portfolio_changes, var_percentile)
    
    # Calculate CVaR
    cvar = np.mean(portfolio_changes[portfolio_changes <= var])
    
    return {
        'var': float(abs(var)),
        'cvar': float(abs(cvar)),
        'confidence_level': confidence_level,
        'time_horizon_days': time_horizon_days,
        'var_as_pct': float(abs(var) / portfolio_value * 100)
    }


def analyze_strategy_distribution(
    final_prices: List[float],
    pnls: List[float],
    bins: int = 50
) -> Dict:
    """
    Analyze distribution of strategy outcomes
    
    Args:
        final_prices: List of simulated final prices
        pnls: List of corresponding P&Ls
        bins: Number of histogram bins
        
    Returns:
        Dictionary with distribution analysis
    """
    final_prices = np.array(final_prices)
    pnls = np.array(pnls)
    
    # P&L histogram
    pnl_hist, pnl_edges = np.histogram(pnls, bins=bins)
    
    # Price histogram
    price_hist, price_edges = np.histogram(final_prices, bins=bins)
    
    # Calculate skewness and kurtosis
    from scipy.stats import skew, kurtosis
    
    pnl_skew = skew(pnls)
    pnl_kurtosis = kurtosis(pnls)
    
    return {
        'pnl_histogram': {
            'counts': pnl_hist.tolist(),
            'edges': pnl_edges.tolist()
        },
        'price_histogram': {
            'counts': price_hist.tolist(),
            'edges': price_edges.tolist()
        },
        'pnl_skewness': float(pnl_skew),
        'pnl_kurtosis': float(pnl_kurtosis)
    }


def calculate_optimal_position_size(
    strategy_func: callable,
    initial_price: float,
    volatility: float,
    days_to_expiry: int,
    capital: float,
    risk_tolerance: float = 0.02,
    num_simulations: int = 1000
) -> Dict:
    """
    Calculate optimal position size using Monte Carlo
    
    Uses Kelly Criterion or risk-based sizing
    
    Args:
        strategy_func: Strategy P&L function
        initial_price: Current price
        volatility: Volatility
        days_to_expiry: Days to expiration
        capital: Available capital
        risk_tolerance: Maximum % of capital to risk
        num_simulations: Number of simulations
        
    Returns:
        Dictionary with sizing recommendations
    """
    # Run simulation for 1 contract
    sim_results = simulate_strategy_outcomes(
        strategy_func=strategy_func,
        initial_price=initial_price,
        volatility=volatility,
        days_to_expiry=days_to_expiry,
        num_simulations=num_simulations
    )
    
    # Get single contract statistics
    mean_pnl = sim_results['mean_pnl']
    std_pnl = sim_results['std_pnl']
    var_95 = abs(sim_results['var_95'])
    prob_profit = sim_results['prob_profit']
    
    # Risk-based sizing (limit loss to risk_tolerance of capital)
    max_loss_per_contract = var_95
    
    if max_loss_per_contract > 0:
        risk_based_size = int((capital * risk_tolerance) / max_loss_per_contract)
    else:
        risk_based_size = 0
    
    # Kelly Criterion (simplified)
    if std_pnl > 0:
        kelly_fraction = mean_pnl / (std_pnl ** 2)
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
        kelly_size = int((capital * kelly_fraction) / abs(mean_pnl) if mean_pnl != 0 else 0)
    else:
        kelly_size = 0
    
    # Conservative recommendation (use the smaller size)
    recommended_size = min(risk_based_size, kelly_size) if kelly_size > 0 else risk_based_size
    
    return {
        'recommended_size': int(recommended_size),
        'risk_based_size': int(risk_based_size),
        'kelly_size': int(kelly_size),
        'expected_pnl': float(mean_pnl * recommended_size),
        'max_loss_95': float(var_95 * recommended_size),
        'max_loss_pct_of_capital': float(var_95 * recommended_size / capital * 100)
    }
