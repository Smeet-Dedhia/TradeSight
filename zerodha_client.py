import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from kiteconnect import KiteConnect

from myconfig import BrokerConfig, ZerodhaConfig


class ZerodhaClient:
    """Client for interacting with Zerodha Kite API using proper KiteConnect authentication"""
    
    def __init__(self, account_config: BrokerConfig):
        """Initialize Zerodha client"""
        self.account_name = account_config.name
        self.api_key = account_config.api_key
        self.api_secret = account_config.api_secret
        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token = None
        self.user_id = None
        self.login_time = None
        
    def get_login_url(self) -> str:
        """
        Get the login URL for manual authentication
        
        Returns:
            str: Login URL that user should visit in browser
        """
        return self.kite.login_url()
    
    def authenticate_with_request_token(self, request_token: str) -> bool:
        """
        Authenticate using the request token received after manual login
        
        Args:
            request_token: Request token received from redirect URL after manual login
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not self.api_secret:
                print(f"❌ Missing API secret for {self.account_name}")
                return False
                
            # Generate session using request token and API secret
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            
            # Set the access token
            self.kite.set_access_token(data["access_token"])
            self.access_token = data["access_token"]
            self.user_id = data.get("user_id")
            self.login_time = datetime.now()
            
            print(f"✅ Zerodha authentication successful for {self.account_name}")
            print(f"   User ID: {self.user_id}")
            print(f"   Access Token: {self.access_token[:20]}...")
            return True
            
        except Exception as e:
            print(f"❌ Zerodha authentication failed for {self.account_name}: {str(e)}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self.access_token is not None and self.kite.access_token is not None
    
    def get_portfolio_holdings(self) -> Optional[List[Dict]]:
        """Fetch portfolio holdings using KiteConnect API"""
        if not self.is_authenticated():
            print(f"❌ Not authenticated for {self.account_name}. Please authenticate first.")
            return None
            
        try:
            # Get holdings using KiteConnect
            holdings = self.kite.holdings()
            
            if not holdings:
                return []
            
            processed_holdings = []
            for holding in holdings:
                processed_holding = {
                    "symbol": holding.get("tradingsymbol"),
                    "quantity": float(holding.get("quantity", 0)),
                    "average_price": float(holding.get("average_price", 0)),
                    "last_price": float(holding.get("last_price", 0)),
                    "pnl": float(holding.get("pnl", 0)),
                    "market_value": float(holding.get("market_value", 0)),
                    "instrument_token": holding.get("instrument_token"),
                    "exchange": holding.get("exchange"),
                    "account_name": self.account_name,
                    "broker": "Zerodha"
                }
                processed_holdings.append(processed_holding)
            
            return processed_holdings
            
        except Exception as e:
            print(f"❌ Error fetching portfolio holdings for {self.account_name}: {str(e)}")
            return None
    
    def get_portfolio_positions(self) -> Optional[List[Dict]]:
        """Fetch current positions using KiteConnect API"""
        if not self.is_authenticated():
            print(f"❌ Not authenticated for {self.account_name}. Please authenticate first.")
            return None
            
        try:
            # Get positions using KiteConnect
            positions = self.kite.positions()
            
            if not positions or "net" not in positions:
                return []
            
            processed_positions = []
            for position in positions["net"]:
                if float(position.get("quantity", 0)) != 0:  # Only non-zero positions
                    processed_position = {
                        "symbol": position.get("tradingsymbol"),
                        "quantity": float(position.get("quantity", 0)),
                        "average_price": float(position.get("average_price", 0)),
                        "last_price": float(position.get("last_price", 0)),
                        "pnl": float(position.get("pnl", 0)),
                        "market_value": float(position.get("market_value", 0)),
                        "instrument_token": position.get("instrument_token"),
                        "exchange": position.get("exchange"),
                        "account_name": self.account_name,
                        "broker": "Zerodha"
                    }
                    processed_positions.append(processed_position)
            
            return processed_positions
            
        except Exception as e:
            print(f"❌ Error fetching portfolio positions for {self.account_name}: {str(e)}")
            return None
    
    def get_portfolio_as_dataframe(self) -> Optional[pd.DataFrame]:
        """Get portfolio holdings as a pandas DataFrame"""
        holdings = self.get_portfolio_holdings()
        if not holdings:
            return None
        
        df = pd.DataFrame(holdings)
        
        # Add calculated columns
        df["investment_value"] = df["quantity"] * df["average_price"]
        df["return_percent"] = (df["pnl"] / df["investment_value"] * 100).round(2)
        
        # Sort by market value (descending)
        df = df.sort_values("market_value", ascending=False).reset_index(drop=True)
        
        return df
    
    def get_portfolio_summary(self) -> Optional[Dict]:
        """Get portfolio summary with total values"""
        holdings = self.get_portfolio_holdings()
        if not holdings:
            return None
        
        total_investment = sum(holding["quantity"] * holding["average_price"] for holding in holdings)
        total_market_value = sum(holding["market_value"] for holding in holdings)
        total_pnl = sum(holding["pnl"] for holding in holdings)
        
        return {
            "account_name": self.account_name,
            "broker": "Zerodha",
            "total_holdings": len(holdings),
            "total_investment": total_investment,
            "total_market_value": total_market_value,
            "total_pnl": total_pnl,
            "total_return_percent": (total_pnl / total_investment * 100) if total_investment > 0 else 0
        }
    
    def get_margins(self) -> Optional[Dict]:
        """Get account margins using KiteConnect API"""
        if not self.is_authenticated():
            print(f"❌ Not authenticated for {self.account_name}. Please authenticate first.")
            return None
            
        try:
            margins = self.kite.margins()
            return margins
        except Exception as e:
            print(f"❌ Error fetching margins for {self.account_name}: {str(e)}")
            return None
    
    def get_orders(self) -> Optional[List[Dict]]:
        """Get order history using KiteConnect API"""
        if not self.is_authenticated():
            print(f"❌ Not authenticated for {self.account_name}. Please authenticate first.")
            return None
            
        try:
            orders = self.kite.orders()
            return orders
        except Exception as e:
            print(f"❌ Error fetching orders for {self.account_name}: {str(e)}")
            return None
    
    def is_session_valid(self) -> bool:
        """Check if current session is still valid"""
        if not self.login_time or not self.access_token:
            return False
        
        # Check if session has expired (Zerodha sessions typically last 24 hours)
        elapsed_time = datetime.now() - self.login_time
        return elapsed_time.total_seconds() < ZerodhaConfig.SESSION_TIMEOUT
    
    def logout(self):
        """Logout and clear session"""
        self.access_token = None
        self.user_id = None
        self.login_time = None
        # Note: KiteConnect doesn't have a logout method, we just clear our local state
        print(f"✅ Logged out from {self.account_name}")
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information using KiteConnect API"""
        if not self.is_authenticated():
            print(f"❌ Not authenticated for {self.account_name}. Please authenticate first.")
            return None
            
        try:
            profile = self.kite.profile()
            return profile
        except Exception as e:
            print(f"❌ Error fetching profile for {self.account_name}: {str(e)}")
            return None 