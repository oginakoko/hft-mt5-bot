"""Analysis tools for strategy performance evaluation."""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta
from ..data.database import Database

class PerformanceAnalyzer:
    """Analyzes trading performance and generates reports."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def calculate_metrics(self, start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> Dict:
        """Calculate comprehensive performance metrics."""
        trades_df = self.db.get_trade_history(start_time=start_time, end_time=end_time)
        metrics_df = self.db.get_performance_metrics(start_time=start_time, end_time=end_time)
        
        if trades_df.empty:
            return {}
        
        # Calculate basic metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['profit'] > 0])
        losing_trades = len(trades_df[trades_df['profit'] <= 0])
        
        total_profit = trades_df['profit'].sum()
        max_drawdown = self._calculate_max_drawdown(trades_df)
        
        # Calculate advanced metrics
        sharpe_ratio = self._calculate_sharpe_ratio(trades_df)
        profit_factor = self._calculate_profit_factor(trades_df)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
            'total_profit': total_profit,
            'avg_profit_per_trade': total_profit / total_trades if total_trades > 0 else 0,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': profit_factor,
            'avg_execution_latency': metrics_df['execution_latency'].mean(),
            'trades_per_second': metrics_df['trades_per_second'].mean()
        }
    
    def _calculate_max_drawdown(self, trades_df: pd.DataFrame) -> float:
        """Calculate maximum drawdown from trade history."""
        if trades_df.empty:
            return 0.0
            
        cumulative = trades_df['profit'].cumsum()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        return abs(drawdown.min()) if len(drawdown) > 0 else 0.0
    
    def _calculate_sharpe_ratio(self, trades_df: pd.DataFrame,
                              risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio of trading returns."""
        if trades_df.empty:
            return 0.0
            
        returns = trades_df['profit'].pct_change().dropna()
        if len(returns) < 2:
            return 0.0
            
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        return np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
    
    def _calculate_profit_factor(self, trades_df: pd.DataFrame) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        if trades_df.empty:
            return 0.0
            
        gross_profit = trades_df[trades_df['profit'] > 0]['profit'].sum()
        gross_loss = abs(trades_df[trades_df['profit'] < 0]['profit'].sum())
        
        return gross_profit / gross_loss if gross_loss != 0 else float('inf')
    
    def generate_report(self, start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> str:
        """Generate a formatted performance report."""
        metrics = self.calculate_metrics(start_time, end_time)
        
        report = [
            "Performance Report",
            "=" * 50,
            f"Period: {start_time or 'All'} to {end_time or 'Now'}",
            "-" * 50,
            f"Total Trades: {metrics.get('total_trades', 0)}",
            f"Win Rate: {metrics.get('win_rate', 0):.2%}",
            f"Total Profit: ${metrics.get('total_profit', 0):.2f}",
            f"Average Profit per Trade: ${metrics.get('avg_profit_per_trade', 0):.2f}",
            f"Maximum Drawdown: {metrics.get('max_drawdown', 0):.2%}",
            f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}",
            f"Profit Factor: {metrics.get('profit_factor', 0):.2f}",
            "-" * 50,
            "Performance Metrics:",
            f"Average Execution Latency: {metrics.get('avg_execution_latency', 0):.2f}ms",
            f"Average Trades per Second: {metrics.get('trades_per_second', 0):.2f}",
        ]
        
        return "\n".join(report)
