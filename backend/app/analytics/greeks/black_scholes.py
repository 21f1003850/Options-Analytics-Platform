"""Black-Scholes option pricing and Greeks calculations"""

import math
from typing import Tuple, Dict
from scipy.stats import norm


def black_scholes_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
    q: float = 0.0
) -> float:
    """
    Calculate Black-Scholes option price
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate (annual)
        sigma: Volatility (annual)
        option_type: 'call' or 'put'
        q: Dividend yield (annual, default 0)
        
    Returns:
        Option price
    """
    if T <= 0:
        # At expiration
        if option_type.lower() == "call":
            return max(0, S - K)
        else:
            return max(0, K - S)
    
    if sigma <= 0:
        raise ValueError("Volatility must be positive")
    
    # Calculate d1 and d2
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    if option_type.lower() == "call":
        price = S * math.exp(-q * T) * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    elif option_type.lower() == "put":
        price = K * math.exp(-r * T) * norm.cdf(-d2) - S * math.exp(-q * T) * norm.cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    
    return price


def _calculate_d1_d2(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0
) -> Tuple[float, float]:
    """Helper function to calculate d1 and d2"""
    if T <= 0:
        return 0.0, 0.0
    
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return d1, d2


def calculate_delta(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
    q: float = 0.0
) -> float:
    """
    Calculate option delta
    
    Delta measures the rate of change of option price with respect to the underlying price.
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility
        option_type: 'call' or 'put'
        q: Dividend yield
        
    Returns:
        Delta value (call: 0 to 1, put: -1 to 0)
    """
    if T <= 0:
        if option_type.lower() == "call":
            return 1.0 if S > K else 0.0
        else:
            return -1.0 if S < K else 0.0
    
    d1, _ = _calculate_d1_d2(S, K, T, r, sigma, q)
    
    if option_type.lower() == "call":
        delta = math.exp(-q * T) * norm.cdf(d1)
    elif option_type.lower() == "put":
        delta = -math.exp(-q * T) * norm.cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    
    return delta


def calculate_gamma(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0
) -> float:
    """
    Calculate option gamma
    
    Gamma measures the rate of change of delta with respect to the underlying price.
    Gamma is the same for calls and puts.
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility
        q: Dividend yield
        
    Returns:
        Gamma value
    """
    if T <= 0:
        return 0.0
    
    d1, _ = _calculate_d1_d2(S, K, T, r, sigma, q)
    
    gamma = (math.exp(-q * T) * norm.pdf(d1)) / (S * sigma * math.sqrt(T))
    return gamma


def calculate_theta(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
    q: float = 0.0
) -> float:
    """
    Calculate option theta
    
    Theta measures the rate of change of option price with respect to time.
    Returns daily theta (divide by 365).
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility
        option_type: 'call' or 'put'
        q: Dividend yield
        
    Returns:
        Theta value (typically negative, per day)
    """
    if T <= 0:
        return 0.0
    
    d1, d2 = _calculate_d1_d2(S, K, T, r, sigma, q)
    
    # Common term
    term1 = -(S * math.exp(-q * T) * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
    
    if option_type.lower() == "call":
        term2 = q * S * math.exp(-q * T) * norm.cdf(d1)
        term3 = -r * K * math.exp(-r * T) * norm.cdf(d2)
        theta = term1 + term2 + term3
    elif option_type.lower() == "put":
        term2 = -q * S * math.exp(-q * T) * norm.cdf(-d1)
        term3 = r * K * math.exp(-r * T) * norm.cdf(-d2)
        theta = term1 + term2 + term3
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    
    # Convert to daily theta
    return theta / 365


def calculate_vega(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0
) -> float:
    """
    Calculate option vega
    
    Vega measures the rate of change of option price with respect to volatility.
    Vega is the same for calls and puts.
    Returns vega per 1% change in volatility.
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility
        q: Dividend yield
        
    Returns:
        Vega value (per 1% volatility change)
    """
    if T <= 0:
        return 0.0
    
    d1, _ = _calculate_d1_d2(S, K, T, r, sigma, q)
    
    vega = S * math.exp(-q * T) * norm.pdf(d1) * math.sqrt(T)
    
    # Return vega per 1% change
    return vega / 100


def calculate_rho(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
    q: float = 0.0
) -> float:
    """
    Calculate option rho
    
    Rho measures the rate of change of option price with respect to interest rate.
    Returns rho per 1% change in interest rate.
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility
        option_type: 'call' or 'put'
        q: Dividend yield
        
    Returns:
        Rho value (per 1% interest rate change)
    """
    if T <= 0:
        return 0.0
    
    _, d2 = _calculate_d1_d2(S, K, T, r, sigma, q)
    
    if option_type.lower() == "call":
        rho = K * T * math.exp(-r * T) * norm.cdf(d2)
    elif option_type.lower() == "put":
        rho = -K * T * math.exp(-r * T) * norm.cdf(-d2)
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    
    # Return rho per 1% change
    return rho / 100


def calculate_all_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
    q: float = 0.0
) -> Dict[str, float]:
    """
    Calculate all Greeks at once (more efficient than separate calls)
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility
        option_type: 'call' or 'put'
        q: Dividend yield
        
    Returns:
        Dictionary with all Greeks: price, delta, gamma, theta, vega, rho
    """
    price = black_scholes_price(S, K, T, r, sigma, option_type, q)
    delta = calculate_delta(S, K, T, r, sigma, option_type, q)
    gamma = calculate_gamma(S, K, T, r, sigma, q)
    theta = calculate_theta(S, K, T, r, sigma, option_type, q)
    vega = calculate_vega(S, K, T, r, sigma, q)
    rho = calculate_rho(S, K, T, r, sigma, option_type, q)
    
    return {
        "price": price,
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho
    }
