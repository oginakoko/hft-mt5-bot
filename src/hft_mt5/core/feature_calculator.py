"""High-performance feature calculation for HFT strategy."""

import numpy as np
from typing import Dict, Optional
from ..utils.logger import logger

class FeatureCalculator:
    """Fast feature calculation for HFT signals."""
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        
    def calculate_features(self, ticks: np.ndarray) -> Dict[str, float]:
        """Calculate features from tick data.
        
        Args:
            ticks: Structured numpy array with fields:
                  time, bid, ask, last, volume, spread, mid_price
        """
        if len(ticks) < self.window_size:
            return {}
            
        try:
            features = {}
            
            # Price dynamics
            mid_prices = ticks['mid_price'][-self.window_size:]
            price_changes = np.diff(mid_prices)
            
            # Momentum features
            features['momentum_1'] = self._calculate_momentum(mid_prices, 1)
            features['momentum_5'] = self._calculate_momentum(mid_prices, 5)
            features['momentum_10'] = self._calculate_momentum(mid_prices, 10)
            
            # Volatility features
            features['volatility'] = np.std(price_changes)
            features['volatility_ratio'] = self._calculate_volatility_ratio(price_changes)
            
            # Spread features
            spreads = ticks['spread'][-self.window_size:]
            features['spread_mean'] = np.mean(spreads)
            features['spread_std'] = np.std(spreads)
            features['spread_trend'] = self._calculate_trend(spreads)
            
            # Volume features
            volumes = ticks['volume'][-self.window_size:]
            features['volume_imbalance'] = self._calculate_volume_imbalance(volumes, price_changes)
            features['volume_trend'] = self._calculate_trend(volumes)
            
            # Microstructure features
            features['tick_intensity'] = self._calculate_tick_intensity(ticks['time'][-self.window_size:])
            
            return features
            
        except Exception as e:
            logger.error(f"Error calculating features: {e}")
            return {}
    
    def _calculate_momentum(self, prices: np.ndarray, period: int) -> float:
        """Calculate price momentum over given period."""
        if len(prices) < period:
            return 0.0
        return (prices[-1] / prices[-period]) - 1.0
    
    def _calculate_volatility_ratio(self, changes: np.ndarray) -> float:
        """Calculate ratio of recent to historical volatility."""
        if len(changes) < 10:
            return 1.0
        recent_vol = np.std(changes[-5:])
        hist_vol = np.std(changes)
        return recent_vol / hist_vol if hist_vol != 0 else 1.0
    
    def _calculate_trend(self, data: np.ndarray) -> float:
        """Calculate linear trend coefficient."""
        if len(data) < 2:
            return 0.0
        x = np.arange(len(data))
        coeffs = np.polyfit(x, data, 1)
        return coeffs[0]
    
    def _calculate_volume_imbalance(self, volumes: np.ndarray, price_changes: np.ndarray) -> float:
        """Calculate volume-weighted price pressure."""
        if len(volumes) <= 1 or len(price_changes) < 1:
            return 0.0
        vol_price = volumes[1:] * price_changes
        return np.sum(vol_price) / np.sum(volumes[1:]) if np.sum(volumes[1:]) > 0 else 0.0
    
    def _calculate_tick_intensity(self, timestamps: np.ndarray) -> float:
        """Calculate tick arrival intensity."""
        if len(timestamps) < 2:
            return 0.0
        time_diffs = np.diff(timestamps)
        return 1000.0 / np.mean(time_diffs) if np.mean(time_diffs) > 0 else 0.0
