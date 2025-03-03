# HFT MT5 Trading Bot

A high-frequency trading bot for MetaTrader 5 with a real-time web dashboard. This project implements an automated trading strategy with risk management, real-time monitoring, and a modern web interface.

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.8 or higher**
   - Download from: [Python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation
   - Verify installation: `python --version`

2. **MetaTrader 5**
   - Download from: [MetaTrader 5 Official Website](https://www.metatrader5.com/en/download)
   - Install for your broker (if you have a specific broker)
   - Enable AutoTrading: Tools -> Options -> Expert Advisors -> "Allow Automated Trading"
   - Allow WebRequests for localhost

3. **Git** (for cloning the repository)
   - Download from: [Git-scm.com](https://git-scm.com/downloads)
   - Verify installation: `git --version`

4. **Visual Studio Build Tools** (required for MetaTrader5 Python package)
   - Download from: [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Install "Desktop development with C++"
   - Required for compiling MT5 Python package

## MetaTrader 5 Configuration

After installing MetaTrader 5, you need to configure it properly:

1. **Enable AutoTrading**
   - Open MetaTrader 5
   - Click Tools -> Options -> Expert Advisors
   - Enable "Allow Automated Trading"
   - Enable "Allow WebRequests for listed URL"
   - Add `http://localhost` and `https://localhost` to the list of allowed URLs
   - Click "OK" to save changes

2. **Allow DLL Imports**
   - Go to Tools -> Options -> Expert Advisors
   - Check "Allow DLL imports"
   - Check "Allow import of external experts"
   - Click "OK" to save changes

3. **Configure Trading Account**
   - File -> Login to Trade Account
   - Enter your broker's server
   - Enter your account credentials
   - Enable "Save account information" for convenience

4. **Verify Market Data**
   - Make sure you can see real-time prices for your trading pairs
   - If prices are not updating, right-click on the symbol and select "Chart Window"
   - Ensure your internet connection is stable

5. **Test Connection**
   - In the "Market Watch" window (Ctrl+M if not visible)
   - Right-click and select "Symbols"
   - Add the currency pairs you plan to trade
   - Ensure you can see bid/ask prices updating

## Features

- Real-time trading strategy execution
- Web-based dashboard for monitoring and control
- Dynamic trading pair management
- Risk management system
- Real-time equity tracking
- Position monitoring
- Dark/Light theme support

## Requirements

- Python 3.8+
- MetaTrader 5 terminal installed
- Windows OS (MT5 requirement)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/oginakoko/hft-mt5-bot.git
cd hft-mt5-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Configure MetaTrader 5:
   - Install MetaTrader 5
   - Log in to your trading account
   - Enable AutoTrading
   - Allow algorithmic trading

5. Configure the bot:
   - Copy `config.example.ini` to `config.ini`
   - Update the configuration with your settings

## Configuration

Edit `config.ini` with your preferred settings:

```ini
[MT5]
# Your MT5 account settings
account_type = real  # or demo
login = your_login
password = your_password
server = your_server

[Trading]
symbols = EURUSD,GBPUSD  # comma-separated list of trading pairs
use_market_orders = true

[Risk]
max_risk_per_trade = 0.02  # 2% per trade
max_total_risk = 0.06     # 6% total
max_positions = 3
max_drawdown = 0.1       # 10% max drawdown

[HFT]
tick_buffer_size = 1000
tick_features_window = 20
signal_threshold = 0.7
equity_points = 1000
```

## Usage

1. Start the bot:
```bash
python run.py
```

2. Open your web browser and navigate to:
```
http://localhost:8000
```

3. Monitor your trading activity through the dashboard:
   - View account summary
   - Track equity curve
   - Manage trading pairs
   - Monitor open positions
   - View trading activity log

## Dashboard Features

- Real-time equity curve
- Account summary (Balance, Equity, Margin, Profit)
- Trading pair management
- Position monitoring
- Trading activity log
- Dark/Light theme toggle

## Safety Features

- Automatic stop-loss and take-profit
- Maximum drawdown protection
- Position size management
- Risk per trade limits
- Maximum open positions limit

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues and Solutions

1. **MetaTrader5 Package Installation Fails**
   - Ensure Visual Studio Build Tools is installed with "Desktop development with C++"
   - Try installing wheel first: `pip install wheel`
   - If using Python 3.11+, try downgrading to Python 3.10
   - Run: `pip install --upgrade setuptools`

2. **"Initialize() failed" Error**
   - Check if MT5 terminal is running
   - Verify AutoTrading is enabled
   - Ensure you're using the correct login credentials
   - Check if another instance of the bot is already running

3. **No Real-Time Data**
   - Verify internet connection
   - Check if the symbols are added in Market Watch
   - Ensure your account has access to the required symbols
   - Try restarting the MT5 terminal

4. **WebSocket Connection Failed**
   - Check if port 8000 is available
   - Try changing the port in config.ini
   - Ensure no firewall is blocking the connection
   - Verify localhost is allowed in MT5's WebRequest settings

5. **Performance Issues**
   - Close unnecessary MT5 charts
   - Reduce the number of monitored symbols
   - Increase tick_buffer_size in config
   - Check system resource usage

### Still Having Issues?

1. Check the log file: `hft_strategy.log`
2. Ensure all prerequisites are properly installed
3. Verify MT5 platform is properly configured
4. Try running with a demo account first
5. Open an issue on GitHub with:
   - Error message
   - Log file contents
   - Your configuration (without sensitive data)
   - Steps to reproduce the issue

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

Trading forex/CFDs carries significant risks. This software is for educational purposes only. Use at your own risk. Past performance is not indicative of future results. 