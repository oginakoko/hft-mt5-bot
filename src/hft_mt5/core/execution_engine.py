"""Execution engine for trading operations."""

import time
import logging
from typing import Dict, Optional
from .data_types import Signal

class ExecutionEngine:
    """Handles trade execution and order management."""
    
    def __init__(self, mt5_handler, use_market_orders: bool = True):
        self.mt5_handler = mt5_handler
        self.use_market_orders = use_market_orders
        self.last_trade_time = {}  # Track last trade time per symbol
        self.logger = logging.getLogger('HFT_Strategy.ExecutionEngine')
        
    def execute_signal(self, signal: Signal, position_size: float,
                      stop_loss_pips: float, take_profit_pips: float) -> bool:
        """Execute a trade based on the signal."""
        
        # Get symbol info for price and pip calculations
        symbol_info = self.mt5_handler.get_symbol_info(signal.symbol)
        if not symbol_info or "error" in symbol_info:
            self.logger.error(f"Failed to get symbol info for {signal.symbol}")
            return False
            
        # Calculate stop loss and take profit levels
        pip_size = 10 ** -symbol_info['digits']
        current_price = symbol_info['ask'] if signal.direction > 0 else symbol_info['bid']
        
        if signal.direction > 0:  # Buy
            stop_loss = current_price - stop_loss_pips * pip_size
            take_profit = current_price + take_profit_pips * pip_size
        else:  # Sell
            stop_loss = current_price + stop_loss_pips * pip_size
            take_profit = current_price - take_profit_pips * pip_size
            
        # Place the order
        result = self.mt5_handler.place_order(
            symbol=signal.symbol,
            order_type="BUY" if signal.direction > 0 else "SELL",
            volume=position_size,
            price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        if "error" in result:
            self.logger.error(f"Order failed: {result['error']}")
            return False
            
        self.logger.info(f"Order executed: {signal.symbol} {'BUY' if signal.direction > 0 else 'SELL'} {position_size} lots")
        self.last_trade_time[signal.symbol] = time.time()
        return True
        
    def close_position(self, ticket: int) -> bool:
        """Close a specific position."""
        result = self.mt5_handler.close_position(ticket)
        if "error" in result:
            self.logger.error(f"Failed to close position {ticket}: {result['error']}")
            return False
        return True
        
    def close_all_positions(self) -> bool:
        """Close all open positions."""
        return self.mt5_handler.close_all_positions()
