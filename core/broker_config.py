"""
Broker Configuration Management

This module provides configuration classes for managing broker account settings
and retrieving account information from environment variables.
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BrokerConfig:
    """Configuration class for broker accounts"""
    
    def __init__(self, name: str, api_key: str, api_secret: str, broker_type: str):
        self.name = name
        self.api_key = api_key
        self.api_secret = api_secret
        self.broker_type = broker_type

def get_broker_accounts() -> List[BrokerConfig]:
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
