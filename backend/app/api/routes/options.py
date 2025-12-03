"""Options chain and Greeks API routes"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from app.models import OptionChainRequest, OptionChainResponse, OptionContractResponse
from app.brokers.factory import BrokerFactory
from app.config import settings

router = APIRouter()


@router.get("/chain", response_model=OptionChainResponse)
async def get_option_chain(
    underlying: str = Query(..., description="Underlying symbol"),
    expiry: Optional[str] = Query(None, description="Optional expiration date (ISO format)")
):
    """
    Get option chain for an underlying symbol
    
    Returns calls and puts with full Greeks for all strikes and expirations
    """
    try:
        # Parse expiry if provided
        expiry_date = None
        if expiry:
            expiry_date = datetime.fromisoformat(expiry)
        
        # Get broker adapter
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        # Get option chain
        contracts = await broker.get_option_chain(underlying, expiry_date)
        
        # Get underlying price
        quote = await broker.get_quote(underlying)
        underlying_price = quote.get('last')
        
        await broker.disconnect()
        
        # Convert to response model
        contract_responses = [
            OptionContractResponse(
                symbol=c.symbol,
                underlying=c.underlying,
                strike=c.strike,
                expiry=c.expiry,
                option_type=c.option_type.value,
                bid=c.bid,
                ask=c.ask,
                last=c.last,
                volume=c.volume,
                open_interest=c.open_interest,
                implied_volatility=c.implied_volatility,
                delta=c.delta,
                gamma=c.gamma,
                theta=c.theta,
                vega=c.vega,
                rho=c.rho
            )
            for c in contracts
        ]
        
        return OptionChainResponse(
            underlying=underlying,
            underlying_price=underlying_price,
            contracts=contract_responses,
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expirations")
async def get_expirations(
    underlying: str = Query(..., description="Underlying symbol")
):
    """Get available expiration dates for an underlying"""
    try:
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        # Get all contracts
        contracts = await broker.get_option_chain(underlying)
        
        # Extract unique expiration dates
        expiries = sorted(set(c.expiry for c in contracts))
        
        await broker.disconnect()
        
        return {
            "underlying": underlying,
            "expirations": [e.isoformat() for e in expiries]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote")
async def get_quote(
    symbol: str = Query(..., description="Option or stock symbol")
):
    """Get real-time quote for a symbol"""
    try:
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        quote = await broker.get_quote(symbol)
        
        await broker.disconnect()
        
        return quote
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/greeks/calculate")
async def calculate_greeks(
    underlying_price: float,
    strike: float,
    time_to_expiry: float,
    volatility: float,
    option_type: str,
    risk_free_rate: float = 0.05,
    dividend_yield: float = 0.0
):
    """
    Calculate Greeks for a specific option
    
    Args:
        underlying_price: Current underlying price
        strike: Strike price
        time_to_expiry: Time to expiration in years
        volatility: Implied volatility (as decimal, e.g., 0.25 for 25%)
        option_type: 'call' or 'put'
        risk_free_rate: Risk-free interest rate
        dividend_yield: Dividend yield
    """
    from app.analytics.greeks.black_scholes import calculate_all_greeks
    
    try:
        greeks = calculate_all_greeks(
            S=underlying_price,
            K=strike,
            T=time_to_expiry,
            r=risk_free_rate,
            sigma=volatility,
            option_type=option_type,
            q=dividend_yield
        )
        
        return greeks
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/iv/calculate")
async def calculate_implied_volatility(
    price: float,
    underlying_price: float,
    strike: float,
    time_to_expiry: float,
    option_type: str,
    risk_free_rate: float = 0.05,
    dividend_yield: float = 0.0
):
    """
    Calculate implied volatility from option price
    
    Returns the IV or null if calculation fails
    """
    from app.analytics.greeks.implied_volatility import calculate_implied_volatility
    
    try:
        iv = calculate_implied_volatility(
            price=price,
            S=underlying_price,
            K=strike,
            T=time_to_expiry,
            r=risk_free_rate,
            option_type=option_type,
            q=dividend_yield,
            method="auto"
        )
        
        return {
            "implied_volatility": iv,
            "price": price,
            "strike": strike,
            "underlying_price": underlying_price
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
