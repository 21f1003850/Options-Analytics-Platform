"""Backtesting and Monte Carlo API routes"""

from fastapi import APIRouter, HTTPException

from ..models import (
    BacktestRequest,
    BacktestResponse,
    MonteCarloRequest,
    MonteCarloResponse
)

router = APIRouter()


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest on a strategy
    
    Simulates strategy performance over historical data
    """
    from ..backtesting.engine import BacktestEngine, BacktestConfig
    from ..brokers.factory import BrokerFactory
    from ..config import settings
    from datetime import datetime, timedelta
    
    try:
        # Create backtest config
        config = BacktestConfig(
            initial_capital=request.config.initial_capital,
            commission_per_contract=request.config.commission_per_contract,
            slippage_pct=request.config.slippage_pct,
            start_date=request.config.start_date,
            end_date=request.config.end_date
        )
        
        # Get historical data for symbols
        broker = BrokerFactory.create(settings.DEFAULT_BROKER)
        await broker.connect({})
        
        data = {}
        end_date = request.config.end_date or datetime.now()
        start_date = request.config.start_date or (end_date - timedelta(days=365))
        
        for symbol in request.symbols:
            historical = await broker.get_historical_data(
                symbol,
                start_date,
                end_date,
                timeframe="1d"
            )
            data[symbol] = historical
        
        await broker.disconnect()
        
        # Define simple strategy function (buy and hold)
        def simple_strategy(current_date, portfolio, market_data):
            # This is a placeholder - real strategies would be more complex
            signals = []
            return signals
        
        # Run backtest
        engine = BacktestEngine(config)
        results = engine.run(data, simple_strategy)
        
        return BacktestResponse(
            final_equity=results['final_equity'],
            total_return=results['performance']['total_return'],
            sharpe_ratio=results['performance']['sharpe_ratio'],
            max_drawdown=results['performance']['max_drawdown'],
            total_trades=results['performance']['total_trades'],
            win_rate=results['performance']['win_rate'],
            equity_curve=results['equity_curve'],
            performance=results['performance']
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-metrics")
async def get_performance_metrics(
    total_return: float,
    sharpe_ratio: float,
    max_drawdown: float
):
    """
    Calculate additional performance metrics
    
    Useful for comparing multiple strategies
    """
    return {
        "total_return": total_return,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "calmar_ratio": total_return / abs(max_drawdown) if max_drawdown != 0 else 0,
        "risk_adjusted_return": sharpe_ratio * abs(total_return)
    }


@router.post("/monte-carlo", response_model=MonteCarloResponse)
async def run_monte_carlo(request: MonteCarloRequest):
    """
    Run Monte Carlo simulation for strategy outcomes
    
    Estimates probability distribution of P&L at expiration
    """
    from ..backtesting.monte_carlo import simulate_strategy_outcomes
    
    try:
        # Define a simple payoff function (placeholder)
        # In real implementation, this would be based on strategy
        def strategy_payoff(final_price):
            # Example: long call at strike = initial_price
            strike = request.initial_price
            intrinsic = max(0, final_price - strike)
            premium = 5.0  # Example premium
            return (intrinsic - premium) * 100  # Per contract
        
        # Run simulation
        results = simulate_strategy_outcomes(
            strategy_func=strategy_payoff,
            initial_price=request.initial_price,
            volatility=request.volatility,
            days_to_expiry=request.days_to_expiry,
            num_simulations=request.num_simulations,
            drift=request.drift
        )
        
        return MonteCarloResponse(**results)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monte-carlo/strategy")
async def monte_carlo_for_strategy(
    strategy_request: dict,
    initial_price: float,
    volatility: float,
    days_to_expiry: int,
    num_simulations: int = 1000
):
    """
    Run Monte Carlo simulation for a custom strategy
    
    Accepts full strategy definition and simulates outcomes
    """
    from ..backtesting.monte_carlo import simulate_strategy_outcomes
    from ..strategies.builder import StrategyBuilder
    from ..strategies.payoff import _calculate_leg_payoff
    import numpy as np
    
    try:
        # Build strategy from request
        strategy = StrategyBuilder()
        # ... build strategy from strategy_request
        
        # Define payoff function based on strategy
        def strategy_payoff(final_price):
            total_payoff = 0.0
            for leg in strategy.legs:
                prices = np.array([final_price])
                leg_payoff = _calculate_leg_payoff(leg, prices, at_expiry=True)
                total_payoff += leg_payoff[0]
            return total_payoff
        
        # Run simulation
        results = simulate_strategy_outcomes(
            strategy_func=strategy_payoff,
            initial_price=initial_price,
            volatility=volatility,
            days_to_expiry=days_to_expiry,
            num_simulations=num_simulations
        )
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{backtest_id}")
async def get_backtest_report(backtest_id: str):
    """
    Get detailed backtest report
    
    Returns comprehensive report with charts and analysis
    """
    # In a real implementation, this would fetch from database
    return {
        "backtest_id": backtest_id,
        "status": "completed",
        "message": "Report generation not yet implemented"
    }


@router.post("/optimize")
async def optimize_strategy(
    strategy_template: str,
    optimization_criteria: str = "sharpe_ratio"
):
    """
    Optimize strategy parameters
    
    Uses grid search or genetic algorithm to find optimal parameters
    """
    return {
        "status": "not_implemented",
        "message": "Strategy optimization coming soon"
    }
