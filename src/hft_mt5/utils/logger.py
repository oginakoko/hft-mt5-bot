"""Logging configuration for the HFT strategy."""

import logging
import sys
from datetime import datetime
import os

def setup_logger(name: str = 'HFT_Strategy') -> logging.Logger:
    """Configure and return a logger instance."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Only add handlers if they don't exist
        logger.setLevel(logging.INFO)
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Create file handler
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f'hft_strategy_{datetime.now().strftime("%Y%m%d")}.log')
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create default logger instance
logger = setup_logger() 