"""Performance metrics calculations for backtesting"""

import numpy as np
from typing import List, Dict


def calculate_performance_metrics(
    equity_curve: List[Dict],
    trade_log: List
) -> Dict[str, float]:
    """
    Calculate comprehensive performance metrics
    
    Args:
        equity_curve: List of equity snapshots over time
        trade_log: List of executed trades
        
    Returns:
        Dictionary with performance metrics
    """
    if not equity_curve or len(equity_curve) < 2:
        return {
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0
        }
    
    # Extract returns
    initial_capital = equity_curve[0]['total_equity']
    final_capital = equity_curve[-1]['total_equity']
    
    returns = []
    for i in range(1, len(equity_curve)):
        ret = (equity_curve[i]['total_equity'] - equity_curve[i-1]['total_equity']) / equity_curve[i-1]['total_equity']
        returns.append(ret)
    
    returns = np.array(returns)
    
    # Total return
    total_return = (final_capital - initial_capital) / initial_capital
    
    # Annualized return (assuming daily data)
    days = len(equity_curve)
    years = days / 252  # Trading days
    if years > 0:
        annualized_return = (1 + total_return) ** (1 / years) - 1
    else:
        annualized_return = 0.0
    
    # Sharpe Ratio (annualized)
    if len(returns) > 1:
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        if std_return > 0:
            sharpe_ratio = (mean_return / std_return) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
    else:
        sharpe_ratio = 0.0
    
    # Sortino Ratio (only downside deviation)
    downside_returns = returns[returns < 0]
    if len(downside_returns) > 1:
        downside_std = np.std(downside_returns, ddof=1)
        if downside_std > 0:
            sortino_ratio = (np.mean(returns) / downside_std) * np.sqrt(252)
        else:
            sortino_ratio = 0.0
    else:
        sortino_ratio = 0.0
    
    # Maximum Drawdown
    max_drawdown, max_drawdown_duration = calculate_max_drawdown(equity_curve)
    
    # Calmar Ratio (return / max drawdown)
    if max_drawdown != 0:
        calmar_ratio = annualized_return / abs(max_drawdown)
    else:
        calmar_ratio = 0.0
    
    # Trade-based metrics
    if trade_log:
        winning_trades = [t.pnl for t in trade_log if t.pnl > 0]
        losing_trades = [t.pnl for t in trade_log if t.pnl < 0]
        
        total_trades = len([t for t in trade_log if t.pnl != 0])
        
        if total_trades > 0:
            win_rate = len(winning_trades) / total_trades
        else:
            win_rate = 0.0
        
        # Profit factor
        gross_profit = sum(winning_trades) if winning_trades else 0
        gross_loss = abs(sum(losing_trades)) if losing_trades else 0
        
        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        else:
            profit_factor = float('inf') if gross_profit > 0 else 0.0
        
        # Average win/loss
        avg_win = np.mean(winning_trades) if winning_trades else 0.0
        avg_loss = np.mean(losing_trades) if losing_trades else 0.0
        
        # Expectancy
        if total_trades > 0:
            expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        else:
            expectancy = 0.0
    else:
        win_rate = 0.0
        profit_factor = 0.0
        avg_win = 0.0
        avg_loss = 0.0
        expectancy = 0.0
        total_trades = 0
    
    return {
        'total_return': float(total_return),
        'annualized_return': float(annualized_return),
        'sharpe_ratio': float(sharpe_ratio),
        'sortino_ratio': float(sortino_ratio),
        'calmar_ratio': float(calmar_ratio),
        'max_drawdown': float(max_drawdown),
        'max_drawdown_duration_days': int(max_drawdown_duration),
        'win_rate': float(win_rate),
        'profit_factor': float(profit_factor) if profit_factor != float('inf') else None,
        'avg_win': float(avg_win),
        'avg_loss': float(avg_loss),
        'expectancy': float(expectancy),
        'total_trades': int(total_trades),
        'final_equity': float(final_capital)
    }


def calculate_max_drawdown(equity_curve: List[Dict]) -> tuple:
    """
    Calculate maximum drawdown and duration
    
    Args:
        equity_curve: List of equity snapshots
        
    Returns:
        Tuple of (max_drawdown_pct, duration_in_periods)
    """
    if not equity_curve:
        return 0.0, 0
    
    equity_values = [e['total_equity'] for e in equity_curve]
    
    max_dd = 0.0
    max_dd_duration = 0
    current_dd_duration = 0
    peak = equity_values[0]
    
    for value in equity_values:
        if value > peak:
            peak = value
            current_dd_duration = 0
        else:
            dd = (value - peak) / peak
            max_dd = min(max_dd, dd)
            current_dd_duration += 1
            max_dd_duration = max(max_dd_duration, current_dd_duration)
    
    return max_dd, max_dd_duration


def calculate_rolling_metrics(
    equity_curve: List[Dict],
    window: int = 30
) -> Dict[str, List[float]]:
    """
    Calculate rolling performance metrics
    
    Args:
        equity_curve: List of equity snapshots
        window: Rolling window size
        
    Returns:
        Dictionary with rolling metrics
    """
    if len(equity_curve) < window:
        return {
            'rolling_return': [],
            'rolling_volatility': [],
            'rolling_sharpe': []
        }
    
    rolling_return = []
    rolling_volatility = []
    rolling_sharpe = []
    
    for i in range(window, len(equity_curve)):
        window_data = equity_curve[i-window:i]
        
        # Calculate returns for window
        returns = []
        for j in range(1, len(window_data)):
            ret = (window_data[j]['total_equity'] - window_data[j-1]['total_equity']) / window_data[j-1]['total_equity']
            returns.append(ret)
        
        returns = np.array(returns)
        
        # Rolling return
        window_return = (window_data[-1]['total_equity'] - window_data[0]['total_equity']) / window_data[0]['total_equity']
        rolling_return.append(window_return)
        
        # Rolling volatility (annualized)
        volatility = np.std(returns, ddof=1) * np.sqrt(252)
        rolling_volatility.append(volatility)
        
        # Rolling Sharpe
        if volatility > 0:
            sharpe = (np.mean(returns) / np.std(returns, ddof=1)) * np.sqrt(252)
        else:
            sharpe = 0.0
        rolling_sharpe.append(sharpe)
    
    return {
        'rolling_return': rolling_return,
        'rolling_volatility': rolling_volatility,
        'rolling_sharpe': rolling_sharpe
    }


def calculate_monthly_returns(equity_curve: List[Dict]) -> Dict:
    """
    Calculate monthly returns for heat map visualization
    
    Args:
        equity_curve: List of equity snapshots
        
    Returns:
        Dictionary with monthly returns by year and month
    """
    monthly_returns = {}
    
    # Group by month
    monthly_equity = {}
    for snapshot in equity_curve:
        timestamp = snapshot['timestamp']
        key = (timestamp.year, timestamp.month)
        
        if key not in monthly_equity:
            monthly_equity[key] = []
        monthly_equity[key].append(snapshot['total_equity'])
    
    # Calculate returns for each month
    for (year, month), equities in monthly_equity.items():
        if len(equities) > 1:
            month_return = (equities[-1] - equities[0]) / equities[0]
        else:
            month_return = 0.0
        
        if year not in monthly_returns:
            monthly_returns[year] = {}
        monthly_returns[year][month] = month_return
    
    return monthly_returns
