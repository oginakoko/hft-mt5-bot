"""Strategy coordinator for managing HFT components."""

import logging
from typing import Dict, Optional
from .mt5_handler import MT5Handler
from .feature_generator import FeatureGenerator
from .signal_generator import SignalGenerator
from .risk_manager import RiskManager
from .execution_engine import ExecutionEngine
from .data_types import TickBuffer

class StrategyCoordinator:
    """Coordinates all strategy components."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('HFT_Strategy.Coordinator')
        
        # Initialize components
        self.mt5_handler = MT5Handler(config)
        self.feature_generator = FeatureGenerator(
            window_size=config.getint('HFT', 'tick_features_window', fallback=20)
        )
        self.signal_generator = SignalGenerator(
            threshold=config.getfloat('HFT', 'signal_threshold', fallback=0.7)
        )
        self.risk_manager = RiskManager(
            max_positions=config.getint('Trading', 'max_positions', fallback=5),
            max_drawdown=config.getfloat('Trading', 'max_drawdown', fallback=0.2),
            risk_per_trade=config.getfloat('Trading', 'risk_per_trade', fallback=0.01),
            stop_loss_pips=config.getfloat('Trading', 'stop_loss_pips', fallback=10),
            take_profit_pips=config.getfloat('Trading', 'take_profit_pips', fallback=20)
        )
        self.execution_engine = ExecutionEngine(
            use_market_orders=config.getboolean('Trading', 'use_market_orders', fallback=True)
        )
        
        # Initialize data structures
        self.symbols = config.get('Trading', 'symbols', fallback='EURUSD,USDJPY,GBPUSD').split(',')
        self.tick_buffers = {
            symbol: TickBuffer(max_size=config.getint('HFT', 'tick_buffer_size', fallback=1000))
            for symbol in self.symbols
        }
        
    def start(self) -> bool:
        """Start the strategy coordinator."""
        if not self.mt5_handler.connect():
            self.logger.error("Failed to connect to MT5")
            return False
            
        self.risk_manager.initialize()
        self.logger.info("Strategy coordinator started successfully")
        return True
        
    def stop(self):
        """Stop the strategy coordinator."""
        self.mt5_handler.disconnect()
        self.logger.info("Strategy coordinator stopped")
        
    def get_account_info(self) -> Dict:
        """Get current account information."""
        return self.mt5_handler.get_account_info()
        
    def get_positions(self) -> Dict:
        """Get current open positions."""
        return self.mt5_handler.get_positions()
        
    def close_all_positions(self) -> bool:
        """Close all open positions."""
        return self.mt5_handler.close_all_positions()
