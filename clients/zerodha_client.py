"""
Zerodha Client for API Operations

This module provides a client for interacting with Zerodha's Kite API,
handling authentication, token management, and data fetching.
"""

import logging
from kiteconnect import KiteConnect
from typing import List, Dict, Optional
from core.broker_config import BrokerConfig
from auth.token_manager import TokenManager

logger = logging.getLogger(__name__)

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
    
    def get_holdings(self) -> List[Dict]:
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
