"""
Stock Data Manager for ICICI BreezeConnect API

Auto-loads credentials from tokens.json and .env file.
Setup: Create .env with ICICI_1_API_KEY and ICICI_1_API_SECRET
"""

from breeze_connect import BreezeConnect
import datetime
import pytz
import json
import os
from typing import Dict, List, Optional


def get_ist_datetime(days_offset: int = 0) -> str:
    """Get datetime string in IST with optional day offset"""
    ist = pytz.timezone('Asia/Kolkata')
    dt = datetime.datetime.now(ist) + datetime.timedelta(days=days_offset)
    return dt.strftime("%Y-%m-%dT07:00:00.000Z")


def load_icici_credentials(account_name: str = "icici_ICICI_Yogesh") -> Dict[str, str]:
    """Load ICICI credentials from tokens.json and .env file"""
    try:
        tokens_file = os.path.join(os.path.dirname(__file__), "tokens.json")
        with open(tokens_file, 'r') as f:
            tokens_data = json.load(f)
        
        if account_name not in tokens_data:
            raise ValueError(f"Account {account_name} not found in tokens.json")
        
        session_token = tokens_data[account_name].get("token")
        if not session_token:
            raise ValueError(f"Session token not found for {account_name}")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("ICICI_1_API_KEY")
        api_secret = os.getenv("ICICI_1_API_SECRET")
        
        if not api_key or not api_secret:
            raise ValueError("ICICI_1_API_KEY and ICICI_1_API_SECRET must be set in .env file")
        
        return {"api_key": api_key, "api_secret": api_secret, "session_token": session_token}
        
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return {}


class StockDataManager:
    """Manages stock data operations using BreezeConnect API"""
    
    def __init__(self, account_name: str = "icici_ICICI_Yogesh"):
        """Initialize with credentials from tokens.json and .env"""
        credentials = load_icici_credentials(account_name)
        if not credentials:
            raise ValueError(f"Could not load credentials for {account_name}")
        
        self.breeze = BreezeConnect(api_key=credentials["api_key"])
        self.breeze.generate_session(
            api_secret=credentials["api_secret"], 
            session_token=credentials["session_token"]
        )
    
    def get_historical_data(
        self,
        symbol: str,
        exchange_code: str = "NSE",
        from_date: str = None,
        to_date: str = None,
        interval: str = "1day",
        product_type: str = "cash"
    ) -> Dict:
        """Get historical stock data for a given symbol"""
        if not from_date:
            from_date = get_ist_datetime(-30)
        if not to_date:
            to_date = get_ist_datetime(0)
        
        try:
            return self.breeze.get_historical_data(
                interval=interval,
                from_date=from_date,
                to_date=to_date,
                stock_code=symbol,
                exchange_code=exchange_code,
                product_type=product_type
            )
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {str(e)}")
            return {}
    
    def get_last_price(self, symbol: str, exchange_code: str = "NSE") -> Optional[float]:
        """Get the last available price (yesterday's close) for a given symbol"""
        try:
            data = self.breeze.get_historical_data(
                interval="1day",
                from_date=get_ist_datetime(-3),  # Reduced from -3 to -1 for faster response
                to_date=get_ist_datetime(0),
                stock_code=symbol,
                exchange_code=exchange_code,
                product_type="cash"
            )
            
            if data and data.get('Success'):
                latest_data = max(data['Success'], key=lambda x: x.get('datetime', ''))
                return float(latest_data.get('close', 0))
            return None
            
        except Exception as e:
            print(f"Error fetching last price for {symbol}: {str(e)}")
            return None



