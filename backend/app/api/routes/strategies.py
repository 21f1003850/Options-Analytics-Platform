"""Strategy builder and analysis API routes"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from ..models import (
    StrategyRequest,
    StrategyResponse,
    PayoffRequest,
    PayoffResponse
)

router = APIRouter()


@router.post("/build", response_model=StrategyResponse)
async def build_strategy(strategy_request: StrategyRequest):
    """
    Build and validate an options strategy
    
    Returns strategy with validation results and aggregated Greeks
    """
    from ..strategies.builder import StrategyBuilder
    from ..strategies.greeks_aggregator import aggregate_greeks
    
    try:
        # Build strategy
        strategy = StrategyBuilder(name=strategy_request.name)
        strategy.set_underlying_price(strategy_request.underlying_price)
        
        for leg in strategy_request.legs:
            strategy.add_leg(
                action=leg.action,
                option_type=leg.option_type,
                strike=leg.strike,
                expiry=leg.expiry,
                quantity=leg.quantity,
                premium=leg.premium,
                delta=leg.delta,
                gamma=leg.gamma,
                theta=leg.theta,
                vega=leg.vega,
                rho=leg.rho
            )
        
        # Validate
        validation = strategy.validate()
        
        # Aggregate Greeks
        greeks = aggregate_greeks(strategy)
        
        # Convert to response
        strategy_dict = strategy.to_dict()
        
        return StrategyResponse(
            name=strategy.name,
            underlying_price=strategy.underlying_price,
            legs=strategy_dict['legs'],
            net_cost=strategy.get_net_cost(),
            validation=validation,
            greeks=greeks
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payoff", response_model=PayoffResponse)
async def calculate_strategy_payoff(payoff_request: PayoffRequest):
    """
    Calculate payoff diagram for a strategy
    
    Returns P&L at different price points and breakeven analysis
    """
    from ..strategies.builder import StrategyBuilder
    from ..strategies.payoff import calculate_payoff
    
    try:
        # Build strategy
        strategy = StrategyBuilder(name=payoff_request.strategy.name)
        strategy.set_underlying_price(payoff_request.strategy.underlying_price)
        
        for leg in payoff_request.strategy.legs:
            strategy.add_leg(
                action=leg.action,
                option_type=leg.option_type,
                strike=leg.strike,
                expiry=leg.expiry,
                quantity=leg.quantity,
                premium=leg.premium,
                delta=leg.delta,
                gamma=leg.gamma,
                theta=leg.theta,
                vega=leg.vega,
                rho=leg.rho
            )
        
        # Calculate payoff
        price_range = tuple(payoff_request.price_range) if payoff_request.price_range else None
        
        payoff_data = calculate_payoff(
            strategy,
            price_range=price_range,
            num_points=payoff_request.num_points
        )
        
        return PayoffResponse(**payoff_data)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze")
async def analyze_strategy(strategy_request: StrategyRequest):
    """
    Comprehensive strategy analysis
    
    Returns Greeks, risk metrics, and probability analysis
    """
    from ..strategies.builder import StrategyBuilder
    from ..strategies.risk import assess_strategy_risk_profile
    
    try:
        # Build strategy
        strategy = StrategyBuilder(name=strategy_request.name)
        strategy.set_underlying_price(strategy_request.underlying_price)
        
        for leg in strategy_request.legs:
            strategy.add_leg(
                action=leg.action,
                option_type=leg.option_type,
                strike=leg.strike,
                expiry=leg.expiry,
                quantity=leg.quantity,
                premium=leg.premium,
                delta=leg.delta,
                gamma=leg.gamma,
                theta=leg.theta,
                vega=leg.vega,
                rho=leg.rho
            )
        
        # Calculate days to expiry (use nearest expiry)
        if strategy.legs:
            nearest_expiry = min(leg.expiry for leg in strategy.legs)
            days_to_expiry = (nearest_expiry - datetime.now()).days
        else:
            days_to_expiry = 30
        
        # Assess risk profile
        underlying_price = strategy_request.underlying_price or 100.0
        volatility = 0.25  # Default volatility
        
        risk_profile = assess_strategy_risk_profile(
            strategy,
            underlying_price,
            volatility
        )
        
        return risk_profile
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates")
async def get_strategy_templates():
    """Get list of pre-built strategy templates"""
    templates = [
        {
            "name": "Long Call",
            "description": "Bullish strategy with unlimited upside",
            "category": "Directional",
            "risk_level": "Medium"
        },
        {
            "name": "Bull Call Spread",
            "description": "Moderately bullish with defined risk",
            "category": "Directional",
            "risk_level": "Low"
        },
        {
            "name": "Iron Condor",
            "description": "Neutral strategy for range-bound markets",
            "category": "Neutral",
            "risk_level": "Medium"
        },
        {
            "name": "Long Straddle",
            "description": "Profit from large moves in either direction",
            "category": "Volatility",
            "risk_level": "Medium"
        },
        {
            "name": "Calendar Spread",
            "description": "Profit from time decay",
            "category": "Time",
            "risk_level": "Low"
        }
    ]
    
    return {"templates": templates}


@router.post("/what-if")
async def what_if_analysis(
    strategy_request: StrategyRequest,
    underlying_price: float
):
    """
    What-if scenario analysis
    
    Tests strategy performance under different market conditions
    """
    from ..strategies.builder import StrategyBuilder
    from ..strategies.greeks_aggregator import whatif_analysis
    
    try:
        # Build strategy
        strategy = StrategyBuilder(name=strategy_request.name)
        strategy.set_underlying_price(strategy_request.underlying_price)
        
        for leg in strategy_request.legs:
            strategy.add_leg(
                action=leg.action,
                option_type=leg.option_type,
                strike=leg.strike,
                expiry=leg.expiry,
                quantity=leg.quantity,
                premium=leg.premium,
                delta=leg.delta,
                gamma=leg.gamma,
                theta=leg.theta,
                vega=leg.vega,
                rho=leg.rho
            )
        
        # Run what-if analysis
        scenarios = whatif_analysis(strategy, underlying_price)
        
        return {"scenarios": scenarios}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
