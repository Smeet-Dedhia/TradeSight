"""
ICICI Direct Client for API Operations

This module provides a client for interacting with ICICI Direct's Breeze API,
handling authentication, token management, and data fetching.
"""

import logging
from breeze_connect import BreezeConnect
from typing import List, Dict, Optional
import urllib.parse
from core.broker_config import BrokerConfig
from auth.token_manager import TokenManager

logger = logging.getLogger(__name__)

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
                holdings = self.breeze.get_portfolio_holdings(exchange_code="NSE")
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
    
    def get_holdings(self) -> List[Dict]:
        """Fetch holdings from ICICI Direct"""
        if not self.authenticated:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        logger.info(f"Fetching holdings from ICICI Direct account: {self.config.name}")
        
        try:
            holdings = self.breeze.get_portfolio_holdings(exchange_code="NSE")
            
            if not holdings:
                logger.warning(f"No holdings found in {self.config.name}")
                return []
            
            logger.info(f"Found {len(holdings)} holdings in {self.config.name}")
            return holdings
            
        except Exception as e:
            logger.error(f"Error fetching holdings from {self.config.name}: {str(e)}")
            raise
