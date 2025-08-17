#!/usr/bin/env python3
"""
Multi-Broker Holdings Fetcher (Refactored)

This script fetches current holdings from multiple broker accounts (Zerodha and ICICI Direct)
and exports them to CSV files in the data folder. It handles authentication for each broker
and processes data consistently across different platforms.

This refactored version uses a modular architecture with separate modules for:
- Broker clients (clients/zerodha_client.py, clients/icici_client.py)
- Configuration management (core/broker_config.py)
- Data processing (utils/holdings_processor.py)
- File operations (utils/file_exporter.py)
- Display utilities (utils/display_utils.py)
"""

import logging
from auth.token_manager import TokenManager
from core.broker_config import get_broker_accounts
from clients.zerodha_client import ZerodhaClient
from clients.icici_client import ICICIClient
from utils.holdings_processor import process_zerodha_holdings, process_icici_holdings
from utils.file_exporter import create_data_folder, export_to_csv
from utils.display_utils import (
    display_startup_message, display_accounts_found, display_no_accounts_message,
    display_cleanup_message, display_account_processing_header, display_summary,
    display_success_message, display_no_holdings_message, display_no_data_message,
    display_error_message, display_completion_message
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_account(account, token_manager, data_folder):
    """Process a single broker account"""
    try:
        display_account_processing_header(account.name)
        
        # Create appropriate client based on broker type
        if account.broker_type == 'zerodha':
            client = ZerodhaClient(account, token_manager)
        elif account.broker_type == 'icici':
            client = ICICIClient(account, token_manager)
        else:
            logger.warning(f"Unknown broker type: {account.broker_type}")
            return False
        
        # Authenticate
        client.authenticate()
        
        # Fetch holdings
        holdings = client.get_holdings()
        
        if holdings:
            # Process holdings data
            if account.broker_type == 'zerodha':
                df = process_zerodha_holdings(holdings, account.name)
            else:
                df = process_icici_holdings(holdings, account.name)
            
            if not df.empty:
                # Export to CSV
                timestamped_filepath, latest_filepath = export_to_csv(df, data_folder, account.name, account.broker_type)
                
                # Display summary
                display_summary(df, account.name, account.broker_type)
                
                # Display success message
                display_success_message(account.name, timestamped_filepath, latest_filepath)
                return True
            else:
                display_no_data_message(account.name)
                return False
        else:
            display_no_holdings_message(account.name)
            return False
        
    except Exception as e:
        logger.error(f"Error processing account {account.name}: {str(e)}")
        display_error_message(account.name, str(e))
        return False

def main():
    """Main function to fetch and export holdings from all broker accounts
    
    Note: All timestamps and file naming use Indian Standard Time (IST)
    for consistent day-based operations and proper file sorting.
    """
    try:
        display_startup_message()
        
        # Get all configured broker accounts
        accounts = get_broker_accounts()
        
        if not accounts:
            display_no_accounts_message()
            return 1
        
        display_accounts_found(accounts)
        
        # Create data folder
        data_folder = create_data_folder()
        
        # Initialize token manager
        token_manager = TokenManager()
        
        # Clear expired tokens before starting
        expired_count = token_manager.clear_expired_tokens()
        display_cleanup_message(expired_count)
        
        # Process each account
        successful_accounts = 0
        for account in accounts:
            if process_account(account, token_manager, data_folder):
                successful_accounts += 1
        
        # Display completion message
        display_completion_message(data_folder, token_manager)
        
        print(f"\n📊 Summary: Successfully processed {successful_accounts}/{len(accounts)} accounts")
        
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
