import pyotp
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

from config import ZerodhaConfig


class ZerodhaClient:
    """Client for interacting with Zerodha Kite API"""
    
    def __init__(self):
        """Initialize Zerodha client"""
        ZerodhaConfig.validate_config()
        self.api_key = ZerodhaConfig.API_KEY
        self.api_secret = ZerodhaConfig.API_SECRET
        self.totp_secret = ZerodhaConfig.TOTP_SECRET
        self.base_url = ZerodhaConfig.BASE_URL
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.login_time = None
        
    def generate_totp(self) -> str:
        """Generate TOTP for 2FA authentication"""
        if not self.totp_secret:
            raise ValueError("TOTP secret not configured")
        
        totp = pyotp.TOTP(self.totp_secret)
        return totp.now()
    
    def login(self, user_id: str, password: str, pin: str) -> bool:
        """
        Login to Zerodha using user credentials
        
        Args:
            user_id: Zerodha user ID
            password: Zerodha password
            pin: Zerodha PIN
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # Step 1: Get login URL
            login_url = f"{ZerodhaConfig.LOGIN_URL}?api_key={self.api_key}&v=3"
            
            # Step 2: Generate TOTP
            totp = self.generate_totp()
            
            # Step 3: Make login request
            login_data = {
                "user_id": user_id,
                "password": password,
                "pin": pin,
                "totp": totp
            }
            
            response = self.session.post(
                f"{self.base_url}/session/token",
                data=login_data,
                headers={"X-KiteConnect-APIKey": self.api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.access_token = data["data"]["access_token"]
                    self.user_id = user_id
                    self.login_time = datetime.now()
                    return True
                else:
                    print(f"Login failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"Login request failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """Make authenticated request to Zerodha API"""
        if not self.access_token:
            raise ValueError("Not authenticated. Please login first.")
        
        headers = {
            "X-KiteConnect-APIKey": self.api_key,
            "Authorization": f"token {self.api_key}:{self.access_token}"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API request failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error making API request: {str(e)}")
            return None
    
    def get_portfolio(self) -> Optional[Dict]:
        """Fetch current portfolio holdings"""
        try:
            response = self._make_request("/portfolio/positions")
            if response and response.get("status") == "success":
                return response["data"]
            return None
        except Exception as e:
            print(f"Error fetching portfolio: {str(e)}")
            return None
    
    def get_portfolio_holdings(self) -> Optional[List[Dict]]:
        """Fetch portfolio holdings in a simplified format"""
        portfolio = self.get_portfolio()
        if not portfolio:
            return None
        
        holdings = []
        
        # Process net positions (current holdings)
        if "net" in portfolio:
            for position in portfolio["net"]:
                if float(position.get("quantity", 0)) > 0:  # Only positive holdings
                    holding = {
                        "symbol": position.get("tradingsymbol"),
                        "quantity": float(position.get("quantity", 0)),
                        "average_price": float(position.get("average_price", 0)),
                        "last_price": float(position.get("last_price", 0)),
                        "pnl": float(position.get("pnl", 0)),
                        "market_value": float(position.get("market_value", 0)),
                        "instrument_token": position.get("instrument_token"),
                        "exchange": position.get("exchange")
                    }
                    holdings.append(holding)
        
        return holdings
    
    def get_portfolio_summary(self) -> Optional[Dict]:
        """Get portfolio summary with total values"""
        holdings = self.get_portfolio_holdings()
        if not holdings:
            return None
        
        total_investment = sum(holding["quantity"] * holding["average_price"] for holding in holdings)
        total_market_value = sum(holding["market_value"] for holding in holdings)
        total_pnl = sum(holding["pnl"] for holding in holdings)
        
        return {
            "total_holdings": len(holdings),
            "total_investment": total_investment,
            "total_market_value": total_market_value,
            "total_pnl": total_pnl,
            "total_return_percent": (total_pnl / total_investment * 100) if total_investment > 0 else 0
        }
    
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
    
    def is_session_valid(self) -> bool:
        """Check if current session is still valid"""
        if not self.login_time or not self.access_token:
            return False
        
        # Check if session has expired
        elapsed_time = datetime.now() - self.login_time
        return elapsed_time.total_seconds() < ZerodhaConfig.SESSION_TIMEOUT
    
    def logout(self):
        """Logout and clear session"""
        try:
            if self.access_token:
                self._make_request("/session/token", method="DELETE")
        except:
            pass  # Ignore logout errors
        
        self.access_token = None
        self.user_id = None
        self.login_time = None
        self.session.close() 