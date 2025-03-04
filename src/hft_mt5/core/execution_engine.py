"""Execution engine for HFT strategy."""

import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from threading import Lock

@dataclass
class Position:
    ticket: int
    symbol: str
    type: int  # 0 for buy, 1 for sell
    volume: float
    open_price: float
    virtual_sl: float
    virtual_tp: float
    open_time: float

class ExecutionEngine:
    """Handles order execution and position management with virtual SL/TP."""
    
    def __init__(self, mt5_handler):
        self.mt5_handler = mt5_handler
        self.logger = logging.getLogger('HFT_Strategy.ExecutionEngine')
        self.positions: Dict[int, Position] = {}
        self.position_lock = Lock()
        self.last_check_time = 0
        self.check_interval = 0.01  # 10ms position check interval
        
    def execute_signal(self, symbol: str, signal_dir: int, position_size: float,
                      sl_points: int = 50, tp_points: int = 75) -> bool:
        """Execute a trade signal with virtual SL/TP."""
        try:
            # Get current price
            tick = self.mt5_handler.get_last_tick(symbol)
            if not tick or "error" in tick:
                return False
                
            price = tick['ask'] if signal_dir == 0 else tick['bid']
            point = self.mt5_handler.get_symbol_info(symbol).get('point', 0.0001)
            
            # Calculate virtual SL/TP levels
            sl_price = price + (point * sl_points * (-1 if signal_dir == 0 else 1))
            tp_price = price + (point * tp_points * (1 if signal_dir == 0 else -1))
            
            # Open position without actual SL/TP
            result = self.mt5_handler.open_position(
                symbol=symbol,
                trade_type=signal_dir,  # 0 for buy, 1 for sell
                volume=position_size,
                price=price
            )
            
            if "error" in result:
                self.logger.error(f"Failed to open position: {result['error']}")
                return False
                
            # Store position with virtual SL/TP
            ticket = result['ticket']
            position = Position(
                ticket=ticket,
                symbol=symbol,
                type=signal_dir,
                volume=position_size,
                open_price=price,
                virtual_sl=sl_price,
                virtual_tp=tp_price,
                open_time=time.time()
            )
            
            with self.position_lock:
                self.positions[ticket] = position
                
            self.logger.info(f"Opened position {ticket} with virtual SL: {sl_price:.5f}, TP: {tp_price:.5f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
            return False
    
    def check_positions(self) -> None:
        """Check and manage virtual SL/TP for open positions."""
        current_time = time.time()
        
        # Rate limit position checks
        if current_time - self.last_check_time < self.check_interval:
            return
            
        try:
            with self.position_lock:
                positions_to_close = []
                
                for ticket, position in self.positions.items():
                    tick = self.mt5_handler.get_last_tick(position.symbol)
                    if not tick or "error" in tick:
                        continue
                        
                    current_price = tick['bid'] if position.type == 0 else tick['ask']
                    
                    # Check if SL or TP is hit
                    if position.type == 0:  # Long position
                        if current_price <= position.virtual_sl:
                            positions_to_close.append((ticket, "SL"))
                        elif current_price >= position.virtual_tp:
                            positions_to_close.append((ticket, "TP"))
                    else:  # Short position
                        if current_price >= position.virtual_sl:
                            positions_to_close.append((ticket, "SL"))
                        elif current_price <= position.virtual_tp:
                            positions_to_close.append((ticket, "TP"))
                
                # Close positions that hit SL/TP
                for ticket, reason in positions_to_close:
                    position = self.positions[ticket]
                    result = self.mt5_handler.close_position(ticket)
                    
                    if "error" not in result:
                        self.logger.info(f"Closed position {ticket} at {reason}")
                        del self.positions[ticket]
                    else:
                        self.logger.error(f"Failed to close position {ticket}: {result['error']}")
            
            self.last_check_time = current_time
            
        except Exception as e:
            self.logger.error(f"Error checking positions: {e}")
    
    def close_all_positions(self) -> None:
        """Close all open positions."""
        try:
            with self.position_lock:
                for ticket in list(self.positions.keys()):
                    result = self.mt5_handler.close_position(ticket)
                    if "error" not in result:
                        self.logger.info(f"Closed position {ticket}")
                        del self.positions[ticket]
                    else:
                        self.logger.error(f"Failed to close position {ticket}: {result['error']}")
        except Exception as e:
            self.logger.error(f"Error closing all positions: {e}")
