"""Tests for signal generation functionality."""

import pytest
import numpy as np
from src.hft_mt5.core.signal_generator import SignalGenerator
from src.hft_mt5.core.data_types import TickBuffer, Tick

def test_signal_generation(mock_config):
    """Test basic signal generation."""
    generator = SignalGenerator(mock_config)
    
    # Create mock tick buffer
    buffer = TickBuffer("EURUSD", max_size=100)
    
    # Add mock ticks with upward trend
    for i in range(20):
        tick = Tick(
            symbol="EURUSD",
            bid=1.1000 + i * 0.0001,
            ask=1.1001 + i * 0.0001,
            time=1000 + i,
            volume=1.0
        )
        buffer.add_tick(tick)
    
    # Generate signal
    signal = generator.generate_signal(buffer)
    assert signal.direction == 1  # Should detect upward trend
    assert signal.strength > 0.7  # Should be strong signal
