"""Risk management component for HFT strategy."""

import logging
from typing import Dict, Optional
import time
import numpy as np

class RiskManager:
    """Manages trading risk and position sizing."""
    
    def __init__(self, mt5_handler, 
                 max_risk_per_trade: float = 0.01,
                 max_total_risk: float = 0.03,
                 max_positions: int = 5,
                 max_drawdown: float = 0.05):
        """Initialize risk manager.
        
        Args:
            max_risk_per_trade: Maximum risk per trade as fraction of account (default: 1%)
            max_total_risk: Maximum total risk across all positions (default: 3%)
            max_positions: Maximum number of open positions (default: 5)
            max_drawdown: Maximum allowed drawdown before stopping (default: 5%)
        """
        self.mt5_handler = mt5_handler
        self.max_risk_per_trade = max_risk_per_trade
        self.max_total_risk = max_total_risk
        self.max_positions = max_positions
        self.max_drawdown = max_drawdown
        self.logger = logging.getLogger('HFT_Strategy.RiskManager')
        
        # Track positions and risk
        self.positions = {}
        self.total_risk = 0.0
        self.initial_equity = 0.0
        self.last_check_time = 0
        self.min_check_interval = 0.1  # 100ms between risk checks
        
    def initialize(self) -> bool:
        """Initialize risk manager with account information."""
        try:
            account_info = self.mt5_handler.get_account_info()
            if not account_info:
                self.logger.error("Failed to get account info")
                return False
                
            self.initial_equity = account_info['equity']
            self.logger.info(f"Risk manager initialized with equity: {self.initial_equity}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing risk manager: {e}")
            return False
    
    def can_open_position(self, symbol: str) -> bool:
        """Check if a new position can be opened."""
        current_time = time.time()
        
        # Rate limit risk checks
        if current_time - self.last_check_time < self.min_check_interval:
            return False
            
        try:
            # Update positions
            positions = self.mt5_handler.get_positions()
            if "error" in positions:
                return False
                
            # Count positions per symbol
            symbol_positions = sum(1 for p in positions if p['symbol'] == symbol)
            if symbol_positions >= 2:  # Max 2 positions per symbol
                return False
                
            # Check total positions
            if len(positions) >= self.max_positions:
                return False
                
            # Get account info
            account_info = self.mt5_handler.get_account_info()
            if not account_info:
                return False
                
            # Check drawdown
            current_equity = account_info['equity']
            drawdown = 1 - (current_equity / self.initial_equity)
            if drawdown > self.max_drawdown:
                self.logger.warning(f"Max drawdown reached: {drawdown:.2%}")
                return False
                
            # Check margin level
            if account_info['margin_level'] < 200:  # Minimum 200% margin level
                return False
                
            # Calculate total risk
            total_risk = sum(abs(p['profit']) for p in positions) / current_equity
            if total_risk > self.max_total_risk:
                return False
                
            self.last_check_time = current_time
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking position limits: {e}")
            return False
    
    def calculate_position_size(self, symbol: str, signal_strength: float) -> float:
        """Calculate position size based on risk parameters and signal strength."""
        try:
            # Get account info
            account_info = self.mt5_handler.get_account_info()
            if not account_info:
                return 0.0
                
            # Get symbol info
            symbol_info = self.mt5_handler.get_symbol_info(symbol)
            if not symbol_info or "error" in symbol_info:
                return 0.0
                
            # Base position size on free margin and signal strength
            equity = account_info['equity']
            risk_amount = equity * self.max_risk_per_trade * signal_strength
            
            # Calculate position size in lots
            point_value = symbol_info['point'] * symbol_info['trade_tick_value']
            if point_value == 0:
                return 0.0
                
            # Dynamic stop loss based on volatility
            volatility = self._estimate_volatility(symbol)
            stop_loss_points = max(50, min(200, int(volatility * 10000)))
            
            # Calculate maximum position size
            max_position_size = risk_amount / (stop_loss_points * point_value)
            
            # Apply limits
            min_lot = symbol_info['volume_min']
            max_lot = min(symbol_info['volume_max'], max_position_size)
            
            # Scale position size by signal strength
            position_size = min_lot + (max_lot - min_lot) * signal_strength
            
            # Round to symbol lot step
            lot_step = symbol_info['volume_step']
            position_size = round(position_size / lot_step) * lot_step
            
            return max(min_lot, min(position_size, max_lot))
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def _estimate_volatility(self, symbol: str) -> float:
        """Estimate current symbol volatility."""
        try:
            # Get recent ticks
            ticks = self.mt5_handler.get_ticks(symbol, 100)
            if not ticks or "error" in ticks:
                return 0.0001  # Default low volatility
                
            # Calculate tick-by-tick returns
            prices = np.array([tick['price'] for tick in ticks])
            returns = np.diff(prices) / prices[:-1]
            
            # Calculate volatility (standard deviation of returns)
            volatility = np.std(returns)
            
            return max(0.0001, min(0.01, volatility))  # Limit between 0.01% and 1%
            
        except Exception as e:
            self.logger.error(f"Error estimating volatility: {e}")
            return 0.0001
