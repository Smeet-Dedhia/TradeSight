import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ZerodhaConfig:
    """Configuration class for Zerodha API"""
    
    # Zerodha API credentials
    API_KEY = os.getenv('ZERODHA_API_KEY')
    API_SECRET = os.getenv('ZERODHA_API_SECRET')
    
    # TOTP secret for 2FA (if using TOTP)
    TOTP_SECRET = os.getenv('ZERODHA_TOTP_SECRET')
    
    # Base URLs
    BASE_URL = "https://api.kite.trade"
    LOGIN_URL = "https://kite.trade/connect/login"
    
    # Session timeout (in seconds)
    SESSION_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        if not cls.API_KEY:
            raise ValueError("ZERODHA_API_KEY not found in environment variables")
        if not cls.API_SECRET:
            raise ValueError("ZERODHA_API_SECRET not found in environment variables")
        
        return True 