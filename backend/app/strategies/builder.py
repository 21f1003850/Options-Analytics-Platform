"""Multi-leg strategy builder and validator"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class ActionType(Enum):
    """Buy or Sell action"""
    BUY = "buy"
    SELL = "sell"


class OptionType(Enum):
    """Call or Put"""
    CALL = "call"
    PUT = "put"


@dataclass
class StrategyLeg:
    """Represents one leg of an options strategy"""
    action: ActionType  # BUY or SELL
    option_type: OptionType  # CALL or PUT
    strike: float
    expiry: datetime
    quantity: int
    premium: float  # Price per contract
    
    # Greeks (optional, for analysis)
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None
    
    @property
    def cost(self) -> float:
        """Calculate cost/credit for this leg"""
        multiplier = 100  # Standard options contract multiplier
        if self.action == ActionType.BUY:
            return -self.premium * self.quantity * multiplier
        else:  # SELL
            return self.premium * self.quantity * multiplier
    
    def __repr__(self) -> str:
        return f"{self.action.value.upper()} {self.quantity} {self.option_type.value.upper()} @ {self.strike} exp {self.expiry.strftime('%Y-%m-%d')}"


class StrategyBuilder:
    """Builder for multi-leg options strategies"""
    
    def __init__(self, name: str = "Custom Strategy"):
        self.name = name
        self.legs: List[StrategyLeg] = []
        self.underlying_price: Optional[float] = None
    
    def add_leg(
        self,
        action: str,
        option_type: str,
        strike: float,
        expiry: datetime,
        quantity: int = 1,
        premium: float = 0.0,
        delta: Optional[float] = None,
        gamma: Optional[float] = None,
        theta: Optional[float] = None,
        vega: Optional[float] = None,
        rho: Optional[float] = None
    ) -> 'StrategyBuilder':
        """
        Add a leg to the strategy
        
        Args:
            action: 'buy' or 'sell'
            option_type: 'call' or 'put'
            strike: Strike price
            expiry: Expiration date
            quantity: Number of contracts
            premium: Option premium
            delta, gamma, theta, vega, rho: Greeks
            
        Returns:
            Self for method chaining
        """
        leg = StrategyLeg(
            action=ActionType(action.lower()),
            option_type=OptionType(option_type.lower()),
            strike=strike,
            expiry=expiry,
            quantity=quantity,
            premium=premium,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho
        )
        self.legs.append(leg)
        return self
    
    def set_underlying_price(self, price: float) -> 'StrategyBuilder':
        """Set the underlying price for analysis"""
        self.underlying_price = price
        return self
    
    def remove_leg(self, index: int) -> 'StrategyBuilder':
        """Remove a leg by index"""
        if 0 <= index < len(self.legs):
            self.legs.pop(index)
        return self
    
    def clear(self) -> 'StrategyBuilder':
        """Clear all legs"""
        self.legs = []
        return self
    
    def get_net_cost(self) -> float:
        """
        Calculate net cost/credit of the strategy
        
        Returns:
            Negative for debit (paid), positive for credit (received)
        """
        return sum(leg.cost for leg in self.legs)
    
    def get_leg_count(self) -> int:
        """Get number of legs in the strategy"""
        return len(self.legs)
    
    def validate(self) -> Dict[str, any]:
        """
        Validate the strategy structure
        
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        if not self.legs:
            errors.append("Strategy has no legs")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        # Check for negative quantities
        for i, leg in enumerate(self.legs):
            if leg.quantity <= 0:
                errors.append(f"Leg {i}: Quantity must be positive")
            
            if leg.strike <= 0:
                errors.append(f"Leg {i}: Strike must be positive")
            
            if leg.premium < 0:
                errors.append(f"Leg {i}: Premium cannot be negative")
        
        # Check for mixed expirations (warning, not error)
        expiries = set(leg.expiry for leg in self.legs)
        if len(expiries) > 1:
            warnings.append("Strategy contains legs with different expirations")
        
        # Check for past expirations
        now = datetime.now()
        for i, leg in enumerate(self.legs):
            if leg.expiry < now:
                errors.append(f"Leg {i}: Expiration date is in the past")
        
        # Check total cost
        net_cost = self.get_net_cost()
        if abs(net_cost) == 0 and len(self.legs) > 1:
            warnings.append("Net cost is zero - verify premiums are set correctly")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "leg_count": len(self.legs),
            "net_cost": net_cost
        }
    
    def to_dict(self) -> Dict:
        """Convert strategy to dictionary"""
        return {
            "name": self.name,
            "underlying_price": self.underlying_price,
            "legs": [
                {
                    "action": leg.action.value,
                    "option_type": leg.option_type.value,
                    "strike": leg.strike,
                    "expiry": leg.expiry.isoformat(),
                    "quantity": leg.quantity,
                    "premium": leg.premium,
                    "delta": leg.delta,
                    "gamma": leg.gamma,
                    "theta": leg.theta,
                    "vega": leg.vega,
                    "rho": leg.rho,
                    "cost": leg.cost
                }
                for leg in self.legs
            ],
            "net_cost": self.get_net_cost()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyBuilder':
        """Create strategy from dictionary"""
        strategy = cls(name=data.get("name", "Custom Strategy"))
        strategy.underlying_price = data.get("underlying_price")
        
        for leg_data in data.get("legs", []):
            strategy.add_leg(
                action=leg_data["action"],
                option_type=leg_data["option_type"],
                strike=leg_data["strike"],
                expiry=datetime.fromisoformat(leg_data["expiry"]),
                quantity=leg_data["quantity"],
                premium=leg_data["premium"],
                delta=leg_data.get("delta"),
                gamma=leg_data.get("gamma"),
                theta=leg_data.get("theta"),
                vega=leg_data.get("vega"),
                rho=leg_data.get("rho")
            )
        
        return strategy
    
    def __repr__(self) -> str:
        legs_str = "\n  ".join(str(leg) for leg in self.legs)
        net_cost = self.get_net_cost()
        cost_type = "DEBIT" if net_cost < 0 else "CREDIT"
        return f"{self.name}:\n  {legs_str}\n  Net {cost_type}: ${abs(net_cost):.2f}"
