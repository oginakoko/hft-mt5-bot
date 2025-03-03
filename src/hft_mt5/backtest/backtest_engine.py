"""Backtesting engine for HFT strategy validation."""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import MetaTrader5 as mt5
from ..core.data_types import Tick, Signal
from ..core.feature_calculator import FeatureCalculator
from ..core.signal_generator import SignalGenerator
from ..utils.logger import logger

class BacktestEngine:
    """High-performance backtesting engine for HFT strategies."""
    
    def __init__(self, config):
        self.config = config
        self.feature_calculator = FeatureCalculator()
        self.signal_generator = SignalGenerator(config)
        
        # Performance tracking
        self.equity_curve = []
        self.trades: List[Dict] = []
        self.current_position = None
        self.initial_balance = 10000  # Default starting balance
        
        # Slippage simulation
        self.slippage_model = self._create_slippage_model()
        
    def run(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Run backtest over specified period."""
        logger.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")
        
        # Get historical data
        ticks = self._get_tick_data(symbol, start_date, end_date)
        if len(ticks) == 0:
            raise ValueError("No tick data available for backtesting")
        
        # Initialize tracking variables
        equity = self.initial_balance
        position = None
        results = []
        
        # Process each tick
        for i, tick in enumerate(ticks):
            # Update equity curve
            if position:
                equity = self._calculate_equity(position, tick)
                self.equity_curve.append(equity)
            
            # Generate features and signals
            if i >= self.feature_calculator.window_size:
                window = ticks[max(0, i-self.feature_calculator.window_size):i]
                features = self.feature_calculator.calculate_features(window)
                signal = self.signal_generator.generate_signal(features)
                
                # Process signal
                if signal.direction != 0:
                    if position is None:
                        # Open new position
                        position = self._open_position(signal, tick)
                    elif (position['direction'] != signal.direction and 
                          signal.strength > self.config.getfloat('HFT', 'signal_threshold')):
                        # Close existing position and open new one
                        results.append(self._close_position(position, tick))
                        position = self._open_position(signal, tick)
            
            # Record state
            results.append({
                'timestamp': tick.time,
                'price': tick.mid,
                'equity': equity,
                'position': 1 if position and position['direction'] > 0 else 
                          -1 if position and position['direction'] < 0 else 0
            })
        
        # Close any remaining position
        if position:
            results.append(self._close_position(position, ticks[-1]))
        
        # Generate performance metrics
        self._calculate_performance_metrics(results)
        
        return pd.DataFrame(results)
    
    def _get_tick_data(self, symbol: str, start_date: datetime, end_date: datetime) -> np.ndarray:
        """Get historical tick data from MT5."""
        ticks = mt5.copy_ticks_range(symbol, start_date, end_date, mt5.COPY_TICKS_ALL)
        if ticks is None:
            return np.array([])
        
        # Convert to structured array
        dtype = [('time', 'i8'), ('bid', 'f8'), ('ask', 'f8'), 
                ('last', 'f8'), ('volume', 'f8'), ('flags', 'i4')]
        return np.array([(t.time, t.bid, t.ask, t.last, t.volume, t.flags) 
                        for t in ticks], dtype=dtype)
    
    def _create_slippage_model(self) -> callable:
        """Create realistic slippage simulation."""
        base_spread = 0.0001  # 1 pip for major pairs
        volatility_impact = 0.5  # Slippage increases with volatility
        
        def slippage_fn(price: float, volume: float, volatility: float) -> float:
            spread = base_spread * (1 + volatility * volatility_impact)
            market_impact = volume * spread * 0.1  # Simple market impact model
            return max(spread + market_impact, 0.0)
        
        return slippage_fn
    
    def _calculate_equity(self, position: Dict, tick: np.ndarray) -> float:
        """Calculate current equity based on open position."""
        if not position:
            return self.equity_curve[-1] if self.equity_curve else self.initial_balance
            
        entry_price = position['entry_price']
        volume = position['volume']
        direction = position['direction']
        
        # Calculate current P&L
        current_price = tick['bid'] if direction > 0 else tick['ask']
        pip_value = 0.0001  # Assuming 4 decimal places
        pips = (current_price - entry_price) / pip_value
        profit = pips * volume * 10  # Standard lot size
        
        return self.initial_balance + profit
    
    def _open_position(self, signal: Signal, tick: np.ndarray) -> Dict:
        """Simulate opening a new position."""
        volume = self._calculate_position_size(signal.strength)
        slippage = self.slippage_model(
            tick['mid'], 
            volume,
            signal.features.get('volatility', 0)
        )
        
        entry_price = tick['ask'] + slippage if signal.direction > 0 else tick['bid'] - slippage
        
        return {
            'direction': signal.direction,
            'volume': volume,
            'entry_price': entry_price,
            'entry_time': tick['time'],
            'signal_strength': signal.strength
        }
    
    def _close_position(self, position: Dict, tick: np.ndarray) -> Dict:
        """Simulate closing a position."""
        slippage = self.slippage_model(
            tick['mid'],
            position['volume'],
            0.0  # Could pass actual volatility here
        )
        
        exit_price = tick['bid'] - slippage if position['direction'] > 0 else tick['ask'] + slippage
        
        pip_value = 0.0001
        pips = (exit_price - position['entry_price']) / pip_value
        profit = pips * position['volume'] * 10 * position['direction']
        
        return {
            'entry_time': position['entry_time'],
            'exit_time': tick['time'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'direction': position['direction'],
            'volume': position['volume'],
            'profit': profit,
            'pips': pips,
            'signal_strength': position['signal_strength']
        }
    
    def _calculate_position_size(self, signal_strength: float) -> float:
        """Calculate position size based on signal strength and risk."""
        base_risk = self.config.getfloat('Trading', 'risk_per_trade', 0.01)
        max_size = self.config.getfloat('Trading', 'max_position_size', 1.0)
        
        size = base_risk * signal_strength * self.initial_balance / 10000
        return min(size, max_size)
    
    def _calculate_performance_metrics(self, results: List[Dict]) -> Dict:
        """Calculate comprehensive performance metrics."""
        df = pd.DataFrame(results)
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['profit'] > 0])
        total_profit = sum(t['profit'] for t in self.trades)
        
        # Advanced metrics
        returns = df['equity'].pct_change().dropna()
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 0 else 0
        max_drawdown = self._calculate_max_drawdown(df['equity'])
        
        self.metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
            'total_profit': total_profit,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'profit_factor': self._calculate_profit_factor(self.trades),
            'avg_trade_duration': self._calculate_avg_duration(self.trades)
        }
        
        logger.info(f"Backtest completed. Metrics: {self.metrics}")
        return self.metrics
    
    def _calculate_max_drawdown(self, equity: pd.Series) -> float:
        """Calculate maximum drawdown from equity curve."""
        peak = equity.expanding(min_periods=1).max()
        drawdown = (equity - peak) / peak
        return abs(drawdown.min()) if len(drawdown) > 0 else 0.0
    
    def _calculate_profit_factor(self, trades: List[Dict]) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        gross_profit = sum(t['profit'] for t in trades if t['profit'] > 0)
        gross_loss = abs(sum(t['profit'] for t in trades if t['profit'] < 0))
        return gross_profit / gross_loss if gross_loss != 0 else float('inf')
    
    def _calculate_avg_duration(self, trades: List[Dict]) -> float:
        """Calculate average trade duration in seconds."""
        durations = [(t['exit_time'] - t['entry_time']) for t in trades]
        return sum(durations) / len(durations) if durations else 0
