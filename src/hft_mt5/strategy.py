"""Main HFT strategy implementation."""

import time
import threading
from typing import Dict, List, Optional
from .core.feature_generator import FeatureGenerator
from .core.signal_generator import SignalGenerator
from .core.risk_manager import RiskManager
from .core.execution_engine import ExecutionEngine
from .core.data_types import TickBuffer, Tick, EquityTracker, EquityPoint, Signal
from .core.config import Config
from .core.mt5_handler import MT5Handler
import logging
from threading import Thread, Event

class HFTStrategy:
    """High-Frequency Trading Strategy implementation."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, config_path: str = 'config.ini'):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(HFTStrategy, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, config_path: str = 'config.ini'):
        if getattr(self, '_initialized', False):
            return
            
        self.logger = logging.getLogger('HFT_Strategy')
        self.logger.info("Initializing HFT Strategy...")
        
        try:
            self.config = Config(config_path)
            self.logger.info("Config loaded successfully")
            
            self.mt5_handler = MT5Handler(self.config)
            self.logger.info("MT5Handler initialized")
            
            # Initialize components with MT5Handler
            self.feature_generator = FeatureGenerator(
                window_size=2  # Ultra-short window for instant reactions
            )
            self.logger.info("FeatureGenerator initialized")
            
            self.signal_generator = SignalGenerator(
                threshold=0.03  # Extremely aggressive threshold
            )
            self.logger.info("SignalGenerator initialized")
            
            self.risk_manager = RiskManager(
                self.mt5_handler,
                max_risk_per_trade=0.005,  # 0.5% risk per trade - very aggressive
                max_total_risk=0.05,  # 5% total risk - tighter overall risk
                max_positions=3,  # Very few concurrent positions
                max_drawdown=0.04  # 4% max drawdown - strict control
            )
            self.logger.info("RiskManager initialized")
            
            self.execution_engine = ExecutionEngine(
                self.mt5_handler
            )
            self.logger.info("ExecutionEngine initialized")
            
            # Get all available symbols and filter for most liquid ones
            self.symbols = self._get_liquid_symbols()
            self.logger.info(f"Trading symbols: {self.symbols}")
            
            self.tick_buffers = {symbol: TickBuffer(
                max_size=15  # Tiny buffer for instant processing
            ) for symbol in self.symbols}
            self.logger.info("Tick buffers initialized")
            
            # Initialize equity tracker
            self.equity_tracker = EquityTracker(
                max_points=self.config.getint('HFT', 'equity_points', fallback=1000)
            )
            self.logger.info("EquityTracker initialized")
            
            # Control flags
            self.stop_event = Event()
            self.is_running = False
            self._initialized = True
            
            # Threads
            self.threads = []
            self.equity_thread = None
            
            self.logger.info("Strategy initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during strategy initialization: {e}")
            self._initialized = False
            raise
            
    def _get_liquid_symbols(self) -> List[str]:
        """Get list of liquid symbols to trade."""
        try:
            all_symbols = self.mt5_handler.get_symbols()
            if not all_symbols or "error" in all_symbols:
                return ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD']
                
            liquid_symbols = []
            for symbol in all_symbols:
                info = self.mt5_handler.get_symbol_info(symbol)
                if not info or "error" in info:
                    continue
                    
                # More aggressive filtering for ultra-liquid pairs
                if (info.get('spread', 1000) < 10 and  # Tighter spread requirement
                    info.get('trade_mode', 0) == 4 and
                    len(symbol) == 6 and
                    any(curr in symbol for curr in ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'NZD', 'CAD'])):
                    liquid_symbols.append(symbol)
                    
            if not liquid_symbols:
                return ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD']
                
            return liquid_symbols[:30]  # Trade more pairs simultaneously
            
        except Exception as e:
            self.logger.error(f"Error getting liquid symbols: {e}")
            return ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD']
            
    def start(self) -> bool:
        """Start the trading strategy."""
        with self._lock:
            if self.is_running:
                self.logger.warning("Strategy is already running")
                return False
                
            if not self._initialized:
                self.logger.error("Strategy not properly initialized")
                return False
                
            self.logger.info("Starting strategy...")
            try:
                # Connect to MT5
                self.logger.info("Connecting to MT5...")
                if not self.mt5_handler.connect():
                    self.logger.error("Failed to connect to MT5")
                    return False
                self.logger.info("Successfully connected to MT5")
                    
                # Initialize risk manager
                self.logger.info("Initializing risk manager...")
                if not self.risk_manager.initialize():
                    self.logger.error("Failed to initialize risk manager")
                    return False
                self.logger.info("Risk manager initialized successfully")
                    
                # Start processing threads
                self.is_running = True
                self.stop_event.clear()
                
                # Start symbol processing threads
                self.logger.info("Starting symbol processing threads...")
                for symbol in self.symbols:
                    thread = Thread(target=self._process_symbol, args=(symbol,), daemon=True)
                    thread.start()
                    self.threads.append(thread)
                    self.logger.info(f"Started processing thread for {symbol}")
                    
                # Start equity tracking
                self.logger.info("Starting equity tracking thread...")
                self.equity_thread = Thread(target=self._track_equity, daemon=True)
                self.equity_thread.start()
                self.threads.append(self.equity_thread)
                self.logger.info("Equity tracking thread started")
                    
                self.logger.info("Strategy started successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error starting strategy: {e}")
                self.stop()
                return False
                
    def stop(self) -> bool:
        """Stop the trading strategy."""
        with self._lock:
            if not self.is_running:
                self.logger.info("Strategy is already stopped")
                return True
                
            self.logger.info("Stopping strategy...")
            
            try:
                # Stop all threads
                self.stop_event.set()
                self.is_running = False
                
                # Wait for threads to finish
                for thread in self.threads:
                    if thread.is_alive():
                        thread.join(timeout=5.0)
                self.threads.clear()
                
                # Close all positions
                self.logger.info("Closing all positions...")
                if not self.execution_engine.close_all_positions():
                    self.logger.warning("Failed to close all positions")
                    
                # Disconnect from MT5
                self.logger.info("Disconnecting from MT5...")
                self.mt5_handler.disconnect()
                
                self.logger.info("Strategy stopped successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping strategy: {e}")
                return False
        
    def _track_equity(self):
        """Track account equity over time."""
        while not self.stop_event.is_set():
            try:
                account_info = self.mt5_handler.get_account_info()
                if account_info:
                    point = EquityPoint(
                        timestamp=time.time(),
                        balance=account_info['balance'],
                        equity=account_info['equity'],
                        margin=account_info['margin'],
                        profit=account_info['profit']
                    )
                    self.equity_tracker.add_point(point)
            except Exception as e:
                self.logger.error(f"Error tracking equity: {e}")
            finally:
                time.sleep(1)  # Update every second
                
    def _process_symbol(self, symbol: str):
        """Process updates for a single symbol."""
        try:
            # Get latest tick
            mt5_tick = self.mt5_handler.get_last_tick(symbol)
            if not mt5_tick or "error" in mt5_tick:
                return
                
            # Convert MT5 tick dict to Tick object
            tick = Tick(
                bid=mt5_tick['bid'],
                ask=mt5_tick['ask'],
                time=mt5_tick.get('time_msc', time.time() * 1000) / 1000.0,
                volume=mt5_tick.get('volume', 0.0)
            )
                
            # Add tick to buffer
            self.tick_buffers[symbol].add_tick(tick)
            
            # Check virtual SL/TP for existing positions
            self.execution_engine.check_positions()
            
            # Generate features from recent ticks
            recent_ticks = self.tick_buffers[symbol].get_recent(25)  # Minimal ticks required
            if len(recent_ticks) < 10:  # Ultra-fast entry with just 10 ticks
                return
                
            features = self.feature_generator.generate_features(recent_ticks)
            
            # Generate trading signal
            signal = self.signal_generator.generate_signal(features)
            if not signal or abs(signal.strength) < 0.08:  # Very low signal requirement
                return
                
            # Calculate position size
            risk_amount = self.risk_manager.get_position_size(symbol, signal.direction)
            if not risk_amount:
                return
                
            # Calculate dynamic SL/TP based on signal strength
            sl_points = int(20 + signal.strength * 30)  # Tighter range: 20-50 points
            tp_points = int(30 + signal.strength * 45)  # Tighter range: 30-75 points
            
            # Execute the trade
            self.execution_engine.execute_signal(
                symbol=symbol,
                direction=signal.direction,
                volume=risk_amount,
                sl_points=sl_points,
                tp_points=tp_points
            )
            
        except Exception as e:
            self.logger.error(f"Error processing symbol {symbol}: {str(e)}")
                
    def add_symbol(self, symbol: str) -> bool:
        """Add a new trading symbol."""
        with self._lock:
            try:
                # Verify symbol exists in MT5
                symbol_info = self.mt5_handler.get_symbol_info(symbol)
                if not symbol_info or "error" in symbol_info:
                    self.logger.error(f"Symbol {symbol} not found in MT5")
                    return False
                
                # Add to symbols list if not already present
                if symbol not in self.symbols:
                    self.symbols.append(symbol)
                    self.tick_buffers[symbol] = TickBuffer(
                        max_size=self.config.getint('HFT', 'tick_buffer_size', fallback=1000)
                    )
                    
                    # Start symbol processing thread if strategy is running
                    if self.is_running:
                        thread = Thread(target=self._process_symbol, args=(symbol,), daemon=True)
                        thread.start()
                        self.threads.append(thread)
                        self.logger.info(f"Started processing thread for {symbol}")
                    
                    self.logger.info(f"Added symbol {symbol}")
                    return True
                    
                return False
                
            except Exception as e:
                self.logger.error(f"Error adding symbol {symbol}: {e}")
                return False
    
    def remove_symbol(self, symbol: str) -> bool:
        """Remove a trading symbol."""
        with self._lock:
            try:
                if symbol in self.symbols:
                    # Close any open positions for this symbol
                    positions = self.mt5_handler.get_positions()
                    if positions and "error" not in positions:
                        for position in positions:
                            if position['symbol'] == symbol:
                                self.mt5_handler.close_position(position['ticket'])
                    
                    # Remove from symbols list and cleanup
                    self.symbols.remove(symbol)
                    if symbol in self.tick_buffers:
                        del self.tick_buffers[symbol]
                    
                    self.logger.info(f"Removed symbol {symbol}")
                    return True
                
                return False
                
            except Exception as e:
                self.logger.error(f"Error removing symbol {symbol}: {e}")
                return False
            