"""Implied volatility calculation using numerical methods"""

import math
from typing import Optional
from scipy.stats import norm
from .black_scholes import black_scholes_price


def implied_volatility_newton(
    price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = "call",
    q: float = 0.0,
    initial_guess: float = 0.3,
    max_iterations: int = 100,
    tolerance: float = 1e-6
) -> Optional[float]:
    """
    Calculate implied volatility using Newton-Raphson method
    
    Args:
        price: Market price of the option
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        option_type: 'call' or 'put'
        q: Dividend yield
        initial_guess: Initial guess for volatility
        max_iterations: Maximum number of iterations
        tolerance: Convergence tolerance
        
    Returns:
        Implied volatility, or None if convergence fails
    """
    if T <= 0:
        return None
    
    if price <= 0:
        return None
    
    # Check bounds - option must be worth at least intrinsic value
    if option_type.lower() == "call":
        intrinsic = max(0, S * math.exp(-q * T) - K * math.exp(-r * T))
    else:
        intrinsic = max(0, K * math.exp(-r * T) - S * math.exp(-q * T))
    
    if price < intrinsic:
        return None
    
    sigma = initial_guess
    
    for i in range(max_iterations):
        try:
            # Calculate option price with current sigma
            calculated_price = black_scholes_price(S, K, T, r, sigma, option_type, q)
            
            # Calculate vega (derivative of price with respect to sigma)
            d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            vega = S * math.exp(-q * T) * norm.pdf(d1) * math.sqrt(T)
            
            # Avoid division by zero
            if abs(vega) < 1e-10:
                return None
            
            # Calculate price difference
            price_diff = calculated_price - price
            
            # Check convergence
            if abs(price_diff) < tolerance:
                return sigma
            
            # Newton-Raphson update
            sigma = sigma - price_diff / vega
            
            # Keep sigma positive and reasonable
            sigma = max(0.001, min(5.0, sigma))
            
        except (ValueError, ZeroDivisionError, OverflowError):
            return None
    
    # Did not converge
    return None


def implied_volatility_bisection(
    price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = "call",
    q: float = 0.0,
    min_vol: float = 0.001,
    max_vol: float = 5.0,
    max_iterations: int = 100,
    tolerance: float = 1e-6
) -> Optional[float]:
    """
    Calculate implied volatility using bisection method
    
    More robust than Newton-Raphson but slower. Used as fallback.
    
    Args:
        price: Market price of the option
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        option_type: 'call' or 'put'
        q: Dividend yield
        min_vol: Minimum volatility to search
        max_vol: Maximum volatility to search
        max_iterations: Maximum number of iterations
        tolerance: Convergence tolerance
        
    Returns:
        Implied volatility, or None if not found
    """
    if T <= 0 or price <= 0:
        return None
    
    # Check if price is within possible bounds
    try:
        price_at_min = black_scholes_price(S, K, T, r, min_vol, option_type, q)
        price_at_max = black_scholes_price(S, K, T, r, max_vol, option_type, q)
    except (ValueError, OverflowError):
        return None
    
    # Check if solution exists in range
    if price < price_at_min or price > price_at_max:
        return None
    
    low = min_vol
    high = max_vol
    
    for i in range(max_iterations):
        mid = (low + high) / 2
        
        try:
            calculated_price = black_scholes_price(S, K, T, r, mid, option_type, q)
        except (ValueError, OverflowError):
            return None
        
        if abs(calculated_price - price) < tolerance:
            return mid
        
        if calculated_price < price:
            low = mid
        else:
            high = mid
        
        # Check if range is too small
        if high - low < tolerance:
            return mid
    
    return (low + high) / 2


def calculate_implied_volatility(
    price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = "call",
    q: float = 0.0,
    method: str = "newton"
) -> Optional[float]:
    """
    Calculate implied volatility with automatic fallback
    
    Tries Newton-Raphson first, falls back to bisection if it fails.
    
    Args:
        price: Market price of the option
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        option_type: 'call' or 'put'
        q: Dividend yield
        method: 'newton', 'bisection', or 'auto' (default: 'newton')
        
    Returns:
        Implied volatility, or None if calculation fails
    """
    if method == "bisection":
        return implied_volatility_bisection(price, S, K, T, r, option_type, q)
    
    # Try Newton-Raphson first
    iv = implied_volatility_newton(price, S, K, T, r, option_type, q)
    
    # Fall back to bisection if Newton-Raphson fails
    if iv is None and method == "auto":
        iv = implied_volatility_bisection(price, S, K, T, r, option_type, q)
    
    return iv


def calculate_iv_for_chain(
    option_data: list,
    S: float,
    r: float,
    q: float = 0.0
) -> list:
    """
    Calculate implied volatility for an entire option chain
    
    Args:
        option_data: List of dicts with keys: price, strike, expiry, option_type
        S: Current stock price
        r: Risk-free interest rate
        q: Dividend yield
        
    Returns:
        List of dicts with original data plus 'implied_volatility' field
    """
    results = []
    
    for option in option_data:
        price = option.get('price', option.get('last', option.get('mid')))
        K = option['strike']
        expiry = option['expiry']
        option_type = option['option_type']
        
        # Calculate time to expiration in years
        if isinstance(expiry, str):
            from datetime import datetime
            expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        
        from datetime import datetime
        T = (expiry - datetime.now()).total_seconds() / (365.25 * 24 * 3600)
        
        if T > 0 and price > 0:
            iv = calculate_implied_volatility(price, S, K, T, r, option_type, q, method="auto")
        else:
            iv = None
        
        result = option.copy()
        result['implied_volatility'] = iv
        results.append(result)
    
    return results
