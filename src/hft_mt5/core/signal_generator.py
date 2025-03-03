"""Signal generation component for HFT strategy."""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
import logging
from .data_types import TickBuffer, Signal

class SignalGenerator:
    """Generates trading signals from calculated features."""
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.logger = logging.getLogger('HFT_Strategy.SignalGenerator')
    
    def generate_signal(self, symbol: str, features: Dict[str, float], timestamp: int) -> Signal:
        """Generate trading signal from features."""
        if not features:
            return Signal(symbol=symbol, direction=0, strength=0.0, 
                        timestamp=timestamp, features=features)
        
        # Calculate signal components
        price_signal = self._calculate_price_signal(features)
        volume_signal = self._calculate_volume_signal(features)
        
        # Combine signals
        combined_strength = (price_signal + volume_signal) / 2
        
        # Determine direction and strength
        if abs(combined_strength) > self.threshold:
            direction = 1 if combined_strength > 0 else -1
            strength = abs(combined_strength)
        else:
            direction = 0
            strength = 0.0
            
        return Signal(
            symbol=symbol,
            direction=direction,
            strength=strength,
            timestamp=timestamp,
            features=features
        )
    
    def _calculate_price_signal(self, features: Dict[str, float]) -> float:
        """Calculate signal component from price features."""
        if 'price_change' not in features or 'volatility' not in features:
            return 0.0
            
        # Normalize price change by volatility
        if features['volatility'] > 0:
            signal = features['price_change'] / features['volatility']
        else:
            signal = 0.0
            
        # Add bid/ask strength influence
        signal += (features.get('bid_strength', 0.5) - 0.5) * 2
        signal += (features.get('ask_strength', 0.5) - 0.5) * 2
        
        return np.clip(signal / 4, -1, 1)  # Normalize to [-1, 1]
    
    def _calculate_volume_signal(self, features: Dict[str, float]) -> float:
        """Calculate signal component from volume features."""
        if 'volume_intensity' not in features:
            return 0.0
            
        # Volume intensity relative to price change
        if abs(features.get('price_change', 0)) > 0:
            signal = np.sign(features['price_change']) * np.log1p(features['volume_intensity'])
        else:
            signal = 0.0
            
        return np.clip(signal / 5, -1, 1)  # Normalize to [-1, 1]
