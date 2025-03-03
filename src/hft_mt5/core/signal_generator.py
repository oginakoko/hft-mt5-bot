"""Signal generation component for HFT strategy."""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
import logging
from .data_types import TickBuffer, Signal

class SignalGenerator:
    """Generates trading signals from calculated features."""
    
    def __init__(self, threshold: float = 0.3):  # Lower threshold for more frequent signals
        self.threshold = threshold
        self.logger = logging.getLogger('HFT_Strategy.SignalGenerator')
        self.last_signal_time = {}  # Track last signal time per symbol
        self.min_signal_interval = 0.1  # Minimum time between signals (100ms)
    
    def generate_signal(self, symbol: str, features: Dict[str, float], timestamp: int) -> Signal:
        """Generate trading signal from features."""
        if not features:
            return self._create_neutral_signal(symbol, timestamp, features)
            
        # Check signal interval
        if symbol in self.last_signal_time:
            time_since_last = timestamp - self.last_signal_time[symbol]
            if time_since_last < self.min_signal_interval:
                return self._create_neutral_signal(symbol, timestamp, features)
        
        # Calculate signal components with weights
        signals = {
            'price': self._calculate_price_signal(features) * 0.4,
            'volume': self._calculate_volume_signal(features) * 0.3,
            'momentum': self._calculate_momentum_signal(features) * 0.2,
            'microstructure': self._calculate_microstructure_signal(features) * 0.1
        }
        
        # Combine weighted signals
        combined_strength = sum(signals.values())
        
        # Dynamic threshold based on volatility
        dynamic_threshold = self.threshold
        if 'volatility' in features:
            dynamic_threshold *= max(0.5, min(2.0, features['volatility']))
        
        # Determine direction and strength
        if abs(combined_strength) > dynamic_threshold:
            direction = 1 if combined_strength > 0 else -1
            strength = min(1.0, abs(combined_strength))
            self.last_signal_time[symbol] = timestamp
        else:
            return self._create_neutral_signal(symbol, timestamp, features)
            
        return Signal(
            symbol=symbol,
            direction=direction,
            strength=strength,
            timestamp=timestamp,
            features=features
        )
    
    def _create_neutral_signal(self, symbol: str, timestamp: int, features: Dict[str, float]) -> Signal:
        """Create a neutral signal."""
        return Signal(symbol=symbol, direction=0, strength=0.0, 
                     timestamp=timestamp, features=features)
    
    def _calculate_price_signal(self, features: Dict[str, float]) -> float:
        """Calculate signal component from price features."""
        if 'price_change' not in features:
            return 0.0
            
        signal = 0.0
        
        # Price change momentum
        if 'price_change' in features:
            signal += np.tanh(features['price_change'] * 10)
        
        # Bid/Ask spread analysis
        if 'spread' in features:
            spread_factor = 1 - min(1, features['spread'] / 0.0001)  # Normalize spread
            signal *= spread_factor
        
        # Order book imbalance
        if 'bid_strength' in features and 'ask_strength' in features:
            imbalance = features['bid_strength'] - features['ask_strength']
            signal += np.tanh(imbalance * 5)
        
        return np.clip(signal / 2, -1, 1)
    
    def _calculate_volume_signal(self, features: Dict[str, float]) -> float:
        """Calculate signal component from volume features."""
        if 'volume_intensity' not in features:
            return 0.0
            
        signal = 0.0
        
        # Volume spike detection
        if features['volume_intensity'] > 2.0:  # Volume spike threshold
            if 'price_change' in features:
                signal = np.sign(features['price_change']) * np.log1p(features['volume_intensity'])
        
        # Volume trend
        if 'volume_trend' in features:
            signal += np.tanh(features['volume_trend'] * 3)
        
        # Volume weighted price change
        if 'vwap_diff' in features:
            signal += np.tanh(features['vwap_diff'] * 5)
        
        return np.clip(signal, -1, 1)
    
    def _calculate_momentum_signal(self, features: Dict[str, float]) -> float:
        """Calculate momentum-based signal component."""
        signal = 0.0
        
        # Short-term momentum
        if 'price_momentum' in features:
            signal += np.tanh(features['price_momentum'] * 3)
        
        # Mean reversion
        if 'mean_deviation' in features:
            signal -= np.tanh(features['mean_deviation'] * 2)
        
        # Acceleration
        if 'price_acceleration' in features:
            signal += np.tanh(features['price_acceleration'])
        
        return np.clip(signal, -1, 1)
    
    def _calculate_microstructure_signal(self, features: Dict[str, float]) -> float:
        """Calculate market microstructure signal component."""
        signal = 0.0
        
        # Tick pattern analysis
        if 'tick_pattern' in features:
            signal += features['tick_pattern'] * 0.5
        
        # Trade sign analysis
        if 'trade_sign' in features:
            signal += features['trade_sign'] * 0.3
        
        # Quote intensity
        if 'quote_intensity' in features:
            signal += np.tanh(features['quote_intensity'] - 1) * 0.2
        
        return np.clip(signal, -1, 1)
