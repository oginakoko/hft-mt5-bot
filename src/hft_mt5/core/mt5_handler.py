"""MetaTrader 5 connection handler."""

try:
    import MetaTrader5 as mt5
except ImportError:
    raise ImportError("MetaTrader5 package is not installed. Please install it with: pip install MetaTrader5")

import logging
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import time
import os
import psutil
from .config import Config

class MT5Handler:
    """Handles connection and interaction with MetaTrader 5."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger('HFT_Strategy.MT5Handler')
        self.connected = False
        
        # Verify MT5 package is properly installed
        if not hasattr(mt5, "__version__"):
            self.logger.error("MetaTrader5 package is not properly installed")
            raise RuntimeError("MetaTrader5 package is not properly installed")
            
        self.logger.info(f"MetaTrader5 package version: {mt5.__version__}")
        
    def _find_mt5_instances(self) -> List[Tuple[str, str]]:
        """Find all running MT5 instances and their paths."""
        mt5_instances = []
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if proc.info['name'].lower() in ['terminal64.exe', 'terminal.exe']:
                    mt5_instances.append((proc.info['exe'], proc.info['name']))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return mt5_instances
        
    def connect(self) -> bool:
        """Initialize connection to MT5 terminal."""
        if self.connected:
            return True
            
        # First shutdown any existing connections
        mt5.shutdown()
        time.sleep(1)  # Give MT5 time to clean up
        
        self.logger.info("\n=== Connecting to MT5 ===")
        
        # Find all running MT5 instances
        mt5_instances = self._find_mt5_instances()
        
        if not mt5_instances:
            self.logger.error("No running MT5 instances found")
            return False
            
        # If multiple instances found, ask user which one to connect to
        selected_path = None
        if len(mt5_instances) > 1:
            self.logger.info("\nMultiple MT5 instances found:")
            for i, (path, name) in enumerate(mt5_instances):
                self.logger.info(f"{i+1}. {name} at {path}")
            
            # Use the first instance by default
            selected_path = mt5_instances[0][0]
            self.logger.info(f"\nAutomatically selecting first instance: {selected_path}")
        else:
            selected_path = mt5_instances[0][0]
            self.logger.info(f"Found MT5 instance at: {selected_path}")
        
        # Initialize MT5 with timeout and retries
        timeout_ms = self.config.getint('MT5', 'timeout_ms', fallback=5000)
        max_init_retries = self.config.getint('MT5', 'max_retries', fallback=3)
        
        self.logger.info("Initializing MT5...")
        for init_attempt in range(max_init_retries):
            try:
                if mt5.initialize(path=selected_path, timeout=timeout_ms):
                    break
                error = mt5.last_error()
                self.logger.warning(f"Initialize attempt {init_attempt + 1} failed. Error code: {error[0]}, Message: {error[1]}")
                if init_attempt < max_init_retries - 1:
                    time.sleep(1)
                    continue
                self.logger.error("All initialize attempts failed")
                return False
            except Exception as e:
                self.logger.error(f"Unexpected error during initialization: {str(e)}")
                if init_attempt < max_init_retries - 1:
                    time.sleep(1)
                    continue
                return False
            
        # Get terminal info with retry
        self.logger.info("Getting terminal info...")
        for info_attempt in range(3):
            try:
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
                    break
                else:
                    if info_attempt < 2:
                        time.sleep(1)
                        continue
                    self.logger.error("Failed to get terminal info after 3 attempts")
                    return False
            except Exception as e:
                self.logger.error(f"Error getting terminal info: {str(e)}")
                if info_attempt < 2:
                    time.sleep(1)
                    continue
                return False
        
        # Try to get account info without login
        self.logger.info("\nAttempting to get account info...")
        account_info = mt5.account_info()
        
        if account_info is not None:
            # Successfully connected to already logged in instance
            self.connected = True
            self.logger.info(f"Successfully connected to logged in account:")
            self.logger.info(f"Account: {account_info.login}")
            self.logger.info(f"Name: {account_info.name}")
            self.logger.info(f"Server: {account_info.server}")
            self.logger.info(f"Balance: ${account_info.balance:.2f}")
            self.logger.info(f"Equity: ${account_info.equity:.2f}")
            return True
            
        # If not logged in, try to login with credentials from config
        username = self.config.getint('MT5', 'username', fallback=None)
        password = self.config.get('MT5', 'password', fallback=None)
        server = self.config.get('MT5', 'server', fallback=None)
        
        if username and password and server:
            self.logger.info("\nNo active login found, attempting login with credentials...")
            self.logger.info(f"Username: {username}")
            self.logger.info(f"Server: {server}")
            
            # Add retry logic for login
            max_retries = self.config.getint('MT5', 'max_retries', fallback=3)
            retry_delay_ms = self.config.getfloat('MT5', 'retry_delay_ms', fallback=1000)
            retry_delay = retry_delay_ms / 1000.0
            
            for attempt in range(max_retries):
                try:
                    login_result = mt5.login(
                        login=username,
                        password=password,
                        server=server.strip(),
                        timeout=timeout_ms
                    )
                    
                    if login_result:
                        break
                        
                    error = mt5.last_error()
                    self.logger.warning(f"Login attempt {attempt + 1} failed. Error code: {error[0]}, Message: {error[1]}")
                    
                    if attempt < max_retries - 1:
                        self.logger.info(f"Retrying in {retry_delay:.1f} seconds...")
                        time.sleep(retry_delay)
                except Exception as e:
                    self.logger.error(f"Unexpected error during login: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    mt5.shutdown()
                    return False
            
            if not login_result:
                error = mt5.last_error()
                self.logger.error(f"All login attempts failed. Error code: {error[0]}, Message: {error[1]}")
                mt5.shutdown()
                return False
        else:
            self.logger.error("No credentials found in config and no active login found")
            mt5.shutdown()
            return False
        
        # Final verification with account info
        self.logger.info("\nVerifying connection...")
        for acc_attempt in range(3):
            try:
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
                    if acc_attempt < 2:
                        time.sleep(1)
                        continue
                    self.logger.error("Failed to get account info after 3 attempts")
                    mt5.shutdown()
                    return False
            except Exception as e:
                self.logger.error(f"Error getting account info: {str(e)}")
                if acc_attempt < 2:
                    time.sleep(1)
                    continue
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
        
    def get_last_tick(self, symbol: str) -> Dict:
        """Get the latest tick data for a symbol."""
        if not self.connected:
            return {"error": "Not connected"}
            
        # Get last tick from MT5
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            error = mt5.last_error()
            return {"error": f"Failed to get tick: {error[1]}"}
            
        return {
            'time': datetime.fromtimestamp(tick.time).timestamp(),
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'volume': tick.volume,
            'flags': tick.flags
        } 