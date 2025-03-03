"""Feature generation component for HFT strategy."""

import numpy as np
from typing import Dict
from .data_types import TickBuffer

class FeatureGenerator:
    """Generates features from tick data for signal generation."""
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
    
    def calculate_features(self, tick_buffer: TickBuffer) -> Dict[str, float]:
        """Calculate features from recent ticks."""
        ticks = tick_buffer.get_recent(self.window_size * 2)  # Get more ticks for better analysis
        if len(ticks) < self.window_size:
            return {}
            
        features = {}
        
        # Price features
        mid_prices = ticks['mid_price']
        features['price_change'] = self._calculate_returns(mid_prices)
        features['volatility'] = self._calculate_volatility(mid_prices)
        features['price_momentum'] = self._calculate_momentum(mid_prices)
        features['mean_deviation'] = self._calculate_mean_deviation(mid_prices)
        features['price_acceleration'] = self._calculate_acceleration(mid_prices)
        
        # Volume features
        features['volume_intensity'] = self._calculate_volume_intensity(ticks['volume'])
        features['volume_trend'] = self._calculate_volume_trend(ticks['volume'])
        features['vwap_diff'] = self._calculate_vwap_difference(ticks)
        
        # Spread and liquidity features
        features['spread'] = ticks['spread'][-1]
        features['bid_strength'] = self._calculate_bid_strength(ticks)
        features['ask_strength'] = self._calculate_ask_strength(ticks)
        
        # Microstructure features
        features['tick_pattern'] = self._analyze_tick_pattern(ticks)
        features['trade_sign'] = self._calculate_trade_sign(ticks)
        features['quote_intensity'] = self._calculate_quote_intensity(ticks)
        
        return features
    
    def _calculate_returns(self, prices: np.ndarray) -> float:
        """Calculate short-term returns."""
        if len(prices) < 2:
            return 0.0
        return (prices[-1] - prices[-2]) / prices[-2]
    
    def _calculate_volatility(self, prices: np.ndarray) -> float:
        """Calculate recent price volatility."""
        if len(prices) < 2:
            return 0.0
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns) * np.sqrt(len(returns))
    
    def _calculate_momentum(self, prices: np.ndarray) -> float:
        """Calculate price momentum."""
        if len(prices) < self.window_size:
            return 0.0
        momentum = prices[-1] / prices[-self.window_size] - 1
        return np.tanh(momentum * 100)  # Normalize
    
    def _calculate_mean_deviation(self, prices: np.ndarray) -> float:
        """Calculate deviation from moving average."""
        if len(prices) < self.window_size:
            return 0.0
        ma = np.mean(prices[-self.window_size:])
        return (prices[-1] - ma) / ma
    
    def _calculate_acceleration(self, prices: np.ndarray) -> float:
        """Calculate price acceleration."""
        if len(prices) < 3:
            return 0.0
        returns = np.diff(prices) / prices[:-1]
        return returns[-1] - returns[-2]
    
    def _calculate_volume_intensity(self, volumes: np.ndarray) -> float:
        """Calculate volume intensity relative to average."""
        if len(volumes) < self.window_size:
            return 1.0
        avg_volume = np.mean(volumes[-self.window_size:-1])
        if avg_volume == 0:
            return 1.0
        return volumes[-1] / avg_volume
    
    def _calculate_volume_trend(self, volumes: np.ndarray) -> float:
        """Calculate volume trend."""
        if len(volumes) < self.window_size:
            return 0.0
        trend = np.polyfit(range(self.window_size), volumes[-self.window_size:], 1)[0]
        return np.tanh(trend * 10)  # Normalize
    
    def _calculate_vwap_difference(self, ticks: np.ndarray) -> float:
        """Calculate difference from VWAP."""
        if len(ticks) < self.window_size:
            return 0.0
        volumes = ticks['volume'][-self.window_size:]
        prices = ticks['mid_price'][-self.window_size:]
        if np.sum(volumes) == 0:
            return 0.0
        vwap = np.sum(prices * volumes) / np.sum(volumes)
        return (prices[-1] - vwap) / vwap
    
    def _calculate_bid_strength(self, ticks: np.ndarray) -> float:
        """Calculate bid side strength."""
        if len(ticks) < self.window_size:
            return 0.5
        bid_changes = np.diff(ticks['bid'][-self.window_size:])
        positive_changes = np.sum(bid_changes > 0)
        return positive_changes / (self.window_size - 1)
    
    def _calculate_ask_strength(self, ticks: np.ndarray) -> float:
        """Calculate ask side strength."""
        if len(ticks) < self.window_size:
            return 0.5
        ask_changes = np.diff(ticks['ask'][-self.window_size:])
        positive_changes = np.sum(ask_changes > 0)
        return positive_changes / (self.window_size - 1)
    
    def _analyze_tick_pattern(self, ticks: np.ndarray) -> float:
        """Analyze tick patterns for predictive signals."""
        if len(ticks) < self.window_size:
            return 0.0
        mid_prices = ticks['mid_price'][-self.window_size:]
        ups = np.sum(np.diff(mid_prices) > 0)
        downs = np.sum(np.diff(mid_prices) < 0)
        return (ups - downs) / (self.window_size - 1)
    
    def _calculate_trade_sign(self, ticks: np.ndarray) -> float:
        """Calculate trade sign based on tick rule."""
        if len(ticks) < 2:
            return 0.0
        last_tick = ticks[-1]
        prev_tick = ticks[-2]
        if last_tick['mid_price'] > prev_tick['mid_price']:
            return 1.0
        elif last_tick['mid_price'] < prev_tick['mid_price']:
            return -1.0
        return 0.0
    
    def _calculate_quote_intensity(self, ticks: np.ndarray) -> float:
        """Calculate quote arrival intensity."""
        if len(ticks) < self.window_size:
            return 1.0
        quote_changes = np.sum(np.diff(ticks['bid'][-self.window_size:]) != 0) + \
                       np.sum(np.diff(ticks['ask'][-self.window_size:]) != 0)
        return quote_changes / (2 * (self.window_size - 1)) 