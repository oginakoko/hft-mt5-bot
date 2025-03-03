"""Test configuration and fixtures."""

import pytest
from src.hft_mt5.core.config import Config
import MetaTrader5 as mt5

@pytest.fixture
def mock_config():
    """Create a test configuration."""
    config = Config("test_config.ini")
    config.config['MT5'] = {
        'username': '12345',
        'password': 'test',
        'server': 'TestServer',
    }
    config.config['Trading'] = {
        'symbols': 'EURUSD,USDJPY',
        'max_positions': '5',
        'max_drawdown': '0.2',
        'risk_per_trade': '0.01'
    }
    return config

@pytest.fixture
def mock_mt5_handler(mocker):
    """Mock MT5 handler for testing."""
    mocker.patch('MetaTrader5.initialize', return_value=True)
    mocker.patch('MetaTrader5.login', return_value=True)
    mocker.patch('MetaTrader5.shutdown')
    return mocker.Mock()
