"""Main entry point for the HFT strategy application."""

import asyncio
import uvicorn
import multiprocessing
import time
import logging
import socket
import sys
import signal
import os
from src.hft_mt5.strategy import HFTStrategy
from src.hft_mt5.web.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('hft_strategy.log')
    ]
)

# Set logging levels for specific loggers
logging.getLogger('uvicorn').setLevel(logging.INFO)
logging.getLogger('fastapi').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

class GracefulKiller:
    """Handle graceful shutdown."""
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
    
    def exit_gracefully(self, *args):
        self.kill_now = True

class SharedState:
    """Shared state between processes."""
    def __init__(self):
        self.is_running = multiprocessing.Value('b', False)
        self.is_connected = multiprocessing.Value('b', False)
        self.account_info = multiprocessing.Array('d', [0.0] * 4)  # balance, equity, margin, profit
        self.positions_lock = multiprocessing.Lock()
        self.positions = multiprocessing.Array('c', 1024)  # JSON string of positions

def find_available_port(start_port=8000, max_port=8020):
    """Find an available port in the given range."""
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except socket.error:
                continue
    raise RuntimeError(f"No available ports in range {start_port}-{max_port}")

def run_strategy(config_path, state, stop_event):
    """Run the HFT strategy."""
    logger.info("Starting strategy process...")
    strategy = None
    killer = GracefulKiller()
    
    try:
        # Initialize strategy
        logger.info("Initializing strategy...")
        strategy = HFTStrategy(config_path)
        
        # Update shared state
        def update_state():
            while not (stop_event.is_set() or killer.kill_now):
                try:
                    if strategy and strategy.is_running and strategy.mt5_handler.connected:
                        # Update connection status
                        state.is_running.value = True
                        state.is_connected.value = True
                        
                        # Update account info
                        account_info = strategy.mt5_handler.get_account_info()
                        if account_info and "error" not in account_info:
                            state.account_info[0] = account_info['balance']
                            state.account_info[1] = account_info['equity']
                            state.account_info[2] = account_info['margin']
                            state.account_info[3] = account_info['profit']
                        
                        # Update positions
                        positions = strategy.mt5_handler.get_positions()
                        if positions and "error" not in positions:
                            with state.positions_lock:
                                state.positions.value = str(positions).encode()
                    else:
                        state.is_running.value = False
                        state.is_connected.value = False
                except Exception as e:
                    logger.error(f"Error in update_state: {e}")
                finally:
                    time.sleep(1)
        
        # Start state update thread
        logger.info("Starting state update thread...")
        import threading
        update_thread = threading.Thread(target=update_state, daemon=True)
        update_thread.start()
        
        # Start strategy
        logger.info("Starting strategy...")
        if not strategy.start():
            raise RuntimeError("Failed to start strategy")
        
        logger.info("Strategy started successfully")
        
        # Keep running until stop event is set
        while not (stop_event.is_set() or killer.kill_now):
            time.sleep(1)
            if not strategy.is_running:
                logger.warning("Strategy stopped running")
                break
            
    except Exception as e:
        logger.error(f"Strategy error: {e}")
        if strategy:
            logger.info("Attempting to stop strategy...")
            strategy.stop()
    finally:
        if strategy:
            logger.info("Cleaning up strategy...")
            strategy.stop()
        state.is_running.value = False
        state.is_connected.value = False
        logger.info("Strategy process ended")

def run_web(config_path, state, stop_event):
    """Run the web interface."""
    logger.info("Starting web interface...")
    killer = GracefulKiller()
    
    try:
        port = find_available_port()
        logger.info(f"Found available port: {port}")
        
        strategy = HFTStrategy(config_path)
        logger.info("Created strategy instance for web interface")
        
        app = create_app(strategy, state)
        logger.info(f"Starting web server on port {port}")
        
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info")
        server = uvicorn.Server(config)
        
        def check_stop():
            while not (stop_event.is_set() or killer.kill_now):
                time.sleep(1)
            server.should_exit = True
        
        # Start stop checker thread
        import threading
        stop_thread = threading.Thread(target=check_stop, daemon=True)
        stop_thread.start()
        
        server.run()
    except Exception as e:
        logger.error(f"Web interface error: {e}")
        raise

if __name__ == "__main__":
    config_path = 'config.ini'
    shared_state = SharedState()
    stop_event = multiprocessing.Event()
    killer = GracefulKiller()
    
    logger.info("Starting HFT application...")
    
    # Start strategy in a separate process
    logger.info("Creating strategy process...")
    strategy_process = multiprocessing.Process(
        target=run_strategy,
        args=(config_path, shared_state, stop_event)
    )
    
    # Start web interface in a separate process
    logger.info("Creating web interface process...")
    web_process = multiprocessing.Process(
        target=run_web,
        args=(config_path, shared_state, stop_event)
    )
    
    try:
        logger.info("Starting strategy process...")
        strategy_process.start()
        
        logger.info("Starting web interface process...")
        web_process.start()
        
        # Wait for processes to finish or kill signal
        while not killer.kill_now:
            if not strategy_process.is_alive() or not web_process.is_alive():
                logger.warning("A process has died, initiating shutdown...")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Application interrupted")
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        logger.info("Cleaning up...")
        stop_event.set()
        
        if strategy_process.is_alive():
            logger.info("Terminating strategy process...")
            strategy_process.terminate()
            strategy_process.join(timeout=5.0)
            
        if web_process.is_alive():
            logger.info("Terminating web interface process...")
            web_process.terminate()
            web_process.join(timeout=5.0)
            
        logger.info("Application shutdown complete") 