"""Data type definitions for the HFT strategy."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Deque
from collections import deque
import time
import pandas as pd
import numpy as np
import threading

@dataclass
class EquityPoint:
    """Single point on the equity curve."""
    timestamp: float
    balance: float
    equity: float
    margin: float
    profit: float

class EquityTracker:
    """Tracks account equity over time."""
    
    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        self.points: Deque[EquityPoint] = deque(maxlen=max_points)
        self.lock = threading.Lock()
        
    def add_point(self, point: EquityPoint):
        """Add new equity point to tracker."""
        with self.lock:
            self.points.append(point)
    
    def get_recent(self, n: Optional[int] = None) -> List[EquityPoint]:
        """Get n most recent equity points."""
        with self.lock:
            if n is None:
                return list(self.points)
            return list(self.points)[-n:]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert equity points to pandas DataFrame."""
        with self.lock:
            if not self.points:
                return pd.DataFrame(columns=['timestamp', 'balance', 'equity', 'margin', 'profit'])
            
            data = {
                'timestamp': [p.timestamp for p in self.points],
                'balance': [p.balance for p in self.points],
                'equity': [p.equity for p in self.points],
                'margin': [p.margin for p in self.points],
                'profit': [p.profit for p in self.points]
            }
            return pd.DataFrame(data)

@dataclass
class Tick:
    """Single price tick data."""
    bid: float
    ask: float
    time: float = 0.0
    volume: float = 0.0

@dataclass
class Signal:
    """Trading signal."""
    direction: int  # 1 for buy, -1 for sell, 0 for no action
    strength: float  # Signal strength between 0 and 1
    features: Dict[str, float]  # Calculated features that generated the signal
    symbol: str = ""  # Trading symbol (e.g. "EURUSD", "BTCUSD")
    timestamp: float = 0.0  # Signal generation timestamp

class TickBuffer:
    """Circular buffer for storing recent ticks."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize buffer with numpy array for better performance."""
        self.max_size = max_size
        self.buffer = np.zeros(max_size, dtype=[
            ('time', 'f8'),
            ('bid', 'f8'),
            ('ask', 'f8'),
            ('volume', 'f8'),
            ('spread', 'f8'),
            ('mid_price', 'f8')
        ])
        self.current_idx = 0
        self.is_filled = False
        self.lock = threading.Lock()
        
    def add_tick(self, tick: Tick):
        """Add new tick to buffer."""
        with self.lock:
            self.buffer[self.current_idx]['time'] = tick.time
            self.buffer[self.current_idx]['bid'] = tick.bid
            self.buffer[self.current_idx]['ask'] = tick.ask
            self.buffer[self.current_idx]['volume'] = tick.volume
            self.buffer[self.current_idx]['spread'] = tick.ask - tick.bid
            self.buffer[self.current_idx]['mid_price'] = (tick.bid + tick.ask) / 2
            
            self.current_idx = (self.current_idx + 1) % self.max_size
            if self.current_idx == 0:
                self.is_filled = True
        
    def get_recent(self, n: int = None) -> np.ndarray:
        """Get n most recent ticks."""
        with self.lock:
            if n is None:
                n = self.max_size
                
            if self.is_filled:
                if n >= self.max_size:
                    return self.buffer.copy()
                else:
                    idx = (self.current_idx - n) % self.max_size
                    if idx < self.current_idx:
                        return self.buffer[idx:self.current_idx].copy()
                    else:
                        return np.concatenate((self.buffer[idx:], self.buffer[:self.current_idx]))
            else:
                return self.buffer[:self.current_idx].copy()
        
    def to_dataframe(self, n_ticks: Optional[int] = None) -> pd.DataFrame:
        """Convert tick buffer to pandas DataFrame.
        
        Args:
            n_ticks: Optional number of most recent ticks to include. If None, includes all ticks.
            
        Returns:
            pd.DataFrame: DataFrame with columns [time, bid, ask, volume, spread, mid_price]
        """
        ticks = self.get_recent(n_ticks)
        if len(ticks) == 0:
            return pd.DataFrame(columns=['time', 'bid', 'ask', 'volume', 'spread', 'mid_price'])
            
        # Create DataFrame without setting time as index
        return pd.DataFrame(ticks)
