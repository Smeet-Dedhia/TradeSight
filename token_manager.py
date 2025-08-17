#!/usr/bin/env python3
"""
Token Manager for Multi-Broker Holdings Fetcher

This module manages authentication tokens for different broker accounts,
automatically storing and retrieving them with timestamps to avoid
daily re-authentication.
"""

import os
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TokenManager:
    """Manages authentication tokens for broker accounts"""
    
    def __init__(self, tokens_file="tokens.json"):
        self.tokens_file = tokens_file
        self.tokens = self._load_tokens()
    
    def _load_tokens(self):
        """Load existing tokens from JSON file"""
        if os.path.exists(self.tokens_file):
            try:
                with open(self.tokens_file, 'r') as f:
                    tokens = json.load(f)
                logger.info(f"Loaded existing tokens from {self.tokens_file}")
                return tokens
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error loading tokens file: {e}. Creating new tokens file.")
                return {}
        else:
            logger.info(f"Creating new tokens file: {self.tokens_file}")
            return {}
    
    def _save_tokens(self):
        """Save tokens to JSON file"""
        try:
            with open(self.tokens_file, 'w') as f:
                json.dump(self.tokens, f, indent=2)
            logger.info(f"Tokens saved to {self.tokens_file}")
        except IOError as e:
            logger.error(f"Error saving tokens: {e}")
            raise
    
    def _get_token_key(self, broker_type, account_name):
        """Generate a unique key for storing tokens"""
        return f"{broker_type}_{account_name}"
    
    def store_token(self, broker_type, account_name, token, token_type="access_token"):
        """Store a new token with timestamp"""
        key = self._get_token_key(broker_type, account_name)
        
        if key not in self.tokens:
            self.tokens[key] = {}
        
        self.tokens[key].update({
            "broker_type": broker_type,
            "account_name": account_name,
            "token_type": token_type,
            "token": token,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat()
        })
        
        self._save_tokens()
        logger.info(f"Stored {token_type} for {account_name} ({broker_type})")
    
    def get_token(self, broker_type, account_name):
        """Retrieve stored token if it exists and is valid"""
        key = self._get_token_key(broker_type, account_name)
        
        if key not in self.tokens:
            return None
        
        token_data = self.tokens[key]
        
        # Check if token exists
        if "token" not in token_data:
            return None
        
        # Check if token is expired based on broker type
        if self._is_token_expired(token_data, broker_type):
            logger.info(f"Token for {account_name} ({broker_type}) has expired")
            return None
        
        # Update last used timestamp
        token_data["last_used"] = datetime.now().isoformat()
        self._save_tokens()
        
        logger.info(f"Retrieved valid token for {account_name} ({broker_type})")
        return token_data["token"]
    
    def _is_token_expired(self, token_data, broker_type):
        """Check if token is expired based on broker type"""
        if "created_at" not in token_data:
            return True
        
        try:
            created_at = datetime.fromisoformat(token_data["created_at"])
            current_time = datetime.now()
            
            # Different expiration times for different brokers
            if broker_type == "zerodha":
                # Zerodha tokens typically last 24 hours
                expiration_hours = 20  # Conservative: 20 hours
            elif broker_type == "icici":
                # ICICI session tokens typically last 1 hour
                expiration_hours = 0.8  # Conservative: 48 minutes
            else:
                # Default: 1 hour
                expiration_hours = 1
            
            expiration_time = created_at + timedelta(hours=expiration_hours)
            
            return current_time > expiration_time
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing token timestamp: {e}")
            return True
    
    def remove_token(self, broker_type, account_name):
        """Remove a stored token"""
        key = self._get_token_key(broker_type, account_name)
        
        if key in self.tokens:
            del self.tokens[key]
            self._save_tokens()
            logger.info(f"Removed token for {account_name} ({broker_type})")
    
    def clear_expired_tokens(self):
        """Remove all expired tokens"""
        expired_keys = []
        
        for key, token_data in self.tokens.items():
            if self._is_token_expired(token_data, token_data.get("broker_type", "unknown")):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.tokens[key]
            logger.info(f"Removed expired token: {key}")
        
        if expired_keys:
            self._save_tokens()
        
        return len(expired_keys)
    
    def get_token_info(self, broker_type, account_name):
        """Get information about a stored token"""
        key = self._get_token_key(broker_type, account_name)
        
        if key not in self.tokens:
            return None
        
        token_data = self.tokens[key].copy()
        
        # Add expiration status
        token_data["is_expired"] = self._is_token_expired(token_data, broker_type)
        
        # Calculate time until expiration
        if "created_at" in token_data:
            try:
                created_at = datetime.fromisoformat(token_data["created_at"])
                current_time = datetime.now()
                
                if broker_type == "zerodha":
                    expiration_hours = 20
                elif broker_type == "icici":
                    expiration_hours = 0.8
                else:
                    expiration_hours = 1
                
                expiration_time = created_at + timedelta(hours=expiration_hours)
                time_until_expiry = expiration_time - current_time
                
                if time_until_expiry.total_seconds() > 0:
                    hours = int(time_until_expiry.total_seconds() // 3600)
                    minutes = int((time_until_expiry.total_seconds() % 3600) // 60)
                    token_data["expires_in"] = f"{hours}h {minutes}m"
                else:
                    token_data["expires_in"] = "Expired"
                    
            except (ValueError, TypeError):
                token_data["expires_in"] = "Unknown"
        
        return token_data
    
    def list_all_tokens(self):
        """List all stored tokens with their status"""
        token_list = []
        
        for key, token_data in self.tokens.items():
            broker_type = token_data.get("broker_type", "unknown")
            account_name = token_data.get("account_name", "unknown")
            
            token_info = self.get_token_info(broker_type, account_name)
            if token_info:
                token_list.append(token_info)
        
        return token_list
    
    def display_token_status(self):
        """Display status of all stored tokens"""
        tokens = self.list_all_tokens()
        
        if not tokens:
            print("No tokens stored.")
            return
        
        print(f"\n🔑 TOKEN STATUS ({len(tokens)} tokens)")
        print("=" * 60)
        
        for token_info in tokens:
            status = "✅ Valid" if not token_info.get("is_expired", True) else "❌ Expired"
            expires_in = token_info.get("expires_in", "Unknown")
            created_at = token_info.get("created_at", "Unknown")
            last_used = token_info.get("last_used", "Never")
            
            print(f"\n{token_info['account_name']} ({token_info['broker_type']})")
            print(f"  Status: {status}")
            print(f"  Expires in: {expires_in}")
            print(f"  Created: {created_at}")
            print(f"  Last used: {last_used}")
            print(f"  Token type: {token_info.get('token_type', 'Unknown')}")
