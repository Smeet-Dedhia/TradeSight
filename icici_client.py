import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

from config import BrokerConfig, ICICIConfig


class ICICIClient:
    """Client for interacting with ICICI Direct (Breeze) API"""
    
    def __init__(self, account_config: BrokerConfig):
        """Initialize ICICI Direct client"""
        self.account_name = account_config.name
        self.api_key = account_config.api_key
        self.api_secret = account_config.api_secret
        self.totp_secret = account_config.totp_secret
        self.base_url = ICICIConfig.BASE_URL
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.login_time = None
        
    def login(self, user_id: str, password: str, pin: str) -> bool:
        """
        Login to ICICI Direct using user credentials
        
        Args:
            user_id: ICICI Direct user ID
            password: ICICI Direct password
            pin: ICICI Direct PIN
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # ICICI Direct login process
            login_data = {
                "user_id": user_id,
                "password": password,
                "pin": pin,
                "api_key": self.api_key,
                "api_secret": self.api_secret
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.access_token = data["data"]["access_token"]
                    self.user_id = user_id
                    self.login_time = datetime.now()
                    return True
                else:
                    print(f"ICICI Direct login failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"ICICI Direct login request failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error during ICICI Direct login: {str(e)}")
            return False
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """Make authenticated request to ICICI Direct API"""
        if not self.access_token:
            raise ValueError("Not authenticated. Please login first.")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
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
                print(f"ICICI Direct API request failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error making ICICI Direct API request: {str(e)}")
            return None
    
    def get_portfolio(self) -> Optional[Dict]:
        """Fetch current portfolio holdings from ICICI Direct"""
        try:
            response = self._make_request("/portfolio/holdings")
            if response and response.get("status") == "success":
                return response["data"]
            return None
        except Exception as e:
            print(f"Error fetching ICICI Direct portfolio: {str(e)}")
            return None
    
    def get_portfolio_holdings(self) -> Optional[List[Dict]]:
        """Fetch portfolio holdings in a simplified format"""
        portfolio = self.get_portfolio()
        if not portfolio:
            return None
        
        holdings = []
        
        # Process holdings data (structure may vary based on ICICI Direct API)
        if "holdings" in portfolio:
            for holding in portfolio["holdings"]:
                if float(holding.get("quantity", 0)) > 0:  # Only positive holdings
                    holding_data = {
                        "symbol": holding.get("symbol") or holding.get("tradingsymbol"),
                        "quantity": float(holding.get("quantity", 0)),
                        "average_price": float(holding.get("average_price", 0)),
                        "last_price": float(holding.get("last_price", 0)),
                        "pnl": float(holding.get("pnl", 0)),
                        "market_value": float(holding.get("market_value", 0)),
                        "instrument_token": holding.get("instrument_token"),
                        "exchange": holding.get("exchange", "NSE"),
                        "account_name": self.account_name,
                        "broker": "ICICI Direct"
                    }
                    holdings.append(holding_data)
        
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
            "account_name": self.account_name,
            "broker": "ICICI Direct",
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
        return elapsed_time.total_seconds() < ICICIConfig.SESSION_TIMEOUT
    
    def logout(self):
        """Logout and clear session"""
        try:
            if self.access_token:
                self._make_request("/auth/logout", method="POST")
        except:
            pass  # Ignore logout errors
        
        self.access_token = None
        self.user_id = None
        self.login_time = None
        self.session.close() 