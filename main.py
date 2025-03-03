import sys
import signal
import logging
from src.hft_mt5.strategy import HFTStrategy

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("hft_strategy.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger('main')
    
    # Create strategy instance
    try:
        strategy = HFTStrategy('config.ini')
    except Exception as e:
        logger.error(f"Failed to initialize strategy: {e}")
        return
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        strategy.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start strategy
    try:
        strategy.start()
        logger.info("Strategy running. Press Ctrl+C to stop.")
        
        # Keep main thread alive
        signal.pause()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        strategy.stop()
        logger.info("Strategy stopped")

if __name__ == "__main__":
    main() 