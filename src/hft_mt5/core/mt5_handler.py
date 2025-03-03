"""MetaTrader 5 connection handler."""

import MetaTrader5 as mt5
import logging
from typing import Optional, List, Dict
from datetime import datetime
import time
from .config import Config

class MT5Handler:
    """Handles connection and interaction with MetaTrader 5."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger('HFT_Strategy.MT5Handler')
        self.connected = False
        
    def verify_installation(self) -> bool:
        """Verify MT5 installation and version."""
        self.logger.info("Verifying MT5 Installation")
        if not mt5.initialize():
            self.logger.error(f"MetaTrader5 package initialization failed: {mt5.last_error()}")
            return False
            
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            self.logger.error("Failed to get terminal info")
            return False
            
        self.logger.info(f"MetaTrader5 package version: {mt5.__version__}")
        self.logger.info(f"Terminal info:")
        self.logger.info(f"  Company: {terminal_info.company}")
        self.logger.info(f"  Terminal: {terminal_info.name}")
        self.logger.info(f"  Connected: {terminal_info.connected}")
        return True
        
    def connect(self) -> bool:
        """Initialize connection to MT5 terminal."""
        if self.connected:
            return True
            
        # First shutdown any existing connections
        mt5.shutdown()
        
        self.logger.info("\n=== Connecting to MT5 ===")
        
        # Get MT5 path from config
        mt5_path = self.config.get('MT5', 'path')
        self.logger.info(f"Using MT5 path: {mt5_path}")
        
        # Initialize MT5
        self.logger.info("Initializing MT5...")
        if not mt5.initialize(path=mt5_path):
            error = mt5.last_error()
            self.logger.error(f"Initialize failed. Error code: {error[0]}, Message: {error[1]}")
            return False
            
        # Get terminal info
        self.logger.info("Getting terminal info...")
        terminal_info = mt5.terminal_info()
        if terminal_info is not None:
            self.logger.info(f"MetaTrader5 version: {mt5.__version__}")
            self.logger.info(f"Terminal info:")
            self.logger.info(f"  Company: {terminal_info.company}")
            self.logger.info(f"  Name: {terminal_info.name}")
            self.logger.info(f"  Connected: {terminal_info.connected}")
            self.logger.info(f"  Path: {terminal_info.path}")
            
            if not terminal_info.connected:
                self.logger.error("Terminal is not connected to broker")
                mt5.shutdown()
                return False
        else:
            self.logger.error("Failed to get terminal info")
            return False
        
        # Login to the account
        username = self.config.getint('MT5', 'username')
        password = self.config.get('MT5', 'password')
        server = self.config.get('MT5', 'server')
        
        self.logger.info(f"\nAttempting login...")
        self.logger.info(f"Username: {username}")
        self.logger.info(f"Server: {server}")
        
        # Add retry logic for login
        max_retries = self.config.getint('MT5', 'retries', fallback=3)
        retry_delay = self.config.getfloat('MT5', 'retry_delay', fallback=1.0)
        
        for attempt in range(max_retries):
            login_result = mt5.login(
                login=username,
                password=password,
                server=server
            )
            
            if login_result:
                break
                
            error = mt5.last_error()
            self.logger.warning(f"Login attempt {attempt + 1} failed. Error code: {error[0]}, Message: {error[1]}")
            
            if attempt < max_retries - 1:
                self.logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        if not login_result:
            error = mt5.last_error()
            self.logger.error(f"All login attempts failed. Error code: {error[0]}, Message: {error[1]}")
            mt5.shutdown()
            return False
        
        # Verify connection with account info
        self.logger.info("\nGetting account info...")
        account_info = mt5.account_info()
        if account_info is not None:
            self.connected = True
            self.logger.info(f"Account: {account_info.login}")
            self.logger.info(f"Name: {account_info.name}")
            self.logger.info(f"Server: {account_info.server}")
            self.logger.info(f"Balance: ${account_info.balance:.2f}")
            self.logger.info(f"Equity: ${account_info.equity:.2f}")
            return True
        else:
            self.logger.error("Failed to get account info")
            mt5.shutdown()
            return False
    
    def disconnect(self):
        """Shutdown MT5 connection"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            self.logger.info("Disconnected from MT5")
    
    def get_symbols(self) -> List[str]:
        """Get available symbols from MT5"""
        if not self.connected:
            self.logger.error("Not connected to MT5")
            return []
        
        symbols = mt5.symbols_get()
        return [symbol.name for symbol in symbols]
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        if not self.connected:
            self.logger.error("Not connected to MT5")
            return {}
        
        account_info = mt5.account_info()
        if account_info is None:
            return {}
        
        return {
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'free_margin': account_info.margin_free,
            'profit': account_info.profit,
            'leverage': account_info.leverage,
            'currency': account_info.currency
        }
        
    def get_positions(self) -> List[Dict]:
        """Get all open positions."""
        if not self.connected:
            return []
            
        positions = mt5.positions_get()
        if positions is None:
            return []
            
        return [
            {
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                'volume': pos.volume,
                'open_price': pos.price_open,
                'current_price': pos.price_current,
                'sl': pos.sl,
                'tp': pos.tp,
                'profit': pos.profit,
                'swap': pos.swap,
                'time': datetime.fromtimestamp(pos.time).strftime('%Y-%m-%d %H:%M:%S')
            }
            for pos in positions
        ]
        
    def place_order(self, symbol: str, order_type: str, volume: float, 
                   price: Optional[float] = None, 
                   stop_loss: Optional[float] = None, 
                   take_profit: Optional[float] = None) -> Dict:
        """Place a market or pending order."""
        if not self.connected:
            return {"error": "Not connected"}
            
        # Define order type
        mt5_order_type = mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL
        
        # Prepare the request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": mt5_order_type,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Add optional parameters
        if price is not None:
            request["price"] = price
        if stop_loss is not None:
            request["sl"] = stop_loss
        if take_profit is not None:
            request["tp"] = take_profit
            
        # Send the order
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {"error": f"Order failed: {result.comment}"}
            
        return {
            "ticket": result.order,
            "volume": volume,
            "price": result.price,
            "comment": result.comment
        }
        
    def close_position(self, ticket: int) -> Dict:
        """Close a specific position."""
        if not self.connected:
            return {"error": "Not connected"}
            
        # Get position details
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            return {"error": "Position not found"}
            
        position = position[0]
        
        # Prepare close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "position": ticket,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send the request
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {"error": f"Close failed: {result.comment}"}
            
        return {
            "ticket": result.order,
            "price": result.price,
            "comment": result.comment
        }
        
    def close_all_positions(self) -> bool:
        """Close all open positions."""
        success = True
        for position in self.get_positions():
            result = self.close_position(position['ticket'])
            if "error" in result:
                success = False
        return success
        
    def get_symbol_info(self, symbol: str) -> Dict:
        """Get symbol information."""
        if not self.connected:
            return {"error": "Not connected"}
            
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {"error": "Symbol not found"}
            
        return {
            "bid": symbol_info.bid,
            "ask": symbol_info.ask,
            "spread": symbol_info.spread,
            "digits": symbol_info.digits,
            "min_lot": symbol_info.volume_min,
            "max_lot": symbol_info.volume_max,
            "lot_step": symbol_info.volume_step
        } 