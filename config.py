import os
from dotenv import load_dotenv
from typing import Dict, List

# Load environment variables
load_dotenv()

class BrokerConfig:
    """Base configuration class for brokers"""
    
    def __init__(self, name: str, api_key: str, api_secret: str, totp_secret: str = None):
        self.name = name
        self.api_key = api_key
        self.api_secret = api_secret
        self.totp_secret = totp_secret

class ZerodhaConfig:
    """Configuration class for Zerodha API"""
    
    # Base URLs
    BASE_URL = "https://api.kite.trade"
    LOGIN_URL = "https://kite.trade/connect/login"
    
    # Session timeout (in seconds)
    SESSION_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def get_accounts() -> List[BrokerConfig]:
        """Get all Zerodha account configurations"""
        accounts = []
        
        # Look for multiple Zerodha accounts
        i = 1
        while True:
            api_key = os.getenv(f'ZERODHA_{i}_API_KEY')
            api_secret = os.getenv(f'ZERODHA_{i}_API_SECRET')
            totp_secret = os.getenv(f'ZERODHA_{i}_TOTP_SECRET')
            
            if not api_key or not api_secret:
                break
                
            account_name = os.getenv(f'ZERODHA_{i}_ACCOUNT_NAME', f'Zerodha Account {i}')
            accounts.append(BrokerConfig(account_name, api_key, api_secret, totp_secret))
            i += 1
        
        return accounts
    
    @staticmethod
    def validate_accounts() -> bool:
        """Validate that at least one Zerodha account is configured"""
        accounts = ZerodhaConfig.get_accounts()
        if not accounts:
            raise ValueError("No Zerodha accounts found in environment variables")
        return True

class ICICIConfig:
    """Configuration class for ICICI Direct (Breeze) API"""
    
    # Base URLs
    BASE_URL = "https://api.icicidirect.com"
    LOGIN_URL = "https://secure.icicidirect.com/IDirectTrading/Trading/TradingPage.aspx"
    
    # Session timeout (in seconds)
    SESSION_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def get_accounts() -> List[BrokerConfig]:
        """Get all ICICI Direct account configurations"""
        accounts = []
        
        # Look for multiple ICICI Direct accounts
        i = 1
        while True:
            api_key = os.getenv(f'ICICI_{i}_API_KEY')
            api_secret = os.getenv(f'ICICI_{i}_API_SECRET')
            totp_secret = os.getenv(f'ICICI_{i}_TOTP_SECRET')
            
            if not api_key or not api_secret:
                break
                
            account_name = os.getenv(f'ICICI_{i}_ACCOUNT_NAME', f'ICICI Direct Account {i}')
            accounts.append(BrokerConfig(account_name, api_key, api_secret, totp_secret))
            i += 1
        
        return accounts
    
    @staticmethod
    def validate_accounts() -> bool:
        """Validate that at least one ICICI Direct account is configured"""
        accounts = ICICIConfig.get_accounts()
        if not accounts:
            raise ValueError("No ICICI Direct accounts found in environment variables")
        return True

class MultiBrokerConfig:
    """Configuration manager for multiple brokers"""
    
    @staticmethod
    def get_all_accounts() -> Dict[str, List[BrokerConfig]]:
        """Get all broker accounts"""
        return {
            "zerodha": ZerodhaConfig.get_accounts(),
            "icici": ICICIConfig.get_accounts()
        }
    
    @staticmethod
    def validate_all_accounts() -> bool:
        """Validate all broker accounts"""
        try:
            ZerodhaConfig.validate_accounts()
            ICICIConfig.validate_accounts()
            return True
        except ValueError as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    @staticmethod
    def get_total_accounts() -> int:
        """Get total number of accounts across all brokers"""
        all_accounts = MultiBrokerConfig.get_all_accounts()
        return sum(len(accounts) for accounts in all_accounts.values()) 