"""Feature generation component for HFT strategy."""

import numpy as np
from typing import Dict
from .data_types import TickBuffer

class FeatureGenerator:
    """Generates features from tick data for signal generation."""
    
    def __init__(self, window_size: int = 10):  # Shorter window for faster reactions
        self.window_size = window_size
    
    def calculate_features(self, tick_buffer: TickBuffer) -> Dict[str, float]:
        """Calculate features from recent ticks."""
        ticks = tick_buffer.get_recent(self.window_size * 2)  # Get more ticks for better analysis
        if len(ticks) < self.window_size:
            return {}
            
        features = {}
        
        # Price features with shorter windows
        mid_prices = ticks['mid_price']
        features['price_change'] = self._calculate_returns(mid_prices[-5:])  # Ultra-short term
        features['volatility'] = self._calculate_volatility(mid_prices)
        features['price_momentum'] = self._calculate_momentum(mid_prices)
        features['mean_deviation'] = self._calculate_mean_deviation(mid_prices[-7:])  # Short-term mean
        features['price_acceleration'] = self._calculate_acceleration(mid_prices[-3:])  # Recent acceleration
        
        # Volume features with higher sensitivity
        features['volume_intensity'] = self._calculate_volume_intensity(ticks['volume'][-5:])  # Recent volume
        features['volume_trend'] = self._calculate_volume_trend(ticks['volume'])
        features['vwap_diff'] = self._calculate_vwap_difference(ticks[-5:])  # Short-term VWAP
        
        # Spread and liquidity features
        features['spread'] = ticks['spread'][-1]
        features['bid_strength'] = self._calculate_bid_strength(ticks[-5:])  # Recent strength
        features['ask_strength'] = self._calculate_ask_strength(ticks[-5:])
        
        # Microstructure features
        features['tick_pattern'] = self._analyze_tick_pattern(ticks[-7:])  # Recent pattern
        features['trade_sign'] = self._calculate_trade_sign(ticks[-2:])  # Very recent sign
        features['quote_intensity'] = self._calculate_quote_intensity(ticks[-5:])
        
        return features
    
    def _calculate_returns(self, prices: np.ndarray) -> float:
        """Calculate short-term returns."""
        if len(prices) < 2:
            return 0.0
        return (prices[-1] - prices[0]) / prices[0]  # Use first and last price
    
    def _calculate_volatility(self, prices: np.ndarray) -> float:
        """Calculate recent price volatility."""
        if len(prices) < 2:
            return 0.0001
        returns = np.diff(prices) / prices[:-1]
        # Exponentially weighted standard deviation
        weights = np.exp(np.linspace(-1, 0, len(returns)))
        weighted_variance = np.average(returns**2, weights=weights) - np.average(returns, weights=weights)**2
        return np.sqrt(weighted_variance)
    
    def _calculate_momentum(self, prices: np.ndarray) -> float:
        """Calculate price momentum."""
        if len(prices) < self.window_size:
            return 0.0
        # Exponentially weighted momentum
        weights = np.exp(np.linspace(-1, 0, len(prices)))
        weighted_returns = np.diff(prices) / prices[:-1] * weights[1:]
        return np.sum(weighted_returns)
    
    def _calculate_mean_deviation(self, prices: np.ndarray) -> float:
        """Calculate deviation from moving average."""
        if len(prices) < 2:
            return 0.0
        # Exponentially weighted moving average
        weights = np.exp(np.linspace(-1, 0, len(prices)))
        weighted_mean = np.average(prices, weights=weights)
        return (prices[-1] - weighted_mean) / weighted_mean
    
    def _calculate_acceleration(self, prices: np.ndarray) -> float:
        """Calculate price acceleration."""
        if len(prices) < 3:
            return 0.0
        returns = np.diff(prices) / prices[:-1]
        if len(returns) < 2:
            return 0.0
        return (returns[-1] - returns[0]) * 100  # Scaled acceleration
    
    def _calculate_volume_intensity(self, volumes: np.ndarray) -> float:
        """Calculate volume intensity relative to average."""
        if len(volumes) < 2:
            return 1.0
        recent_avg = np.mean(volumes[:-1])
        if recent_avg == 0:
            return 1.0
        return volumes[-1] / recent_avg
    
    def _calculate_volume_trend(self, volumes: np.ndarray) -> float:
        """Calculate volume trend."""
        if len(volumes) < self.window_size:
            return 0.0
        # Exponentially weighted trend
        weights = np.exp(np.linspace(-1, 0, len(volumes)))
        trend = np.polyfit(range(len(volumes)), volumes, 1, w=weights)[0]
        return np.tanh(trend * 5)  # More sensitive scaling
    
    def _calculate_vwap_difference(self, ticks: np.ndarray) -> float:
        """Calculate difference from VWAP."""
        if len(ticks) < 2:
            return 0.0
        volumes = ticks['volume']
        prices = ticks['mid_price']
        if np.sum(volumes) == 0:
            return 0.0
        # Exponentially weighted VWAP
        weights = np.exp(np.linspace(-1, 0, len(volumes)))
        vwap = np.sum(prices * volumes * weights) / np.sum(volumes * weights)
        return (prices[-1] - vwap) / vwap
    
    def _calculate_bid_strength(self, ticks: np.ndarray) -> float:
        """Calculate bid side strength."""
        if len(ticks) < 2:
            return 0.5
        bid_changes = np.diff(ticks['bid'])
        # Exponentially weight recent changes
        weights = np.exp(np.linspace(-1, 0, len(bid_changes)))
        return np.sum((bid_changes > 0) * weights) / np.sum(weights)
    
    def _calculate_ask_strength(self, ticks: np.ndarray) -> float:
        """Calculate ask side strength."""
        if len(ticks) < 2:
            return 0.5
        ask_changes = np.diff(ticks['ask'])
        # Exponentially weight recent changes
        weights = np.exp(np.linspace(-1, 0, len(ask_changes)))
        return np.sum((ask_changes > 0) * weights) / np.sum(weights)
    
    def _analyze_tick_pattern(self, ticks: np.ndarray) -> float:
        """Analyze tick patterns for predictive signals."""
        if len(ticks) < 2:
            return 0.0
        mid_prices = ticks['mid_price']
        price_changes = np.diff(mid_prices)
        # Exponentially weight recent patterns
        weights = np.exp(np.linspace(-1, 0, len(price_changes)))
        weighted_ups = np.sum((price_changes > 0) * weights)
        weighted_downs = np.sum((price_changes < 0) * weights)
        return (weighted_ups - weighted_downs) / np.sum(weights)
    
    def _calculate_trade_sign(self, ticks: np.ndarray) -> float:
        """Calculate trade sign based on tick rule."""
        if len(ticks) < 2:
            return 0.0
        last_tick = ticks[-1]
        prev_tick = ticks[-2]
        # More aggressive sign calculation
        if last_tick['mid_price'] > prev_tick['mid_price']:
            return 1.0
        elif last_tick['mid_price'] < prev_tick['mid_price']:
            return -1.0
        # Use spread for tie-breaking
        elif last_tick['spread'] < prev_tick['spread']:
            return 0.5  # Slightly bullish on spread compression
        elif last_tick['spread'] > prev_tick['spread']:
            return -0.5  # Slightly bearish on spread expansion
        return 0.0
    
    def _calculate_quote_intensity(self, ticks: np.ndarray) -> float:
        """Calculate quote arrival intensity."""
        if len(ticks) < 2:
            return 1.0
        # Count both bid and ask changes with exponential weighting
        weights = np.exp(np.linspace(-1, 0, len(ticks)-1))
        quote_changes = (np.diff(ticks['bid']) != 0) | (np.diff(ticks['ask']) != 0)
        weighted_changes = np.sum(quote_changes * weights)
        return weighted_changes / np.sum(weights) 