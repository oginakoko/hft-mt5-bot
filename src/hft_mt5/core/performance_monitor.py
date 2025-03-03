"""Performance monitoring for the HFT strategy."""

import time
from dataclasses import dataclass
from typing import Dict, List
import numpy as np
from ..utils.logger import logger

@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    tick_processing_times: List[float]
    signal_generation_times: List[float]
    execution_times: List[float]
    trades_per_second: float
    signals_per_second: float
    current_drawdown: float
    peak_drawdown: float

class PerformanceMonitor:
    """Monitors and logs strategy performance metrics."""
    
    def __init__(self, metrics_window: int = 1000):
        self.metrics_window = metrics_window
        self.tick_times: List[float] = []
        self.signal_times: List[float] = []
        self.execution_times: List[float] = []
        self.trade_count = 0
        self.signal_count = 0
        self.start_time = time.time()
    
    def record_tick_time(self, duration: float):
        """Record tick processing time."""
        self.tick_times.append(duration)
        if len(self.tick_times) > self.metrics_window:
            self.tick_times.pop(0)
    
    def record_signal_time(self, duration: float):
        """Record signal generation time."""
        self.signal_times.append(duration)
        self.signal_count += 1
        if len(self.signal_times) > self.metrics_window:
            self.signal_times.pop(0)
    
    def record_execution_time(self, duration: float):
        """Record trade execution time."""
        self.execution_times.append(duration)
        self.trade_count += 1
        if len(self.execution_times) > self.metrics_window:
            self.execution_times.pop(0)
    
    def get_metrics(self) -> PerformanceMetrics:
        """Calculate current performance metrics."""
        runtime = time.time() - self.start_time
        
        return PerformanceMetrics(
            tick_processing_times=self.tick_times[-100:] if self.tick_times else [],
            signal_generation_times=self.signal_times[-100:] if self.signal_times else [],
            execution_times=self.execution_times[-100:] if self.execution_times else [],
            trades_per_second=self.trade_count / runtime if runtime > 0 else 0,
            signals_per_second=self.signal_count / runtime if runtime > 0 else 0,
            current_drawdown=0.0,  # To be implemented
            peak_drawdown=0.0      # To be implemented
        )
    
    def log_metrics(self):
        """Log current performance metrics."""
        metrics = self.get_metrics()
        
        logger.info("Performance Metrics:")
        logger.info(f"Avg Tick Processing: {np.mean(metrics.tick_processing_times)*1000:.2f}ms")
        logger.info(f"Avg Signal Generation: {np.mean(metrics.signal_generation_times)*1000:.2f}ms")
        logger.info(f"Avg Execution Time: {np.mean(metrics.execution_times)*1000:.2f}ms")
        logger.info(f"Trades/sec: {metrics.trades_per_second:.2f}")
        logger.info(f"Signals/sec: {metrics.signals_per_second:.2f}")
