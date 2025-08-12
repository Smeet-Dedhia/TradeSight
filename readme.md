# TradeSight 📈

A comprehensive **multi-broker** portfolio tracking and analysis tool for Indian traders, built with Python and data science capabilities. Supports multiple Zerodha and ICICI Direct accounts with consolidated portfolio analysis.

## Features ✨

- **Multi-Broker Support**: Manage up to 4 Zerodha + 2 ICICI Direct accounts
- **Consolidated Portfolio**: Unified view across all broker accounts
- **Portfolio Tracking**: Real-time portfolio data from multiple brokers
- **Data Analysis**: Comprehensive portfolio analysis with risk metrics
- **Watchlist Generation**: Create watchlists based on various criteria
- **Visualization**: Interactive charts and portfolio distribution analysis
- **Export Capabilities**: Export data in CSV, Excel, and JSON formats
- **Alert System**: Portfolio alerts for significant movements and risks
- **Performance Metrics**: Detailed performance analysis and tracking
- **Broker Comparison**: Compare performance across different brokers

## Project Structure 📁

```
TradeSight/
├── config.py                    # Multi-broker configuration management
├── zerodha_client.py            # Zerodha API client (multi-account)
├── icici_client.py              # ICICI Direct (Breeze) API client
├── multi_broker_manager.py      # Multi-broker portfolio manager
├── portfolio_manager.py         # Single broker portfolio analysis
├── multi_broker_example.py      # Multi-broker demo script
├── example_usage.py             # Single broker demo script
├── requirements.txt             # Python dependencies
├── env_example.txt              # Environment variables template
└── README.md                    # This file
```

## Prerequisites 🔑

1. **Broker Accounts**: Active Zerodha and/or ICICI Direct trading accounts
2. **API Access**: API keys and secrets from broker developer consoles
3. **TOTP Setup**: 2FA authentication setup (recommended)
4. **Python 3.8+**: Python 3.8 or higher installed

## Installation 🚀

### 1. Clone the Repository
```bash
git clone <repository-url>
cd TradeSight
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Copy the example environment file and fill in your credentials:
```bash
cp env_example.txt .env
```

Edit `.env` file with your actual broker credentials:

#### For Zerodha Accounts (up to 4):
```env
# Zerodha Account 1
ZERODHA_1_API_KEY=your_api_key_1
ZERODHA_1_API_SECRET=your_api_secret_1
ZERODHA_1_TOTP_SECRET=your_totp_secret_1
ZERODHA_1_ACCOUNT_NAME=Zerodha Account 1

# Zerodha Account 2
ZERODHA_2_API_KEY=your_api_key_2
ZERODHA_2_API_SECRET=your_api_secret_2
ZERODHA_2_TOTP_SECRET=your_totp_secret_2
ZERODHA_2_ACCOUNT_NAME=Zerodha Account 2
```

#### For ICICI Direct Accounts (up to 2):
```env
# ICICI Direct Account 1
ICICI_1_API_KEY=your_api_key_1
ICICI_1_API_SECRET=your_api_secret_1
ICICI_1_TOTP_SECRET=your_totp_secret_1
ICICI_1_ACCOUNT_NAME=ICICI Direct Account 1
```

## Usage 💻

### Multi-Broker Portfolio Management
```python
from multi_broker_manager import MultiBrokerManager

# Initialize multi-broker manager
manager = MultiBrokerManager()
manager.initialize_brokers()

# Login to all accounts
credentials = {
    "Zerodha Account 1": {"user_id": "user1", "password": "pass1", "pin": "1234"},
    "ICICI Direct Account 1": {"user_id": "user2", "password": "pass2", "pin": "5678"}
}
manager.login_all_accounts(credentials)

# Get consolidated portfolio overview
overview = manager.get_consolidated_overview()
print(overview)
```

### Single Broker Usage (Legacy)
```python
from zerodha_client import ZerodhaClient
from portfolio_manager import PortfolioManager

# Initialize client for specific account
client = ZerodhaClient(account_config)
if client.login(user_id, password, pin):
    portfolio_mgr = PortfolioManager(client)
    overview = portfolio_mgr.get_portfolio_overview()
```

### Run the Multi-Broker Demo
```bash
python multi_broker_example.py
```

### Run the Single Broker Demo
```bash
python example_usage.py
```

## API Reference 📚

### MultiBrokerManager

Main manager for handling multiple broker accounts.

#### Methods:
- `initialize_brokers()`: Initialize all broker clients
- `login_all_accounts(credentials)`: Login to all accounts
- `fetch_all_portfolios()`: Fetch data from all accounts
- `get_consolidated_overview()`: Get unified portfolio analysis
- `generate_consolidated_watchlist(criteria, limit)`: Generate watchlists
- `plot_consolidated_portfolio()`: Create comprehensive charts
- `export_consolidated_portfolio(format, filepath)`: Export data
- `get_consolidated_alerts()`: Get alerts from all portfolios

### ZerodhaClient

Client for interacting with Zerodha API (multi-account support).

#### Methods:
- `login(user_id, password, pin)`: Authenticate with Zerodha
- `get_portfolio()`: Fetch raw portfolio data
- `get_portfolio_holdings()`: Get simplified holdings data
- `get_portfolio_summary()`: Get portfolio summary statistics
- `get_portfolio_as_dataframe()`: Get holdings as pandas DataFrame

### ICICIClient

Client for interacting with ICICI Direct (Breeze) API.

#### Methods:
- `login(user_id, password, pin)`: Authenticate with ICICI Direct
- `get_portfolio()`: Fetch portfolio data
- `get_portfolio_holdings()`: Get simplified holdings data
- `get_portfolio_summary()`: Get portfolio summary statistics
- `get_portfolio_as_dataframe()`: Get holdings as pandas DataFrame

## Multi-Broker Features 🏛️

### Account Management
- **Up to 4 Zerodha accounts** with unique naming
- **Up to 2 ICICI Direct accounts** with unique naming
- **Flexible configuration** - only configure accounts you need
- **Account-specific credentials** and session management

### Consolidated Analysis
- **Unified portfolio view** across all brokers
- **Broker-wise breakdown** and comparison
- **Account performance tracking** and ranking
- **Cross-account risk assessment**

### Advanced Analytics
- **Consolidated risk metrics** (Herfindahl index, concentration risk)
- **Performance comparison** across accounts and brokers
- **Unified watchlist generation** from all portfolios
- **Multi-account alerts** and notifications

## Security 🔒

- **Environment Variables**: Never commit `.env` file to version control
- **API Credentials**: Keep your API keys and secrets secure
- **Session Management**: Automatic session timeout and cleanup for each account
- **Rate Limiting**: Built-in rate limiting for API calls
- **Secure Authentication**: 2FA support for enhanced security

## Data Science Capabilities 📊

- **Multi-Account Analysis**: Risk metrics, concentration analysis, performance tracking
- **Statistical Analysis**: Returns distribution, correlation analysis across accounts
- **Visualization**: Matplotlib, Seaborn, and Plotly charts with broker breakdown
- **Data Export**: Multiple format support for further analysis
- **Risk Assessment**: Consolidated Herfindahl index, portfolio volatility

## Troubleshooting 🛠️

### Common Issues:

1. **Authentication Failed**
   - Verify API key and secret for each account
   - Check TOTP secret configuration
   - Ensure accounts are active

2. **Portfolio Data Not Loading**
   - Check internet connection
   - Verify session validity for each account
   - Check API rate limits

3. **Configuration Errors**
   - Ensure environment variables are properly set
   - Check account naming conventions
   - Verify broker-specific requirements

### Getting Help:
- Check broker API documentation
- Verify your API permissions
- Check network connectivity
- Review environment variable configuration

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer ⚠️

This tool is for educational and personal use only. Trading involves risk, and past performance doesn't guarantee future results. Always do your own research and consider consulting with financial advisors.

## Support 💬

For issues and questions:
- Check the troubleshooting section
- Review broker API documentation
- Verify your API permissions
- Open an issue in the repository

---

**Happy Multi-Broker Trading! 📈💰🏛️**