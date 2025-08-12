# TradeSight 📈

A comprehensive portfolio tracking and analysis tool for Zerodha users, built with Python and data science capabilities.

## Features ✨

- **Portfolio Tracking**: Fetch real-time portfolio data from Zerodha
- **Data Analysis**: Comprehensive portfolio analysis with risk metrics
- **Watchlist Generation**: Create watchlists based on various criteria
- **Visualization**: Interactive charts and portfolio distribution analysis
- **Export Capabilities**: Export data in CSV, Excel, and JSON formats
- **Alert System**: Portfolio alerts for significant movements and risks
- **Performance Metrics**: Detailed performance analysis and tracking

## Project Structure 📁

```
TradeSight/
├── config.py              # Configuration and environment variables
├── zerodha_client.py      # Zerodha API client implementation
├── portfolio_manager.py   # Portfolio analysis and management
├── example_usage.py       # Example usage and demo script
├── requirements.txt       # Python dependencies
├── env_example.txt        # Environment variables template
└── README.md             # This file
```

## Prerequisites 🔑

1. **Zerodha Account**: Active Zerodha trading account
2. **API Access**: Zerodha API key and secret from [Zerodha Developer Console](https://developers.kite.trade/)
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

Edit `.env` file with your actual Zerodha credentials:
```env
ZERODHA_API_KEY=your_actual_api_key
ZERODHA_API_SECRET=your_actual_api_secret
ZERODHA_TOTP_SECRET=your_actual_totp_secret
```

## Usage 💻

### Basic Portfolio Fetching
```python
from zerodha_client import ZerodhaClient
from portfolio_manager import PortfolioManager

# Initialize client
client = ZerodhaClient()

# Login (you'll be prompted for credentials)
if client.login(user_id, password, pin):
    # Initialize portfolio manager
    portfolio_mgr = PortfolioManager(client)
    
    # Get portfolio overview
    overview = portfolio_mgr.get_portfolio_overview()
    print(overview)
```

### Run the Example Script
```bash
python example_usage.py
```

## API Reference 📚

### ZerodhaClient

Main client for interacting with Zerodha API.

#### Methods:
- `login(user_id, password, pin)`: Authenticate with Zerodha
- `get_portfolio()`: Fetch raw portfolio data
- `get_portfolio_holdings()`: Get simplified holdings data
- `get_portfolio_summary()`: Get portfolio summary statistics
- `get_portfolio_as_dataframe()`: Get holdings as pandas DataFrame
- `logout()`: Clear session and logout

### PortfolioManager

High-level portfolio analysis and management.

#### Methods:
- `get_portfolio_overview()`: Comprehensive portfolio analysis
- `generate_watchlist(criteria, limit)`: Generate watchlists
- `plot_portfolio_distribution()`: Create portfolio charts
- `export_portfolio(format, filepath)`: Export data to files
- `get_portfolio_alerts()`: Get portfolio alerts and notifications

#### Watchlist Criteria:
- `"top_gainers"`: Stocks with highest returns
- `"top_losers"`: Stocks with lowest returns
- `"highest_value"`: Stocks with highest market value
- `"highest_volume"`: Stocks with highest quantity

## Security 🔒

- **Environment Variables**: Never commit `.env` file to version control
- **API Credentials**: Keep your API keys and secrets secure
- **Session Management**: Automatic session timeout and cleanup
- **Rate Limiting**: Built-in rate limiting for API calls

## Data Science Capabilities 📊

- **Portfolio Analysis**: Risk metrics, concentration analysis, performance tracking
- **Statistical Analysis**: Returns distribution, correlation analysis
- **Visualization**: Matplotlib, Seaborn, and Plotly charts
- **Data Export**: Multiple format support for further analysis
- **Risk Assessment**: Herfindahl index, portfolio volatility

## Troubleshooting 🛠️

### Common Issues:

1. **Authentication Failed**
   - Verify API key and secret
   - Check TOTP secret configuration
   - Ensure account is active

2. **Portfolio Data Not Loading**
   - Check internet connection
   - Verify session is valid
   - Check API rate limits

3. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python version compatibility
   - Verify file paths

### Getting Help:
- Check Zerodha API documentation
- Verify your API permissions
- Check network connectivity

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
- Review Zerodha API documentation
- Open an issue in the repository

---

**Happy Trading! 📈💰**