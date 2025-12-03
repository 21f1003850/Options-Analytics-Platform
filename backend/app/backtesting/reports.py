"""Report generation for backtest results"""

from typing import Dict, List
from datetime import datetime
import json


def generate_backtest_report(
    backtest_results: Dict,
    strategy_name: str = "Options Strategy",
    output_format: str = "dict"
) -> Dict:
    """
    Generate comprehensive backtest report
    
    Args:
        backtest_results: Results from BacktestEngine
        strategy_name: Name of the strategy
        output_format: 'dict', 'json', or 'html'
        
    Returns:
        Formatted report
    """
    performance = backtest_results.get('performance', {})
    equity_curve = backtest_results.get('equity_curve', [])
    trade_log = backtest_results.get('trade_log', [])
    
    # Summary statistics
    summary = {
        'strategy_name': strategy_name,
        'report_generated': datetime.now().isoformat(),
        'backtest_period': {
            'start': equity_curve[0]['timestamp'].isoformat() if equity_curve else None,
            'end': equity_curve[-1]['timestamp'].isoformat() if equity_curve else None,
            'total_days': len(equity_curve)
        },
        'performance_summary': {
            'total_return': f"{performance.get('total_return', 0) * 100:.2f}%",
            'annualized_return': f"{performance.get('annualized_return', 0) * 100:.2f}%",
            'sharpe_ratio': f"{performance.get('sharpe_ratio', 0):.2f}",
            'sortino_ratio': f"{performance.get('sortino_ratio', 0):.2f}",
            'max_drawdown': f"{performance.get('max_drawdown', 0) * 100:.2f}%",
            'calmar_ratio': f"{performance.get('calmar_ratio', 0):.2f}"
        },
        'trading_statistics': {
            'total_trades': performance.get('total_trades', 0),
            'win_rate': f"{performance.get('win_rate', 0) * 100:.2f}%",
            'profit_factor': f"{performance.get('profit_factor', 0):.2f}" if performance.get('profit_factor') is not None else "N/A",
            'avg_win': f"${performance.get('avg_win', 0):.2f}",
            'avg_loss': f"${performance.get('avg_loss', 0):.2f}",
            'expectancy': f"${performance.get('expectancy', 0):.2f}"
        }
    }
    
    # Trade analysis
    if trade_log:
        winning_trades = [t for t in trade_log if hasattr(t, 'pnl') and t.pnl > 0]
        losing_trades = [t for t in trade_log if hasattr(t, 'pnl') and t.pnl < 0]
        
        largest_win = max(winning_trades, key=lambda t: t.pnl) if winning_trades else None
        largest_loss = min(losing_trades, key=lambda t: t.pnl) if losing_trades else None
        
        trade_analysis = {
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'largest_win': {
                'symbol': largest_win.symbol,
                'pnl': f"${largest_win.pnl:.2f}",
                'date': largest_win.timestamp.isoformat()
            } if largest_win else None,
            'largest_loss': {
                'symbol': largest_loss.symbol,
                'pnl': f"${largest_loss.pnl:.2f}",
                'date': largest_loss.timestamp.isoformat()
            } if largest_loss else None
        }
    else:
        trade_analysis = {}
    
    # Risk metrics
    risk_metrics = {
        'max_drawdown': f"{performance.get('max_drawdown', 0) * 100:.2f}%",
        'max_drawdown_duration': f"{performance.get('max_drawdown_duration_days', 0)} days",
        'volatility': 'N/A',  # Would need to calculate from equity curve
        'var_95': 'N/A'  # Would need to calculate
    }
    
    report = {
        'summary': summary,
        'trade_analysis': trade_analysis,
        'risk_metrics': risk_metrics,
        'raw_performance': performance
    }
    
    if output_format == "json":
        return json.dumps(report, indent=2)
    elif output_format == "html":
        return generate_html_report(report)
    else:
        return report


def generate_html_report(report_data: Dict) -> str:
    """
    Generate HTML report
    
    Args:
        report_data: Report dictionary
        
    Returns:
        HTML string
    """
    summary = report_data['summary']
    perf = summary['performance_summary']
    trade_stats = summary['trading_statistics']
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Backtest Report - {summary['strategy_name']}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #333;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #555;
                margin-top: 30px;
            }}
            .metric-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .metric-card {{
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #4CAF50;
            }}
            .metric-label {{
                font-size: 14px;
                color: #777;
                margin-bottom: 5px;
            }}
            .metric-value {{
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }}
            .positive {{
                color: #4CAF50;
            }}
            .negative {{
                color: #f44336;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Backtest Report: {summary['strategy_name']}</h1>
            <p>Generated: {summary['report_generated']}</p>
            
            <h2>Performance Summary</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Return</div>
                    <div class="metric-value positive">{perf['total_return']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Annualized Return</div>
                    <div class="metric-value">{perf['annualized_return']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Sharpe Ratio</div>
                    <div class="metric-value">{perf['sharpe_ratio']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Max Drawdown</div>
                    <div class="metric-value negative">{perf['max_drawdown']}</div>
                </div>
            </div>
            
            <h2>Trading Statistics</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Trades</div>
                    <div class="metric-value">{trade_stats['total_trades']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value">{trade_stats['win_rate']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Profit Factor</div>
                    <div class="metric-value">{trade_stats['profit_factor']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Expectancy</div>
                    <div class="metric-value">{trade_stats['expectancy']}</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def export_trades_to_csv(trade_log: List, filename: str = "trades.csv") -> str:
    """
    Export trade log to CSV
    
    Args:
        trade_log: List of trades
        filename: Output filename
        
    Returns:
        CSV content as string
    """
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Timestamp', 'Symbol', 'Action', 'Quantity', 
        'Price', 'Commission', 'P&L', 'Cumulative P&L'
    ])
    
    # Trades
    for trade in trade_log:
        writer.writerow([
            trade.timestamp.isoformat() if hasattr(trade, 'timestamp') else '',
            trade.symbol if hasattr(trade, 'symbol') else '',
            trade.action if hasattr(trade, 'action') else '',
            trade.quantity if hasattr(trade, 'quantity') else 0,
            f"{trade.price:.2f}" if hasattr(trade, 'price') else '',
            f"{trade.commission:.2f}" if hasattr(trade, 'commission') else '',
            f"{trade.pnl:.2f}" if hasattr(trade, 'pnl') else '',
            f"{trade.cumulative_pnl:.2f}" if hasattr(trade, 'cumulative_pnl') else ''
        ])
    
    return output.getvalue()


def generate_tear_sheet(
    backtest_results: Dict,
    strategy_name: str
) -> Dict:
    """
    Generate comprehensive tear sheet with all key metrics
    
    Args:
        backtest_results: Backtest results
        strategy_name: Strategy name
        
    Returns:
        Tear sheet dictionary
    """
    performance = backtest_results.get('performance', {})
    
    tear_sheet = {
        'strategy': strategy_name,
        'returns': {
            'total': performance.get('total_return'),
            'annualized': performance.get('annualized_return'),
            'monthly_avg': performance.get('annualized_return', 0) / 12 if performance.get('annualized_return') else 0
        },
        'risk': {
            'sharpe': performance.get('sharpe_ratio'),
            'sortino': performance.get('sortino_ratio'),
            'calmar': performance.get('calmar_ratio'),
            'max_dd': performance.get('max_drawdown'),
            'max_dd_duration': performance.get('max_drawdown_duration_days')
        },
        'trades': {
            'total': performance.get('total_trades'),
            'win_rate': performance.get('win_rate'),
            'profit_factor': performance.get('profit_factor'),
            'avg_win': performance.get('avg_win'),
            'avg_loss': performance.get('avg_loss'),
            'expectancy': performance.get('expectancy')
        }
    }
    
    return tear_sheet
