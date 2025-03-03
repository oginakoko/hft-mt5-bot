"""Configuration management for the HFT strategy."""

import configparser
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

class Config:
    """Configuration handler for the HFT strategy framework."""
    
    def __init__(self, config_path: str = "config.ini"):
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
        self.logger = logging.getLogger('HFT_Strategy.Config')
        
        # Ensure the config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.config_path.exists():
            try:
                self.config.read(config_path)
                self._ensure_required_sections()
            except Exception as e:
                self.logger.error(f"Error reading config file: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _ensure_required_sections(self):
        """Ensure all required sections exist with default values."""
        default_config = configparser.ConfigParser(interpolation=None)
        self._create_default_config(default_config)
        
        # Add missing sections and keys
        for section in default_config.sections():
            if not self.config.has_section(section):
                self.config[section] = default_config[section]
            else:
                for key, value in default_config[section].items():
                    if key not in self.config[section]:
                        self.config[section][key] = value
        
        self.save()
    
    def _create_default_config(self, config=None):
        """Create default configuration settings."""
        if config is None:
            config = self.config
            
        # MT5 Connection Settings
        config['MT5'] = {
            'username': '',
            'password': '',
            'server': '',
            'timeout_ms': '5000',
            'retry_delay_ms': '1000',
            'max_retries': '3'
        }
        
        # Trading Parameters
        config['Trading'] = {
            'symbols': 'EURUSD,USDJPY,GBPUSD',
            'max_positions': '5',
            'max_drawdown': '0.2',
            'risk_per_trade': '0.01',
            'stop_loss_pips': '10',
            'take_profit_pips': '20',
            'min_trade_interval': '0.5',
            'use_market_orders': 'True',
            'allow_hedging': 'False',
            'max_spread_pips': '3',
            'slippage_pips': '1'
        }
        
        # HFT Specific Settings
        config['HFT'] = {
            'tick_buffer_size': '1000',
            'signal_threshold': '0.7',
            'tick_features_window': '20',
            'polling_interval_ms': '50',
            'trade_cooldown_ms': '500',
            'feature_calculation_window': '100',
            'max_tick_age_ms': '1000',
            'price_rounding_digits': '5'
        }
        
        # Risk Management
        config['Risk'] = {
            'max_position_size': '1.0',
            'daily_loss_limit': '0.05',
            'max_trades_per_hour': '10',
            'correlation_threshold': '0.7',
            'volatility_scaling': 'True',
            'max_leverage': '30'
        }
        
        # Performance Monitoring
        config['Monitor'] = {
            'metrics_update_ms': '1000',
            'log_trades': 'True',
            'save_ticks': 'True',
            'performance_window': '3600',
            'alert_threshold': '0.1'
        }
        
        if config is self.config:
            self.save()
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """Get string value from config."""
        try:
            value = self.config.get(section, key, fallback=fallback)
            if key == 'path':
                # Handle path values
                return str(Path(os.path.expandvars(value)))
            return value
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            self.logger.warning(f"Missing config value: [{section}] {key}")
            return ""
    
    def getint(self, section: str, key: str, fallback: Optional[int] = None) -> int:
        """Get integer value from config."""
        try:
            return self.config.getint(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if fallback is not None:
                return fallback
            self.logger.warning(f"Missing or invalid integer config value: [{section}] {key}")
            return 0
    
    def getfloat(self, section: str, key: str, fallback: Optional[float] = None) -> float:
        """Get float value from config."""
        try:
            return self.config.getfloat(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if fallback is not None:
                return fallback
            self.logger.warning(f"Missing or invalid float config value: [{section}] {key}")
            return 0.0
    
    def getboolean(self, section: str, key: str, fallback: Optional[bool] = None) -> bool:
        """Get boolean value from config."""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if fallback is not None:
                return fallback
            self.logger.warning(f"Missing or invalid boolean config value: [{section}] {key}")
            return False
    
    def get_symbols(self) -> List[str]:
        """Get list of trading symbols."""
        symbols_str = self.get('Trading', 'symbols')
        return [s.strip() for s in symbols_str.split(',')]
    
    def update_trading_params(self, risk_per_trade: Optional[float] = None,
                            max_drawdown: Optional[float] = None,
                            symbols: Optional[List[str]] = None,
                            stop_loss_pips: Optional[int] = None,
                            take_profit_pips: Optional[int] = None):
        """Update trading parameters."""
        if risk_per_trade is not None:
            self.config['Trading']['risk_per_trade'] = str(risk_per_trade)
        if max_drawdown is not None:
            self.config['Trading']['max_drawdown'] = str(max_drawdown)
        if symbols is not None:
            self.config['Trading']['symbols'] = ','.join(symbols)
        if stop_loss_pips is not None:
            self.config['Trading']['stop_loss_pips'] = str(stop_loss_pips)
        if take_profit_pips is not None:
            self.config['Trading']['take_profit_pips'] = str(take_profit_pips)
        self.save()
    
    def update_hft_params(self, signal_threshold: Optional[float] = None,
                         tick_buffer_size: Optional[int] = None,
                         polling_interval: Optional[int] = None):
        """Update HFT-specific parameters."""
        if signal_threshold is not None:
            self.config['HFT']['signal_threshold'] = str(signal_threshold)
        if tick_buffer_size is not None:
            self.config['HFT']['tick_buffer_size'] = str(tick_buffer_size)
        if polling_interval is not None:
            self.config['HFT']['polling_interval_ms'] = str(polling_interval)
        self.save()
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate configuration settings."""
        errors = []
        
        # Check required MT5 settings
        if not self.get('MT5', 'username'):
            errors.append("MT5 username not configured")
        if not self.get('MT5', 'password'):
            errors.append("MT5 password not configured")
            
        # Validate trading parameters
        try:
            risk = self.getfloat('Trading', 'risk_per_trade')
            if not 0 < risk <= 0.1:
                errors.append("risk_per_trade must be between 0 and 0.1")
                
            max_dd = self.getfloat('Trading', 'max_drawdown')
            if not 0 < max_dd <= 0.5:
                errors.append("max_drawdown must be between 0 and 0.5")
                
            if not self.get_symbols():
                errors.append("No trading symbols configured")
        except ValueError as e:
            errors.append(f"Invalid trading parameter: {e}")
        
        return len(errors) == 0, errors
    
    def save(self):
        """Save current configuration to file."""
        with open(self.config_path, 'w') as f:
            self.config.write(f)
        self.logger.info(f"Configuration saved to {self.config_path}")
