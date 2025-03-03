"""Risk management component for HFT strategy."""

import logging
from typing import Dict, Optional

class RiskManager:
    """Manages trading risk and position sizing."""
    
    def __init__(self, mt5_handler,
                 max_risk_per_trade: float = 0.02,
                 max_total_risk: float = 0.06,
                 max_positions: int = 3,
                 max_drawdown: float = 0.1):
        """Initialize risk manager with risk parameters."""
        self.mt5_handler = mt5_handler
        self.max_risk_per_trade = max_risk_per_trade
        self.max_total_risk = max_total_risk
        self.max_positions = max_positions
        self.max_drawdown = max_drawdown
        self.logger = logging.getLogger('HFT_Strategy.RiskManager')
        
    def initialize(self) -> bool:
        """Initialize risk manager with account info."""
        account_info = self.mt5_handler.get_account_info()
        if not account_info or "error" in account_info:
            self.logger.error("Failed to get account info")
            return False
        return True
        
    def can_open_position(self, symbol: str) -> bool:
        """Check if a new position can be opened."""
        # Check number of open positions
        positions = self.mt5_handler.get_positions()
        if "error" in positions:
            self.logger.error("Failed to get positions")
            return False
            
        symbol_positions = [p for p in positions if p['symbol'] == symbol]
        if len(symbol_positions) >= self.max_positions:
            self.logger.info(f"Maximum positions ({self.max_positions}) reached for {symbol}")
            return False
            
        # Check drawdown
        if not self._check_drawdown():
            return False
            
        return True
        
    def _check_drawdown(self) -> bool:
        """Check if current drawdown is within limits."""
        account_info = self.mt5_handler.get_account_info()
        if not account_info or "error" in account_info:
            self.logger.error("Failed to get account info for drawdown check")
            return False
            
        equity = account_info['equity']
        balance = account_info['balance']
        
        if balance == 0:
            self.logger.error("Account balance is zero")
            return False
            
        current_drawdown = (balance - equity) / balance
        if current_drawdown > self.max_drawdown:
            self.logger.warning(f"Maximum drawdown exceeded: {current_drawdown:.2%}")
            return False
            
        return True
        
    def calculate_position_size(self, symbol: str, risk_amount: float) -> float:
        """Calculate position size based on risk parameters."""
        # Get symbol info for calculations
        symbol_info = self.mt5_handler.get_symbol_info(symbol)
        if not symbol_info or "error" in symbol_info:
            self.logger.error(f"Failed to get symbol info for {symbol}")
            return 0.0
            
        # Get account info
        account_info = self.mt5_handler.get_account_info()
        if not account_info or "error" in account_info:
            self.logger.error("Failed to get account info")
            return 0.0
            
        # Calculate position size based on risk
        equity = account_info['equity']
        risk_money = equity * risk_amount
        
        # Ensure risk doesn't exceed maximum
        max_risk_money = equity * self.max_risk_per_trade
        risk_money = min(risk_money, max_risk_money)
        
        # Calculate lot size based on risk money
        min_lot = symbol_info['volume_min']
        max_lot = symbol_info['volume_max']
        lot_step = symbol_info['volume_step']
        
        # Calculate lots based on risk money and current price
        price = symbol_info['ask']
        lot_size = risk_money / (price * 100000)  # Standard lot is 100,000 units
        
        # Round to nearest valid lot size
        lot_size = round(lot_size / lot_step) * lot_step
        
        # Ensure lot size is within limits
        lot_size = max(min_lot, min(lot_size, max_lot))
        
        return lot_size
