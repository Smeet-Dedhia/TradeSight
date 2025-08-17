#!/usr/bin/env python3
"""
Multi-Broker Holdings Fetcher

This script fetches current holdings from multiple broker accounts (Zerodha and ICICI Direct)
and exports them to CSV files in the data folder. It handles authentication for each broker
and processes data consistently across different platforms.
"""

import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from kiteconnect import KiteConnect
from breeze_connect import BreezeConnect
import logging
import urllib.parse
from token_manager import TokenManager

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrokerConfig:
    """Configuration class for broker accounts"""
    
    def __init__(self, name: str, api_key: str, api_secret: str, broker_type: str):
        self.name = name
        self.api_key = api_key
        self.api_secret = api_secret
        self.broker_type = broker_type

class ZerodhaClient:
    """Client for Zerodha API operations"""
    
    def __init__(self, config: BrokerConfig, token_manager: TokenManager):
        self.config = config
        self.kite = KiteConnect(api_key=config.api_key)
        self.token_manager = token_manager
        self.authenticated = False
    
    def authenticate(self):
        """Authenticate with Zerodha"""
        logger.info(f"Authenticating with Zerodha account: {self.config.name}")
        
        # Check if we have a stored access token from token manager
        access_token = self.token_manager.get_token("zerodha", self.config.name)
        
        if access_token:
            try:
                self.kite.set_access_token(access_token)
                # Test if token is still valid
                profile = self.kite.profile()
                logger.info(f"Using stored access token for user: {profile.get('user_name', 'N/A')}")
                self.authenticated = True
                return True
            except Exception as e:
                logger.warning(f"Stored access token expired: {str(e)}")
                # Remove expired token
                self.token_manager.remove_token("zerodha", self.config.name)
        
        # If no valid token, perform full authentication
        logger.info("Starting authentication process...")
        
        # Get login URL
        login_url = self.kite.login_url()
        print(f"\n🌐 Visit this login URL in your browser for {self.config.name}:")
        print(f"   {login_url}")
        print("\n   Complete the login process in your browser.")
        print("   After successful login, you'll be redirected to a URL containing 'request_token'")
        
        # Get request token from user
        request_token = input(f"\n📝 Enter the request_token for {self.config.name}: ").strip()
        
        if not request_token:
            raise ValueError("No request token provided")
        
        # Generate session using request token
        logger.info("Generating session...")
        data = self.kite.generate_session(request_token, api_secret=self.config.api_secret)
        self.kite.set_access_token(data["access_token"])
        
        logger.info("Authentication successful!")
        
        # Store the access token in token manager
        self.token_manager.store_token("zerodha", self.config.name, data["access_token"], "access_token")
        print(f"\n💾 Access token automatically stored for future use.")
        
        self.authenticated = True
        return True
    
    def get_holdings(self):
        """Fetch holdings from Zerodha"""
        if not self.authenticated:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        logger.info(f"Fetching holdings from Zerodha account: {self.config.name}")
        
        try:
            holdings = self.kite.holdings()
            
            if not holdings:
                logger.warning(f"No holdings found in {self.config.name}")
                return []
            
            logger.info(f"Found {len(holdings)} holdings in {self.config.name}")
            return holdings
            
        except Exception as e:
            logger.error(f"Error fetching holdings from {self.config.name}: {str(e)}")
            raise

class ICICIClient:
    """Client for ICICI Direct (Breeze) API operations"""
    
    def __init__(self, config: BrokerConfig, token_manager: TokenManager):
        self.config = config
        self.breeze = BreezeConnect(api_key=config.api_key)
        self.token_manager = token_manager
        self.authenticated = False
    
    def authenticate(self):
        """Authenticate with ICICI Direct"""
        logger.info(f"Authenticating with ICICI Direct account: {self.config.name}")
        
        # Check if we have a stored session token from token manager
        session_token = self.token_manager.get_token("icici", self.config.name)
        
        if session_token:
            try:
                # Try to use stored session token
                self.breeze.generate_session(
                    api_secret=self.config.api_secret,
                    session_token=session_token
                )
                # Test if session is still valid
                holdings = self.breeze.get_demat_holdings()
                logger.info(f"Using stored session token for {self.config.name}")
                self.authenticated = True
                return True
            except Exception as e:
                logger.warning(f"Stored session token expired: {str(e)}")
                # Remove expired token
                self.token_manager.remove_token("icici", self.config.name)
        
        # If no valid token, perform full authentication
        logger.info("Starting authentication process...")
        
        # Generate login URL
        login_url = f"https://api.icicidirect.com/apiuser/login?api_key={urllib.parse.quote_plus(self.config.api_key)}"
        print(f"\n🌐 Visit this login URL in your browser for {self.config.name}:")
        print(f"   {login_url}")
        print("\n   Complete the login process in your browser.")
        print("   After successful login, you'll get a session token.")
        
        # Get session token from user
        session_token = input(f"\n📝 Enter the session token for {self.config.name}: ").strip()
        
        if not session_token:
            raise ValueError("No session token provided")
        
        # Generate session using session token
        logger.info("Generating session...")
        self.breeze.generate_session(
            api_secret=self.config.api_secret,
            session_token=session_token
        )
        
        logger.info("Authentication successful!")
        
        # Store the session token in token manager
        self.token_manager.store_token("icici", self.config.name, session_token, "session_token")
        print(f"\n💾 Session token automatically stored for future use.")
        
        self.authenticated = True
        return True
    
    def get_holdings(self):
        """Fetch holdings from ICICI Direct"""
        if not self.authenticated:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        logger.info(f"Fetching holdings from ICICI Direct account: {self.config.name}")
        
        try:
            holdings = self.breeze.get_demat_holdings()
            
            if not holdings:
                logger.warning(f"No holdings found in {self.config.name}")
                return []
            
            logger.info(f"Found {len(holdings)} holdings in {self.config.name}")
            return holdings
            
        except Exception as e:
            logger.error(f"Error fetching holdings from {self.config.name}: {str(e)}")
            raise

def get_broker_accounts():
    """Get all configured broker accounts from environment variables"""
    accounts = []
    
    # Get Zerodha accounts
    i = 1
    while True:
        api_key = os.getenv(f'ZERODHA_{i}_API_KEY')
        api_secret = os.getenv(f'ZERODHA_{i}_API_SECRET')
        
        if not api_key or not api_secret:
            break
            
        account_name = os.getenv(f'ZERODHA_{i}_ACCOUNT_NAME', f'Zerodha_{i}')
        accounts.append(BrokerConfig(account_name, api_key, api_secret, 'zerodha'))
        i += 1
    
            # Get ICICI accounts
        i = 1
        while True:
            api_key = os.getenv(f'ICICI_{i}_API_KEY')
            api_secret = os.getenv(f'ICICI_{i}_API_SECRET')
            
            if not api_key or not api_secret:
                break
                
            account_name = os.getenv(f'ICICI_{i}_ACCOUNT_NAME', f'ICICI_{i}')
            accounts.append(BrokerConfig(account_name, api_key, api_secret, 'icici'))
            i += 1
    
    return accounts

def process_zerodha_holdings(holdings, account_name):
    """Process Zerodha holdings data into a clean DataFrame"""
    if not holdings:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(holdings)
    
    # Define the columns we want to keep and their display names
    column_mapping = {
        'tradingsymbol': 'symbol',
        'quantity': 'quantity',
        'average_price': 'average_price',
        'last_price': 'last_price',
        'pnl': 'pnl',
        'product': 'product',
        'exchange': 'exchange',
        'isin': 'isin'
    }
    
    # Select and rename columns
    df_clean = df[column_mapping.keys()].copy()
    df_clean.columns = column_mapping.values()
    
    # Calculate additional metrics
    df_clean['investment_value'] = df_clean['quantity'] * df_clean['average_price']
    df_clean['market_value'] = df_clean['quantity'] * df_clean['last_price']
    df_clean['return_percent'] = ((df_clean['last_price'] - df_clean['average_price']) / df_clean['average_price']) * 100
    
    # Round numeric columns
    numeric_columns = ['average_price', 'last_price', 'pnl', 'investment_value', 'market_value', 'return_percent']
    df_clean[numeric_columns] = df_clean[numeric_columns].round(2)
    
    # Add account information
    df_clean['account_name'] = account_name
    df_clean['broker'] = 'Zerodha'
    
    # Sort by market value (descending)
    df_clean = df_clean.sort_values('market_value', ascending=False)
    
    # Reset index
    df_clean = df_clean.reset_index(drop=True)
    
    return df_clean

def process_icici_holdings(holdings, account_name):
    """Process ICICI Direct holdings data into a clean DataFrame"""
    if not holdings:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(holdings)
    
    # Define the columns we want to keep and their display names
    # Note: ICICI column names may differ from Zerodha
    column_mapping = {
        'stock_code': 'symbol',
        'quantity': 'quantity',
        'average_price': 'average_price',
        'last_price': 'last_price',
        'pnl': 'pnl',
        'exchange': 'exchange',
        'isin': 'isin'
    }
    
    # Select and rename columns (handle missing columns gracefully)
    available_columns = [col for col in column_mapping.keys() if col in df.columns]
    df_clean = df[available_columns].copy()
    df_clean.columns = [column_mapping[col] for col in available_columns]
    
    # Add missing columns with default values
    missing_columns = set(column_mapping.values()) - set(df_clean.columns)
    for col in missing_columns:
        if col == 'product':
            df_clean[col] = 'CNC'  # Default for ICICI
        elif col in ['investment_value', 'market_value', 'return_percent']:
            continue  # Will be calculated below
        else:
            df_clean[col] = ''
    
    # Calculate additional metrics
    if 'quantity' in df_clean.columns and 'average_price' in df_clean.columns:
        df_clean['investment_value'] = df_clean['quantity'] * df_clean['average_price']
    else:
        df_clean['investment_value'] = 0
    
    if 'quantity' in df_clean.columns and 'last_price' in df_clean.columns:
        df_clean['market_value'] = df_clean['quantity'] * df_clean['last_price']
    else:
        df_clean['market_value'] = 0
    
    if 'average_price' in df_clean.columns and 'last_price' in df_clean.columns:
        df_clean['return_percent'] = ((df_clean['last_price'] - df_clean['average_price']) / df_clean['average_price']) * 100
    else:
        df_clean['return_percent'] = 0
    
    # Round numeric columns
    numeric_columns = ['average_price', 'last_price', 'pnl', 'investment_value', 'market_value', 'return_percent']
    df_clean[numeric_columns] = df_clean[numeric_columns].round(2)
    
    # Add account information
    df_clean['account_name'] = account_name
    df_clean['broker'] = 'ICICI Direct'
    
    # Sort by market value (descending)
    df_clean = df_clean.sort_values('market_value', ascending=False)
    
    # Reset index
    df_clean = df_clean.reset_index(drop=True)
    
    return df_clean

def create_data_folder():
    """Create /data folder if it doesn't exist"""
    data_folder = "data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        logger.info(f"Created {data_folder} folder")
    return data_folder

def export_to_csv(df, data_folder, account_name, broker_type):
    """Export DataFrame to CSV file in data folder"""
    # Create timestamped file (dd-mm-yyyy format)
    date_str = datetime.now().strftime("%d-%m-%Y")
    timestamped_filename = f"{account_name}_{date_str}.csv"
    timestamped_filepath = os.path.join(data_folder, timestamped_filename)
    
    # Create latest file (accountname_latest.csv)
    latest_filename = f"{account_name}_latest.csv"
    latest_filepath = os.path.join(data_folder, latest_filename)
    
    try:
        # Save to timestamped file
        df.to_csv(timestamped_filepath, index=False)
        logger.info(f"Holdings exported to timestamped file: {timestamped_filepath}")
        
        # Save to latest file (overwrites previous latest)
        df.to_csv(latest_filepath, index=False)
        logger.info(f"Holdings exported to latest file: {latest_filepath}")
        
        return timestamped_filepath, latest_filepath
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        raise

def display_summary(df, account_name, broker_type):
    """Display a summary of the holdings"""
    if df.empty:
        print(f"No holdings data to display for {account_name}")
        return
    
    print(f"\n" + "="*60)
    print(f"📊 HOLDINGS SUMMARY - {account_name} ({broker_type})")
    print("="*60)
    
    # Basic stats
    total_investment = df['investment_value'].sum()
    total_market_value = df['market_value'].sum()
    total_pnl = df['pnl'].sum() if 'pnl' in df.columns else 0
    total_return = ((total_market_value - total_investment) / total_investment) * 100 if total_investment > 0 else 0
    
    print(f"Total Holdings: {len(df)}")
    print(f"Total Investment: ₹{total_investment:,.2f}")
    print(f"Current Market Value: ₹{total_market_value:,.2f}")
    if 'pnl' in df.columns:
        print(f"Total P&L: ₹{total_pnl:,.2f}")
    print(f"Overall Return: {total_return:.2f}%")
    
    # Top 5 holdings by value
    print(f"\n🏆 Top 5 Holdings by Market Value:")
    print("-" * 50)
    for i, (_, row) in enumerate(df.head(5).iterrows(), 1):
        symbol = row.get('symbol', 'N/A')
        market_value = row.get('market_value', 0)
        return_percent = row.get('return_percent', 0)
        print(f"{i}. {symbol:<15} ₹{market_value:>10,.2f} ({return_percent:>6.1f}%)")
    
    # Performance breakdown
    profitable = df[df['return_percent'] > 0]
    loss_making = df[df['return_percent'] < 0]
    
    print(f"\n📈 Performance Breakdown:")
    print(f"   Profitable Holdings: {len(profitable)}")
    print(f"   Loss Making Holdings: {len(loss_making)}")
    
    if not profitable.empty:
        best_performer = profitable.loc[profitable['return_percent'].idxmax()]
        print(f"   Best Performer: {best_performer['symbol']} (+{best_performer['return_percent']:.1f}%)")
    
    if not loss_making.empty:
        worst_performer = loss_making.loc[loss_making['return_percent'].idxmin()]
        print(f"   Worst Performer: {worst_performer['symbol']} ({worst_performer['return_percent']:.1f}%)")

def main():
    """Main function to fetch and export holdings from all broker accounts"""
    try:
        print("🚀 Starting Multi-Broker Holdings Export")
        print("=" * 50)
        
        # Get all configured broker accounts
        accounts = get_broker_accounts()
        
        if not accounts:
            print("❌ No broker accounts found in environment variables")
            print("Please check your .env file and ensure you have configured at least one broker account.")
            return 1
        
        print(f"Found {len(accounts)} broker account(s)")
        for account in accounts:
            print(f"  - {account.name} ({account.broker_type})")
        
        # Create data folder
        data_folder = create_data_folder()
        
        # Initialize token manager
        token_manager = TokenManager()
        
        # Clear expired tokens before starting
        expired_count = token_manager.clear_expired_tokens()
        if expired_count > 0:
            print(f"🧹 Cleaned up {expired_count} expired tokens")
        
        # Process each account
        for account in accounts:
            try:
                print(f"\n{'='*20} Processing {account.name} {'='*20}")
                
                # Create appropriate client based on broker type
                if account.broker_type == 'zerodha':
                    client = ZerodhaClient(account, token_manager)
                elif account.broker_type == 'icici':
                    client = ICICIClient(account, token_manager)
                else:
                    logger.warning(f"Unknown broker type: {account.broker_type}")
                    continue
                
                # Authenticate
                client.authenticate()
                
                # Fetch holdings
                holdings = client.get_holdings()
                
                if holdings:
                    # Process holdings data
                    if account.broker_type == 'zerodha':
                        df = process_zerodha_holdings(holdings, account.name)
                    else:
                        df = process_icici_holdings(holdings, account.name)
                    
                    if not df.empty:
                        # Export to CSV
                        timestamped_filepath, latest_filepath = export_to_csv(df, data_folder, account.name, account.broker_type)
                        
                        # Display summary
                        display_summary(df, account.name, account.broker_type)
                        
                        print(f"✅ Success! Holdings exported to:")
                        print(f"   📅 Timestamped file: {timestamped_filepath}")
                        print(f"   🔄 Latest file: {latest_filepath}")
                    else:
                        print(f"⚠️  No holdings data available for {account.name}")
                else:
                    print(f"⚠️  No holdings found for {account.name}")
                
            except Exception as e:
                logger.error(f"Error processing account {account.name}: {str(e)}")
                print(f"❌ Error processing {account.name}: {str(e)}")
                continue
        
        print(f"\n🎉 Multi-broker holdings export completed!")
        print(f"📁 Check the {data_folder} folder for exported CSV files.")
        print(f"📅 Each account gets a daily timestamped file and a latest file.")
        
        # Display token status
        token_manager.display_token_status()
        
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
