"""API routes package initialization"""

from fastapi import APIRouter

# Create main API router
api_router = APIRouter()

# Import and include all route modules
from .options import router as options_router
from .volatility import router as volatility_router
from .open_interest import router as oi_router
from .strategies import router as strategies_router
from .backtest import router as backtest_router

api_router.include_router(options_router, prefix="/options", tags=["options"])
api_router.include_router(volatility_router, prefix="/volatility", tags=["volatility"])
api_router.include_router(oi_router, prefix="/oi", tags=["open-interest"])
api_router.include_router(strategies_router, prefix="/strategies", tags=["strategies"])
api_router.include_router(backtest_router, prefix="/backtest", tags=["backtest"])

__all__ = ["api_router"]
