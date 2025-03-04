"""Signal generation component for HFT strategy."""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
import logging
from .data_types import TickBuffer, Signal

class SignalGenerator:
    """Generates trading signals from calculated features."""
    
    def __init__(self, threshold: float = 0.1):  # Ultra-low threshold
        self.threshold = threshold
        self.logger = logging.getLogger('HFT_Strategy.SignalGenerator')
        self.last_signal_time = {}  # Track last signal time per symbol
        self.min_signal_interval = 0.01  # 10ms minimum between signals - ultra aggressive
    
    def generate_signal(self, symbol: str, features: Dict[str, float], timestamp: int) -> Signal:
        """Generate trading signal from features."""
        if not features:
            return self._create_neutral_signal(symbol, timestamp, features)
            
        # Check signal interval
        if symbol in self.last_signal_time:
            time_since_last = timestamp / 1000 - self.last_signal_time[symbol]  # Convert to seconds
            if time_since_last < self.min_signal_interval:
                return self._create_neutral_signal(symbol, timestamp, features)
        
        # Calculate signal components with adjusted weights for ultra-fast trading
        signals = {
            'price': self._calculate_price_signal(features) * 0.6,  # Even more weight on price
            'volume': self._calculate_volume_signal(features) * 0.2,
            'momentum': self._calculate_momentum_signal(features) * 0.15,
            'microstructure': self._calculate_microstructure_signal(features) * 0.05
        }
        
        # Combine weighted signals
        combined_strength = sum(signals.values())
        
        # Ultra-aggressive dynamic threshold
        dynamic_threshold = self.threshold
        if 'volatility' in features:
            # Much lower threshold during high volatility
            dynamic_threshold *= max(0.2, min(1.0, 0.8 - features['volatility']))
        
        # Determine direction and strength with ultra-low threshold
        if abs(combined_strength) > dynamic_threshold:
            direction = 1 if combined_strength > 0 else -1
            strength = min(1.0, abs(combined_strength))
            self.last_signal_time[symbol] = timestamp / 1000  # Store in seconds
            
            # Log signal generation
            self.logger.info(f"Generated signal for {symbol}: dir={direction}, strength={strength:.3f}")
            
            return Signal(
                symbol=symbol,
                direction=direction,
                strength=strength,
                timestamp=timestamp,
                features=features
            )
        
        return self._create_neutral_signal(symbol, timestamp, features)
    
    def _calculate_price_signal(self, features: Dict[str, float]) -> float:
        """Calculate signal component from price features."""
        if 'price_change' not in features:
            return 0.0
            
        signal = 0.0
        
        # Ultra-sensitive price change momentum
        if 'price_change' in features:
            signal += np.tanh(features['price_change'] * 30)  # Even more sensitive
        
        # Bid/Ask spread analysis - ultra-aggressive during tight spreads
        if 'spread' in features:
            spread_factor = 1 - min(1, features['spread'] / 0.00002)  # Even more sensitive to tight spreads
            signal *= spread_factor
        
        # Order book imbalance - maximum weight
        if 'bid_strength' in features and 'ask_strength' in features:
            imbalance = features['bid_strength'] - features['ask_strength']
            signal += np.tanh(imbalance * 15)  # Maximum sensitivity
        
        return np.clip(signal / 2, -1, 1)
    
    def _calculate_volume_signal(self, features: Dict[str, float]) -> float:
        """Calculate signal component from volume features."""
        if 'volume_intensity' not in features:
            return 0.0
            
        signal = 0.0
        
        # Ultra-sensitive volume spike detection
        if features['volume_intensity'] > 1.2:  # Even lower threshold
            if 'price_change' in features:
                signal = np.sign(features['price_change']) * np.log1p(features['volume_intensity'] * 1.5)
        
        # Volume trend - maximum weight
        if 'volume_trend' in features:
            signal += np.tanh(features['volume_trend'] * 8)
        
        # VWAP difference - ultra-sensitive
        if 'vwap_diff' in features:
            signal += np.tanh(features['vwap_diff'] * 15)
        
        return np.clip(signal, -1, 1)
    
    def _calculate_momentum_signal(self, features: Dict[str, float]) -> float:
        """Calculate momentum-based signal component."""
        signal = 0.0
        
        # Ultra-aggressive momentum
        if 'price_momentum' in features:
            signal += np.tanh(features['price_momentum'] * 8)
        
        # Mean reversion - minimal weight
        if 'mean_deviation' in features:
            signal -= np.tanh(features['mean_deviation'] * 0.5)
        
        # Acceleration - maximum weight
        if 'price_acceleration' in features:
            signal += np.tanh(features['price_acceleration'] * 3)
        
        return np.clip(signal, -1, 1)
    
    def _calculate_microstructure_signal(self, features: Dict[str, float]) -> float:
        """Calculate market microstructure signal component."""
        signal = 0.0
        
        # Tick pattern analysis - ultra-aggressive
        if 'tick_pattern' in features:
            signal += features['tick_pattern'] * 0.9
        
        # Trade sign analysis - maximum aggression
        if 'trade_sign' in features:
            signal += features['trade_sign'] * 0.8
        
        # Quote intensity - ultra-sensitive
        if 'quote_intensity' in features:
            signal += np.tanh((features['quote_intensity'] - 1) * 3) * 0.4
        
        return np.clip(signal, -1, 1)
    
    def _create_neutral_signal(self, symbol: str, timestamp: int, features: Dict[str, float]) -> Signal:
        """Create a neutral signal."""
        return Signal(symbol=symbol, direction=0, strength=0.0, 
                     timestamp=timestamp, features=features)
