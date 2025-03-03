"""Tests for risk management functionality."""

import pytest
from src.hft_mt5.core.risk_manager import RiskManager

def test_risk_manager_initialization(mock_config, mock_mt5_handler):
    """Test risk manager initialization."""
    risk_manager = RiskManager(mock_config, mock_mt5_handler)
    assert risk_manager.max_drawdown == 0.2
    assert risk_manager.risk_per_trade == 0.01

def test_drawdown_calculation(mock_config, mock_mt5_handler):
    """Test drawdown calculations."""
    risk_manager = RiskManager(mock_config, mock_mt5_handler)
    
    # Mock account info
    mock_mt5_handler.get_account_info.return_value = {'equity': 1000.0}
    
    # Initialize
    risk_manager.initialize()
    assert risk_manager.initial_equity == 1000.0
    
    # Simulate drawdown
    mock_mt5_handler.get_account_info.return_value = {'equity': 900.0}
    risk_manager.update()
    assert risk_manager.drawdown == 0.1  # 10% drawdown
    
    # Test max drawdown breach
    mock_mt5_handler.get_account_info.return_value = {'equity': 750.0}
    risk_manager.update()
    assert risk_manager.drawdown == 0.25  # 25% drawdown
    mock_mt5_handler.close_all_positions.assert_called_once()
