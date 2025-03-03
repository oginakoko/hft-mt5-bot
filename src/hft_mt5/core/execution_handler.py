"""Advanced execution handling with error recovery."""

import time
from typing import Optional, Dict, List
import MetaTrader5 as mt5
from ..utils.logger import logger

class ExecutionHandler:
    """Handles order execution with retry logic and error recovery."""
    
    def __init__(self, config):
        self.config = config
        self.max_retries = config.getint('Trading', 'max_retries', 3)
        self.retry_delay = config.getfloat('Trading', 'retry_delay_ms', 100) / 1000
        self.last_errors: List[Dict] = []
        
    def execute_order(self, order_params: Dict) -> Optional[int]:
        """Execute order with retry logic."""
        for attempt in range(self.max_retries):
            try:
                # Update current price
                tick = mt5.symbol_info_tick(order_params['symbol'])
                if tick is None:
                    raise ValueError(f"Failed to get tick for {order_params['symbol']}")
                
                # Update order price
                if order_params['type'] == mt5.ORDER_TYPE_BUY:
                    order_params['price'] = tick.ask
                else:
                    order_params['price'] = tick.bid
                
                # Send order
                result = mt5.order_send(order_params)
                
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    error = {
                        'code': result.retcode,
                        'message': f"Order failed: {result.comment}",
                        'timestamp': time.time()
                    }
                    self.last_errors.append(error)
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    
                    logger.error(f"Order failed after {attempt + 1} attempts: {error['message']}")
                    return None
                
                return result.order
                
            except Exception as e:
                logger.error(f"Execution error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None
    
    def close_position(self, position_ticket: int, deviation: int = 10) -> bool:
        """Close position with retry logic."""
        for attempt in range(self.max_retries):
            try:
                position = mt5.positions_get(ticket=position_ticket)
                if not position:
                    logger.error(f"Position {position_ticket} not found")
                    return False
                
                position = position[0]
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "position": position_ticket,
                    "symbol": position.symbol,
                    "volume": position.volume,
                    "type": mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
                    "price": mt5.symbol_info_tick(position.symbol).bid if position.type == 0 else mt5.symbol_info_tick(position.symbol).ask,
                    "deviation": deviation,
                    "magic": 123456,
                    "comment": "Close position",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                result = mt5.order_send(request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    logger.error(f"Failed to close position after {attempt + 1} attempts")
                    return False
                
                return True
                
            except Exception as e:
                logger.error(f"Error closing position on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False
    
    def get_error_stats(self) -> Dict:
        """Get statistics about recent execution errors."""
        if not self.last_errors:
            return {}
            
        error_counts = {}
        for error in self.last_errors[-100:]:  # Look at last 100 errors
            code = error['code']
            error_counts[code] = error_counts.get(code, 0) + 1
            
        return {
            'total_errors': len(self.last_errors),
            'recent_error_counts': error_counts,
            'last_error': self.last_errors[-1] if self.last_errors else None
        }
