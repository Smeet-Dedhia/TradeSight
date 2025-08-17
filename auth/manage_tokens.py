#!/usr/bin/env python3
"""
Token Management Utility for Multi-Broker Holdings Fetcher

This script allows you to view, manage, and clean up stored authentication tokens.
"""

from token_manager import TokenManager
import argparse

def main():
    """Main function for token management"""
    parser = argparse.ArgumentParser(description="Manage authentication tokens for broker accounts")
    parser.add_argument("--tokens-file", default="tokens.json", help="Path to tokens file (default: tokens.json)")
    parser.add_argument("--clean", action="store_true", help="Clean up expired tokens")
    parser.add_argument("--remove", nargs=2, metavar=("BROKER_TYPE", "ACCOUNT_NAME"), 
                       help="Remove token for specific broker and account")
    parser.add_argument("--info", nargs=2, metavar=("BROKER_TYPE", "ACCOUNT_NAME"),
                       help="Show detailed info for specific token")
    
    args = parser.parse_args()
    
    # Initialize token manager
    token_manager = TokenManager(args.tokens_file)
    
    print("🔑 Token Management Utility")
    print("=" * 50)
    
    if args.clean:
        # Clean expired tokens
        expired_count = token_manager.clear_expired_tokens()
        if expired_count > 0:
            print(f"🧹 Cleaned up {expired_count} expired tokens")
        else:
            print("✨ No expired tokens found")
    
    elif args.remove:
        # Remove specific token
        broker_type, account_name = args.remove
        token_manager.remove_token(broker_type, account_name)
        print(f"🗑️  Removed token for {account_name} ({broker_type})")
    
    elif args.info:
        # Show specific token info
        broker_type, account_name = args.info
        token_info = token_manager.get_token_info(broker_type, account_name)
        
        if token_info:
            print(f"\n📋 TOKEN INFO - {account_name} ({broker_type})")
            print("=" * 50)
            for key, value in token_info.items():
                if key != "token":  # Don't show the actual token for security
                    print(f"{key}: {value}")
        else:
            print(f"❌ No token found for {account_name} ({broker_type})")
    
    else:
        # Default: show all tokens
        token_manager.display_token_status()
        
        # Show summary
        tokens = token_manager.list_all_tokens()
        if tokens:
            valid_tokens = sum(1 for t in tokens if not t.get("is_expired", True))
            expired_tokens = len(tokens) - valid_tokens
            
            print(f"\n📊 SUMMARY")
            print("=" * 30)
            print(f"Total tokens: {len(tokens)}")
            print(f"Valid tokens: {valid_tokens}")
            print(f"Expired tokens: {expired_tokens}")
            
            if expired_tokens > 0:
                print(f"\n💡 Run with --clean to remove expired tokens")

if __name__ == "__main__":
    main()
