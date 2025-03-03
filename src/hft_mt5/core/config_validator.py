"""Configuration validation for the HFT strategy framework."""

from typing import Dict, List, Tuple
import MetaTrader5 as mt5
from ..utils.logger import logger

class ConfigValidator:
    """Validates configuration settings for the HFT strategy."""
    
    @staticmethod
    def validate_config(config) -> Tuple[bool, List[str]]:
        """Validate configuration settings.
        
        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
        """
        errors = []
        
        # Check MT5 settings
        if not config.get('MT5', 'username'):
            errors.append("MT5 username not configured")
        if not config.get('MT5', 'password'):
            errors.append("MT5 password not configured")
        if not config.get('MT5', 'server'):
            errors.append("MT5 server not configured")
            
        # Validate trading parameters
        try:
            max_dd = config.getfloat('Trading', 'max_drawdown')
            if not 0 < max_dd < 1:
                errors.append("max_drawdown must be between 0 and 1")
                
            risk_per_trade = config.getfloat('Trading', 'risk_per_trade')
            if not 0 < risk_per_trade < 0.1:
                errors.append("risk_per_trade must be between 0 and 0.1")
                
            max_positions = config.getint('Trading', 'max_positions')
            if not 0 < max_positions < 100:
                errors.append("max_positions must be between 1 and 100")
        except ValueError as e:
            errors.append(f"Invalid trading parameter: {e}")
            
        # Validate symbols
        symbols = config.get('Trading', 'symbols', '').split(',')
        if not symbols:
            errors.append("No trading symbols configured")
        else:
            for symbol in symbols:
                if not ConfigValidator.check_symbol_available(symbol.strip()):
                    errors.append(f"Symbol {symbol} not available in MT5")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def check_symbol_available(symbol: str) -> bool:
        """Check if a symbol is available in MT5."""
        if not mt5.initialize():
            return False
        symbol_info = mt5.symbol_info(symbol)
        return symbol_info is not None
