"""Volatility analytics API routes"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..models import VolatilitySurfaceResponse, VolatilitySkewResponse, IVTermStructureResponse
from ..brokers.factory import BrokerFactory
from ..config import settings

router = APIRouter()


@router.get("/surface", response_model=VolatilitySurfaceResponse)
async def get_volatility_surface(
    underlying: str = Query(..., description="Underlying symbol")
):
    """
    Get 3D volatility surface data
    
    Returns IV across strikes and expirations for visualization
    """
    from ..analytics.volatility.surface import generate_volatility_surface
    
    try:
        # Get option chain
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        contracts = await broker.get_option_chain(underlying)
        quote = await broker.get_quote(underlying)
        underlying_price = quote.get('last')
        
        await broker.disconnect()
        
        # Convert contracts to dict format
        option_data = [
            {
                'strike': c.strike,
                'expiry': c.expiry,
                'implied_volatility': c.implied_volatility
            }
            for c in contracts
        ]
        
        # Generate surface
        surface_data = generate_volatility_surface(option_data, underlying_price)
        
        return VolatilitySurfaceResponse(
            strikes=surface_data['strikes'].tolist(),
            expiries=surface_data['expiries'].tolist(),
            iv_surface=surface_data['iv_surface'].tolist(),
            moneyness=surface_data['moneyness'].tolist(),
            underlying_price=underlying_price
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skew", response_model=VolatilitySkewResponse)
async def get_volatility_skew(
    underlying: str = Query(..., description="Underlying symbol"),
    expiry_days: Optional[int] = Query(None, description="Filter by expiry (days)"),
    by_delta: bool = Query(False, description="Plot by delta instead of strike")
):
    """
    Get volatility skew data
    
    Shows how IV changes across strikes or deltas
    """
    from ..analytics.volatility.skew import calculate_volatility_skew
    
    try:
        # Get option chain
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        contracts = await broker.get_option_chain(underlying)
        quote = await broker.get_quote(underlying)
        underlying_price = quote.get('last')
        
        await broker.disconnect()
        
        # Convert to dict format
        option_data = [
            {
                'strike': c.strike,
                'expiry': c.expiry,
                'implied_volatility': c.implied_volatility,
                'delta': c.delta,
                'option_type': c.option_type.value
            }
            for c in contracts
        ]
        
        # Calculate skew
        skew_data = calculate_volatility_skew(
            option_data,
            underlying_price,
            expiry_days=expiry_days,
            by_delta=by_delta
        )
        
        return VolatilitySkewResponse(**skew_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smile")
async def get_volatility_smile(
    underlying: str = Query(..., description="Underlying symbol"),
    expiry_days: int = Query(..., description="Days to expiration")
):
    """Get volatility smile for a specific expiration"""
    from ..analytics.volatility.smile import calculate_volatility_smile
    
    try:
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        contracts = await broker.get_option_chain(underlying)
        quote = await broker.get_quote(underlying)
        underlying_price = quote.get('last')
        
        await broker.disconnect()
        
        option_data = [
            {
                'strike': c.strike,
                'expiry': c.expiry,
                'implied_volatility': c.implied_volatility,
                'option_type': c.option_type.value
            }
            for c in contracts
        ]
        
        smile_data = calculate_volatility_smile(
            option_data,
            underlying_price,
            expiry_days
        )
        
        return smile_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/term-structure", response_model=IVTermStructureResponse)
async def get_iv_term_structure(
    underlying: str = Query(..., description="Underlying symbol"),
    moneyness: float = Query(1.0, description="Target moneyness (1.0 = ATM)")
):
    """
    Get IV term structure
    
    Shows how IV changes across expirations at a given moneyness
    """
    from ..analytics.volatility.term_structure import calculate_iv_term_structure
    
    try:
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        contracts = await broker.get_option_chain(underlying)
        quote = await broker.get_quote(underlying)
        underlying_price = quote.get('last')
        
        await broker.disconnect()
        
        option_data = [
            {
                'strike': c.strike,
                'expiry': c.expiry,
                'implied_volatility': c.implied_volatility
            }
            for c in contracts
        ]
        
        ts_data = calculate_iv_term_structure(
            option_data,
            underlying_price,
            moneyness_target=moneyness
        )
        
        return IVTermStructureResponse(**ts_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical")
async def get_historical_volatility(
    symbol: str = Query(..., description="Symbol"),
    window: int = Query(30, description="Window size in days")
):
    """Calculate historical volatility from price data"""
    from ..analytics.volatility.historical import calculate_historical_volatility
    
    try:
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        # Get historical data
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=window + 10)
        
        historical_data = await broker.get_historical_data(
            symbol,
            start_date,
            end_date,
            timeframe="1d"
        )
        
        await broker.disconnect()
        
        # Calculate HV
        hv = calculate_historical_volatility(historical_data, window=window)
        
        return {
            "symbol": symbol,
            "window": window,
            "historical_volatility": hv
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
