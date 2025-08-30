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
    display_error_message, display_completion_message, display_consolidated_summary
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

def create_consolidated_holdings(data_folder: str) -> tuple[str, str]:
    """
    Create consolidated holdings by merging all account data
    Returns: (timestamped_filepath, latest_filepath)
    """
    import os
    import pandas as pd
    from datetime import datetime
    import pytz
    
    logger.info("Creating consolidated holdings...")
    
    # Create consolidated folder
    consolidated_folder = os.path.join(data_folder, "consolidated_holdings")
    if not os.path.exists(consolidated_folder):
        os.makedirs(consolidated_folder)
        logger.info(f"Created consolidated folder: {consolidated_folder}")
    
    # Get all account folders
    account_folders = []
    for item in os.listdir(data_folder):
        item_path = os.path.join(data_folder, item)
        if os.path.isdir(item_path) and item != "consolidated_holdings":
            account_folders.append(item)
    
    if not account_folders:
        logger.warning("No account folders found for consolidation")
        return None, None
    
    logger.info(f"Found {len(account_folders)} account folders for consolidation")
    
    # Read latest.csv from each account folder
    all_holdings = []
    for account_folder in account_folders:
        latest_file = os.path.join(data_folder, account_folder, "latest.csv")
        if os.path.exists(latest_file):
            try:
                df = pd.read_csv(latest_file)
                if not df.empty:
                    all_holdings.append(df)
                    logger.info(f"Added {len(df)} holdings from {account_folder}")
            except Exception as e:
                logger.error(f"Error reading {latest_file}: {str(e)}")
    
    if not all_holdings:
        logger.warning("No holdings data found for consolidation")
        return None, None
    
    # Concatenate all holdings
    consolidated_df = pd.concat(all_holdings, ignore_index=True)
    logger.info(f"Consolidated {len(consolidated_df)} total holdings from {len(all_holdings)} accounts")
    
    # Keep only the specified columns and rename them consistently
    column_mapping = {
        'symbol': 'Symbol',
        'exchange': 'exchange',
        'quantity': 'quantity',
        'average_price': 'average_price',
        'last_price': 'last_price',
        'investment_value': 'investment_value',
        'market_value': 'market_value',
        'account_name': 'account_name'
    }
    
    # Select only the columns that exist in the DataFrame
    available_columns = [col for col in column_mapping.keys() if col in consolidated_df.columns]
    consolidated_df = consolidated_df[available_columns].copy()
    
    # Rename columns to match the desired format
    consolidated_df.columns = [column_mapping[col] for col in available_columns]
    
    logger.info(f"Selected columns for consolidation: {list(consolidated_df.columns)}")
    
    # Compute profit_loss and return_percent
    if 'average_price' in consolidated_df.columns and 'last_price' in consolidated_df.columns:
        # Calculate profit/loss per share
        consolidated_df['profit_loss'] = consolidated_df['last_price'] - consolidated_df['average_price']
        
        # Calculate return percentage
        consolidated_df['return_percent'] = ((consolidated_df['last_price'] - consolidated_df['average_price']) / consolidated_df['average_price']) * 100
        
        # Handle division by zero (when average_price is 0)
        consolidated_df['return_percent'] = consolidated_df['return_percent'].fillna(0)
        
        logger.info("Calculated profit_loss and return_percent columns")
    
    # Round numeric columns for better readability
    numeric_columns = ['quantity', 'average_price', 'last_price', 'investment_value', 'market_value', 'profit_loss', 'return_percent']
    existing_numeric_columns = [col for col in numeric_columns if col in consolidated_df.columns]
    if existing_numeric_columns:
        consolidated_df[existing_numeric_columns] = consolidated_df[existing_numeric_columns].round(2)
    
    # Sort by market value (descending) for better readability
    if 'market_value' in consolidated_df.columns:
        consolidated_df = consolidated_df.sort_values('market_value', ascending=False)
    
    # Reset index after sorting
    consolidated_df = consolidated_df.reset_index(drop=True)
    
    # Create timestamped file using Indian Standard Time
    ist = pytz.timezone('Asia/Kolkata')
    current_time_ist = datetime.now(ist)
    date_str = current_time_ist.strftime("%Y-%m-%d")
    timestamped_filename = f"{date_str}.csv"
    timestamped_filepath = os.path.join(consolidated_folder, timestamped_filename)
    
    # Create latest file
    latest_filename = "latest.csv"
    latest_filepath = os.path.join(consolidated_folder, latest_filename)
    
    try:
        # Save consolidated data
        consolidated_df.to_csv(timestamped_filepath, index=False)
        consolidated_df.to_csv(latest_filepath, index=False)
        
        logger.info(f"Consolidated holdings exported to: {timestamped_filepath}")
        logger.info(f"Consolidated holdings exported to: {latest_filepath}")
        
        return timestamped_filepath, latest_filepath
        
    except Exception as e:
        logger.error(f"Error exporting consolidated holdings: {str(e)}")
        raise

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
        
        # Create consolidated holdings if we have successful accounts
        if successful_accounts > 0:
            try:
                consolidated_timestamped, consolidated_latest = create_consolidated_holdings(data_folder)
                if consolidated_timestamped and consolidated_latest:
                    print(f"\n🔗 Consolidated holdings created:")
                    print(f"   📅 Date-wise: {consolidated_timestamped}")
                    print(f"   📋 Latest: {consolidated_latest}")
                    
                    # Display consolidated summary
                    try:
                        import pandas as pd
                        consolidated_df = pd.read_csv(consolidated_latest)
                        display_consolidated_summary(consolidated_df, successful_accounts)
                    except Exception as e:
                        logger.error(f"Error displaying consolidated summary: {str(e)}")
                else:
                    print("\n⚠️  Consolidated holdings creation failed")
            except Exception as e:
                logger.error(f"Error creating consolidated holdings: {str(e)}")
                print(f"\n❌ Error creating consolidated holdings: {str(e)}")
        
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
