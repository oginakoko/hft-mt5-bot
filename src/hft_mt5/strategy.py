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
                window_size=self.config.getint('HFT', 'tick_features_window', fallback=20)
            )
            self.logger.info("FeatureGenerator initialized")
            
            self.signal_generator = SignalGenerator(
                threshold=self.config.getfloat('HFT', 'signal_threshold', fallback=0.7)
            )
            self.logger.info("SignalGenerator initialized")
            
            self.risk_manager = RiskManager(
                self.mt5_handler,
                max_risk_per_trade=self.config.getfloat('Risk', 'max_risk_per_trade', fallback=0.02),
                max_total_risk=self.config.getfloat('Risk', 'max_total_risk', fallback=0.06),
                max_positions=self.config.getint('Risk', 'max_positions', fallback=3),
                max_drawdown=self.config.getfloat('Risk', 'max_drawdown', fallback=0.1)
            )
            self.logger.info("RiskManager initialized")
            
            self.execution_engine = ExecutionEngine(
                self.mt5_handler,
                use_market_orders=self.config.getboolean('Trading', 'use_market_orders', fallback=True)
            )
            self.logger.info("ExecutionEngine initialized")
            
            self.symbols = self.config.get('Trading', 'symbols').split(',')
            self.logger.info(f"Trading symbols: {self.symbols}")
            
            self.tick_buffers = {symbol: TickBuffer(
                max_size=self.config.getint('HFT', 'tick_buffer_size', fallback=1000)
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
        """Process market data for a symbol."""
        last_tick_time = 0
        min_tick_interval = 0.001  # 1ms minimum between ticks
        
        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                if current_time - last_tick_time < min_tick_interval:
                    continue
                    
                # Get latest tick
                tick_info = self.mt5_handler.get_symbol_info(symbol)
                if not tick_info or "error" in tick_info:
                    continue
                    
                tick = Tick(
                    bid=tick_info['bid'],
                    ask=tick_info['ask'],
                    time=current_time,
                    volume=tick_info.get('volume', 0)
                )
                
                # Update tick buffer
                self.tick_buffers[symbol].add_tick(tick)
                
                # Generate features
                features = self.feature_generator.calculate_features(
                    self.tick_buffers[symbol]
                )
                
                # Generate signals
                signal = self.signal_generator.generate_signal(
                    symbol=symbol,
                    features=features,
                    timestamp=int(current_time * 1000)  # Millisecond timestamp
                )
                
                if signal and signal.direction != 0:
                    self._execute_signal(signal)
                    
                last_tick_time = current_time
                    
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
            finally:
                time.sleep(0.0001)  # 0.1ms delay to prevent CPU overload
                
    def _execute_signal(self, signal: Signal):
        """Execute a trading signal."""
        try:
            # Quick position check
            if not self.risk_manager.can_open_position(signal.symbol):
                return
                
            # Calculate position size based on signal strength
            position_size = self.risk_manager.calculate_position_size(
                signal.symbol,
                signal.strength
            )
            
            if position_size <= 0:
                return
                
            # Get current market state
            symbol_info = self.mt5_handler.get_symbol_info(signal.symbol)
            if not symbol_info or "error" in symbol_info:
                return
                
            # Dynamic stop loss and take profit based on volatility
            volatility = signal.features.get('volatility', 0.0001)
            stop_loss_pips = max(5, min(20, int(volatility * 10000)))
            take_profit_pips = max(7, min(30, int(volatility * 15000)))
            
            # Execute trade with tight stops
            result = self.execution_engine.execute_signal(
                signal,
                position_size,
                stop_loss_pips,
                take_profit_pips
            )
            
            # Log the trade execution
            if result and "error" not in result:
                self.logger.info(
                    f"Executed {signal.direction > 0 and 'BUY' or 'SELL'} signal on {signal.symbol} "
                    f"with size {position_size:.2f} @ {result.get('price', 0):.5f} "
                    f"(SL: {stop_loss_pips}p, TP: {take_profit_pips}p)"
                )
            
        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
            
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
            