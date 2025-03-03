"""Signal processing and filtering component."""

from typing import Dict, List, Optional
from dataclasses import dataclass
import time
import numpy as np
from ..utils.logger import logger
from .data_types import Signal

@dataclass
class FilteredSignal:
    """Enhanced signal with filtering metadata."""
    original: Signal
    filtered_strength: float
    timestamp: float
    metadata: Dict

class SignalProcessor:
    """Processes and filters trading signals."""
    
    def __init__(self, config):
        self.config = config
        self.signal_history: Dict[str, List[Signal]] = {}
        self.threshold = config.getfloat('HFT', 'signal_threshold', 0.7)
        self.history_window = config.getint('HFT', 'signal_history_window', 100)
        
    def process_signal(self, signal: Signal) -> Optional[FilteredSignal]:
        """Process and filter a trading signal."""
        if not self._update_history(signal):
            return None
            
        # Apply filtering logic
        filtered_strength = self._apply_filters(signal)
        if filtered_strength < self.threshold:
            return None
            
        return FilteredSignal(
            original=signal,
            filtered_strength=filtered_strength,
            timestamp=time.time(),
            metadata=self._generate_metadata(signal)
        )
    
    def _update_history(self, signal: Signal) -> bool:
        """Update signal history for the symbol."""
        if signal.symbol not in self.signal_history:
            self.signal_history[signal.symbol] = []
            
        history = self.signal_history[signal.symbol]
        history.append(signal)
        
        # Maintain window size
        if len(history) > self.history_window:
            history.pop(0)
            
        return len(history) >= 3  # Minimum history needed
        
    def _apply_filters(self, signal: Signal) -> float:
        """Apply filtering logic to signal strength."""
        history = self.signal_history[signal.symbol]
        
        # Base strength
        strength = signal.strength
        
        # Momentum confirmation
        if len(history) >= 3:
            prev_directions = [s.direction for s in history[-3:]]
            if all(d == signal.direction for d in prev_directions):
                strength *= 1.2  # Boost strength for consistent direction
            elif any(d != signal.direction for d in prev_directions):
                strength *= 0.8  # Reduce strength for direction changes
        
        # Volatility adjustment
        if 'volatility' in signal.features:
            vol = signal.features['volatility']
            if vol > 0.001:  # High volatility
                strength *= 0.9  # Reduce confidence
                
        return min(1.0, max(0.0, strength))
    
    def _generate_metadata(self, signal: Signal) -> Dict:
        """Generate additional metadata for signal analysis."""
        history = self.signal_history[signal.symbol]
        
        return {
            'avg_strength': np.mean([s.strength for s in history[-10:]]),
            'direction_changes': sum(1 for i in range(1, len(history)) 
                                  if history[i].direction != history[i-1].direction),
            'feature_stability': self._calculate_feature_stability(history[-10:])
        }
    
    def _calculate_feature_stability(self, signals: List[Signal]) -> float:
        """Calculate stability of signal features over time."""
        if not signals or not signals[0].features:
            return 0.0
            
        # Calculate standard deviation of each feature
        stabilities = []
        for feature in signals[0].features.keys():
            values = [s.features.get(feature, 0) for s in signals]
            if values:
                stabilities.append(np.std(values))
                
        return 1.0 / (1.0 + np.mean(stabilities)) if stabilities else 0.0
