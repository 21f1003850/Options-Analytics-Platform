"""Unit tests for Black-Scholes Greeks calculations"""

import pytest
import math
from app.analytics.greeks.black_scholes import (
    black_scholes_price,
    calculate_delta,
    calculate_gamma,
    calculate_theta,
    calculate_vega,
    calculate_rho,
    calculate_all_greeks
)


class TestBlackScholesPrice:
    """Test Black-Scholes option pricing"""
    
    def test_call_option_price(self):
        """Test call option pricing with known values"""
        price = black_scholes_price(
            S=100,
            K=100,
            T=1.0,
            r=0.05,
            sigma=0.25,
            option_type="call",
            q=0.0
        )
        
        # ATM call with 1 year to expiration should be positive
        assert price > 0
        # Price should be reasonable (not too high or low)
        assert 5 < price < 20
    
    def test_put_option_price(self):
        """Test put option pricing"""
        price = black_scholes_price(
            S=100,
            K=100,
            T=1.0,
            r=0.05,
            sigma=0.25,
            option_type="put",
            q=0.0
        )
        
        assert price > 0
        assert 5 < price < 20
    
    def test_put_call_parity(self):
        """Test put-call parity: C - P = S - K*e^(-rT)"""
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.25
        
        call_price = black_scholes_price(S, K, T, r, sigma, "call")
        put_price = black_scholes_price(S, K, T, r, sigma, "put")
        
        lhs = call_price - put_price
        rhs = S - K * math.exp(-r * T)
        
        # Should be approximately equal (within small tolerance)
        assert abs(lhs - rhs) < 0.01
    
    def test_itm_call(self):
        """Test in-the-money call"""
        price = black_scholes_price(
            S=110,  # Stock at 110
            K=100,  # Strike at 100
            T=1.0,
            r=0.05,
            sigma=0.25,
            option_type="call"
        )
        
        # ITM call should be worth at least intrinsic value
        intrinsic = 110 - 100
        assert price >= intrinsic
    
    def test_otm_call(self):
        """Test out-of-the-money call"""
        price = black_scholes_price(
            S=90,   # Stock at 90
            K=100,  # Strike at 100
            T=1.0,
            r=0.05,
            sigma=0.25,
            option_type="call"
        )
        
        # OTM call should have positive time value
        assert price > 0
        # But less than ATM call
        atm_price = black_scholes_price(100, 100, 1.0, 0.05, 0.25, "call")
        assert price < atm_price


class TestDelta:
    """Test delta calculation"""
    
    def test_atm_call_delta(self):
        """ATM call delta should be around 0.5"""
        delta = calculate_delta(
            S=100, K=100, T=1.0, r=0.05, sigma=0.25, option_type="call"
        )
        
        # ATM call delta should be close to 0.5
        assert 0.45 < delta < 0.55
    
    def test_atm_put_delta(self):
        """ATM put delta should be around -0.5"""
        delta = calculate_delta(
            S=100, K=100, T=1.0, r=0.05, sigma=0.25, option_type="put"
        )
        
        # ATM put delta should be close to -0.5
        assert -0.55 < delta < -0.45
    
    def test_itm_call_delta(self):
        """Deep ITM call delta approaches 1"""
        delta = calculate_delta(
            S=150, K=100, T=1.0, r=0.05, sigma=0.25, option_type="call"
        )
        
        # Deep ITM call should have high delta
        assert delta > 0.9
    
    def test_otm_call_delta(self):
        """Deep OTM call delta approaches 0"""
        delta = calculate_delta(
            S=50, K=100, T=1.0, r=0.05, sigma=0.25, option_type="call"
        )
        
        # Deep OTM call should have low delta
        assert delta < 0.1


class TestGamma:
    """Test gamma calculation"""
    
    def test_gamma_positive(self):
        """Gamma should always be positive"""
        gamma = calculate_gamma(
            S=100, K=100, T=1.0, r=0.05, sigma=0.25
        )
        
        assert gamma > 0
    
    def test_atm_highest_gamma(self):
        """ATM options have highest gamma"""
        gamma_atm = calculate_gamma(S=100, K=100, T=1.0, r=0.05, sigma=0.25)
        gamma_itm = calculate_gamma(S=120, K=100, T=1.0, r=0.05, sigma=0.25)
        gamma_otm = calculate_gamma(S=80, K=100, T=1.0, r=0.05, sigma=0.25)
        
        assert gamma_atm > gamma_itm
        assert gamma_atm > gamma_otm


class TestTheta:
    """Test theta calculation"""
    
    def test_theta_negative(self):
        """Theta for long options should be negative (time decay)"""
        theta = calculate_theta(
            S=100, K=100, T=1.0, r=0.05, sigma=0.25, option_type="call"
        )
        
        # Theta should be negative for long options
        assert theta < 0


class TestVega:
    """Test vega calculation"""
    
    def test_vega_positive(self):
        """Vega should be positive for long options"""
        vega = calculate_vega(
            S=100, K=100, T=1.0, r=0.05, sigma=0.25
        )
        
        assert vega > 0
    
    def test_longer_expiry_higher_vega(self):
        """Longer dated options have higher vega"""
        vega_1y = calculate_vega(S=100, K=100, T=1.0, r=0.05, sigma=0.25)
        vega_1m = calculate_vega(S=100, K=100, T=1/12, r=0.05, sigma=0.25)
        
        assert vega_1y > vega_1m


class TestAllGreeks:
    """Test combined Greeks calculation"""
    
    def test_calculate_all_greeks(self):
        """Test that all Greeks are calculated together"""
        greeks = calculate_all_greeks(
            S=100, K=100, T=1.0, r=0.05, sigma=0.25, option_type="call"
        )
        
        # Check all Greeks are present
        assert "price" in greeks
        assert "delta" in greeks
        assert "gamma" in greeks
        assert "theta" in greeks
        assert "vega" in greeks
        assert "rho" in greeks
        
        # Check values are reasonable
        assert greeks["price"] > 0
        assert 0 < greeks["delta"] < 1
        assert greeks["gamma"] > 0
        assert greeks["theta"] < 0
        assert greeks["vega"] > 0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_zero_time_to_expiry(self):
        """Test behavior at expiration"""
        price = black_scholes_price(
            S=110, K=100, T=0, r=0.05, sigma=0.25, option_type="call"
        )
        
        # At expiration, price should equal intrinsic value
        assert price == 10.0
    
    def test_invalid_volatility(self):
        """Test that negative volatility raises error"""
        with pytest.raises(ValueError):
            black_scholes_price(
                S=100, K=100, T=1.0, r=0.05, sigma=-0.25, option_type="call"
            )
    
    def test_invalid_option_type(self):
        """Test that invalid option type raises error"""
        with pytest.raises(ValueError):
            black_scholes_price(
                S=100, K=100, T=1.0, r=0.05, sigma=0.25, option_type="invalid"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
