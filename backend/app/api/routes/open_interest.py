"""Open Interest analytics API routes"""

from fastapi import APIRouter, HTTPException, Query

from ..models import PCRResponse, MaxPainResponse
from ..brokers.factory import BrokerFactory
from ..config import settings

router = APIRouter()


@router.get("/pcr", response_model=PCRResponse)
async def get_put_call_ratio(
    underlying: str = Query(..., description="Underlying symbol"),
    metric: str = Query("oi", description="Metric: 'oi' or 'volume'")
):
    """
    Calculate Put-Call Ratio
    
    PCR > 1.5: Bearish sentiment
    PCR < 0.7: Bullish sentiment
    """
    from ..analytics.open_interest.pcr import calculate_pcr
    
    try:
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        contracts = await broker.get_option_chain(underlying)
        
        await broker.disconnect()
        
        option_data = [
            {
                'option_type': c.option_type.value,
                'open_interest': c.open_interest,
                'volume': c.volume
            }
            for c in contracts
        ]
        
        pcr_data = calculate_pcr(option_data, metric=metric)
        
        return PCRResponse(**pcr_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pcr/by-expiry")
async def get_pcr_by_expiry(
    underlying: str = Query(..., description="Underlying symbol"),
    metric: str = Query("oi", description="Metric: 'oi' or 'volume'")
):
    """Calculate PCR for each expiration separately"""
    from ..analytics.open_interest.pcr import calculate_pcr_by_expiry
    
    try:
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        contracts = await broker.get_option_chain(underlying)
        
        await broker.disconnect()
        
        option_data = [
            {
                'option_type': c.option_type.value,
                'open_interest': c.open_interest,
                'volume': c.volume,
                'expiry': c.expiry
            }
            for c in contracts
        ]
        
        pcr_by_expiry = calculate_pcr_by_expiry(option_data, metric=metric)
        
        return pcr_by_expiry
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/max-pain", response_model=MaxPainResponse)
async def get_max_pain(
    underlying: str = Query(..., description="Underlying symbol")
):
    """
    Calculate Max Pain strike price
    
    Max Pain is the strike where option writers would lose the least
    """
    from ..analytics.open_interest.max_pain import calculate_max_pain
    
    try:
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        contracts = await broker.get_option_chain(underlying)
        
        await broker.disconnect()
        
        option_data = [
            {
                'strike': c.strike,
                'open_interest': c.open_interest,
                'option_type': c.option_type.value
            }
            for c in contracts
        ]
        
        max_pain_data = calculate_max_pain(option_data)
        
        return MaxPainResponse(**max_pain_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/concentration")
async def get_oi_concentration(
    underlying: str = Query(..., description="Underlying symbol"),
    top_n: int = Query(10, description="Number of top strikes to return")
):
    """Get open interest concentration at specific strikes"""
    from ..analytics.open_interest.oi_analysis import calculate_oi_concentration
    
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
                'open_interest': c.open_interest,
                'option_type': c.option_type.value
            }
            for c in contracts
        ]
        
        concentration = calculate_oi_concentration(
            option_data,
            underlying_price,
            top_n=top_n
        )
        
        return concentration
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heatmap")
async def get_oi_heatmap(
    underlying: str = Query(..., description="Underlying symbol")
):
    """Get data for OI heatmap visualization"""
    from ..analytics.open_interest.charts import generate_oi_heatmap_data
    
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
                'open_interest': c.open_interest,
                'option_type': c.option_type.value
            }
            for c in contracts
        ]
        
        heatmap_data = generate_oi_heatmap_data(option_data, underlying_price)
        
        return heatmap_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/distribution")
async def get_oi_distribution(
    underlying: str = Query(..., description="Underlying symbol"),
    expiry_days: int = Query(None, description="Filter by expiry days")
):
    """Get OI distribution by strike"""
    from ..analytics.open_interest.charts import generate_oi_distribution_data
    
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
                'open_interest': c.open_interest,
                'option_type': c.option_type.value
            }
            for c in contracts
        ]
        
        distribution = generate_oi_distribution_data(
            option_data,
            underlying_price,
            expiry_days=expiry_days
        )
        
        return distribution
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gamma-walls")
async def get_gamma_walls(
    underlying: str = Query(..., description="Underlying symbol"),
    threshold_pct: float = Query(0.1, description="Threshold for significance")
):
    """Identify gamma walls (high gamma concentration points)"""
    from ..analytics.open_interest.oi_analysis import identify_gamma_walls
    
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
                'gamma': c.gamma,
                'open_interest': c.open_interest,
                'option_type': c.option_type.value
            }
            for c in contracts
        ]
        
        gamma_walls = identify_gamma_walls(
            option_data,
            underlying_price,
            threshold_pct=threshold_pct
        )
        
        return gamma_walls
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
