# HFT MT5 Trading Bot

A high-frequency trading bot for MetaTrader 5 with a real-time web dashboard. This project implements an automated trading strategy with risk management, real-time monitoring, and a modern web interface.

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
git clone https://github.com/yourusername/hft-mt5-bot.git
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

Trading forex/CFDs carries significant risks. This software is for educational purposes only. Use at your own risk. Past performance is not indicative of future results. 