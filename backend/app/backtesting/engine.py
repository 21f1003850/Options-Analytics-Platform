"""Event-driven backtesting engine for options strategies"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import numpy as np


class EventType(Enum):
    """Backtest event types"""
    MARKET_DATA = "market_data"
    SIGNAL = "signal"
    ORDER = "order"
    FILL = "fill"


@dataclass
class BacktestConfig:
    """Configuration for backtest"""
    initial_capital: float = 100000.0
    commission_per_contract: float = 0.65
    slippage_pct: float = 0.01  # 1% slippage
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    benchmark: Optional[str] = None


@dataclass
class TradeLog:
    """Record of a trade"""
    timestamp: datetime
    symbol: str
    action: str  # 'buy' or 'sell'
    quantity: int
    price: float
    commission: float
    pnl: float = 0.0
    cumulative_pnl: float = 0.0


class Portfolio:
    """Portfolio manager for backtest"""
    
    def __init__(self, initial_capital: float, commission_per_contract: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_per_contract = commission_per_contract
        self.positions: Dict[str, Dict] = {}
        self.trade_log: List[TradeLog] = []
        self.equity_curve: List[Dict] = []
        
    def execute_order(
        self,
        timestamp: datetime,
        symbol: str,
        action: str,
        quantity: int,
        price: float
    ) -> bool:
        """
        Execute an order
        
        Args:
            timestamp: Order timestamp
            symbol: Option symbol
            action: 'buy' or 'sell'
            quantity: Number of contracts
            price: Execution price
            
        Returns:
            True if order executed successfully
        """
        multiplier = 100
        commission = self.commission_per_contract * quantity
        
        if action.lower() == 'buy':
            cost = price * quantity * multiplier + commission
            
            if cost > self.cash:
                return False  # Insufficient funds
            
            self.cash -= cost
            
            if symbol in self.positions:
                # Add to existing position
                self.positions[symbol]['quantity'] += quantity
                self.positions[symbol]['avg_cost'] = (
                    (self.positions[symbol]['avg_cost'] * self.positions[symbol]['quantity'] + 
                     price * quantity) / self.positions[symbol]['quantity']
                )
            else:
                # New position
                self.positions[symbol] = {
                    'quantity': quantity,
                    'avg_cost': price,
                    'entry_time': timestamp
                }
            
            pnl = 0.0
            
        else:  # sell
            if symbol not in self.positions:
                # Allow opening short position
                self.positions[symbol] = {
                    'quantity': -quantity,
                    'avg_cost': price,
                    'entry_time': timestamp
                }
                credit = price * quantity * multiplier - commission
                self.cash += credit
                pnl = 0.0
            else:
                # Closing or reducing position
                pos = self.positions[symbol]
                avg_cost = pos['avg_cost']
                
                # Calculate P&L
                pnl = (price - avg_cost) * min(quantity, pos['quantity']) * multiplier - commission
                
                credit = price * quantity * multiplier - commission
                self.cash += credit
                
                pos['quantity'] -= quantity
                
                if pos['quantity'] <= 0:
                    del self.positions[symbol]
        
        # Record trade
        cumulative_pnl = sum(trade.pnl for trade in self.trade_log) + pnl
        
        trade = TradeLog(
            timestamp=timestamp,
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            commission=commission,
            pnl=pnl,
            cumulative_pnl=cumulative_pnl
        )
        self.trade_log.append(trade)
        
        return True
    
    def update_equity(self, timestamp: datetime, current_prices: Dict[str, float]):
        """Update equity curve with current prices"""
        position_value = 0.0
        
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                position_value += pos['quantity'] * current_prices[symbol] * 100
        
        total_equity = self.cash + position_value
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'cash': self.cash,
            'position_value': position_value,
            'total_equity': total_equity,
            'return': (total_equity - self.initial_capital) / self.initial_capital
        })
    
    def get_current_equity(self, current_prices: Dict[str, float]) -> float:
        """Get current total equity"""
        position_value = sum(
            pos['quantity'] * current_prices.get(symbol, pos['avg_cost']) * 100
            for symbol, pos in self.positions.items()
        )
        return self.cash + position_value


class BacktestEngine:
    """Event-driven backtesting engine"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.portfolio = Portfolio(config.initial_capital, config.commission_per_contract)
        self.current_time: Optional[datetime] = None
        
    def run(
        self,
        data: Dict[str, List[Dict]],
        strategy_func: Callable,
        rebalance_freq: str = "daily"
    ) -> Dict:
        """
        Run backtest
        
        Args:
            data: Dictionary mapping symbols to price data
            strategy_func: Strategy function that generates signals
            rebalance_freq: Rebalancing frequency ('daily', 'weekly', 'monthly')
            
        Returns:
            Dictionary with backtest results
        """
        # Get date range
        all_dates = set()
        for symbol_data in data.values():
            for bar in symbol_data:
                all_dates.add(bar['timestamp'] if isinstance(bar['timestamp'], datetime) 
                             else datetime.fromisoformat(bar['timestamp']))
        
        dates = sorted(all_dates)
        
        if self.config.start_date:
            dates = [d for d in dates if d >= self.config.start_date]
        if self.config.end_date:
            dates = [d for d in dates if d <= self.config.end_date]
        
        # Run backtest
        for i, current_date in enumerate(dates):
            self.current_time = current_date
            
            # Get current market data
            current_prices = {}
            for symbol, symbol_data in data.items():
                for bar in symbol_data:
                    bar_time = bar['timestamp'] if isinstance(bar['timestamp'], datetime) else datetime.fromisoformat(bar['timestamp'])
                    if bar_time == current_date:
                        current_prices[symbol] = bar['close']
                        break
            
            # Update equity curve
            self.portfolio.update_equity(current_date, current_prices)
            
            # Generate signals from strategy
            signals = strategy_func(
                current_date=current_date,
                portfolio=self.portfolio,
                market_data=current_prices
            )
            
            # Execute signals
            if signals:
                for signal in signals:
                    self.portfolio.execute_order(
                        timestamp=current_date,
                        symbol=signal['symbol'],
                        action=signal['action'],
                        quantity=signal['quantity'],
                        price=signal['price'] * (1 + self.config.slippage_pct)
                    )
        
        # Final equity update
        if dates:
            final_prices = {}
            for symbol in data.keys():
                for bar in data[symbol]:
                    bar_time = bar['timestamp'] if isinstance(bar['timestamp'], datetime) else datetime.fromisoformat(bar['timestamp'])
                    if bar_time == dates[-1]:
                        final_prices[symbol] = bar['close']
            
            self.portfolio.update_equity(dates[-1], final_prices)
        
        # Calculate performance metrics
        from .performance import calculate_performance_metrics
        performance = calculate_performance_metrics(
            self.portfolio.equity_curve,
            self.portfolio.trade_log
        )
        
        return {
            'config': self.config,
            'equity_curve': self.portfolio.equity_curve,
            'trade_log': self.portfolio.trade_log,
            'final_equity': self.portfolio.equity_curve[-1]['total_equity'] if self.portfolio.equity_curve else self.config.initial_capital,
            'performance': performance
        }
    
    def get_results(self) -> Dict:
        """Get backtest results"""
        from .performance import calculate_performance_metrics
        
        performance = calculate_performance_metrics(
            self.portfolio.equity_curve,
            self.portfolio.trade_log
        )
        
        return {
            'equity_curve': self.portfolio.equity_curve,
            'trade_log': [vars(trade) for trade in self.portfolio.trade_log],
            'performance': performance
        }
