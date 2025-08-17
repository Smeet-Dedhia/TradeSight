"""
File Export Utilities

This module provides functions for exporting holdings data to CSV files
with both timestamped and latest file naming conventions.
"""

import os
import pandas as pd
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

def create_data_folder() -> str:
    """Create /data folder if it doesn't exist"""
    data_folder = "data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        logger.info(f"Created {data_folder} folder")
    return data_folder

def export_to_csv(df: pd.DataFrame, data_folder: str, account_name: str, broker_type: str) -> tuple[str, str]:
    """
    Export DataFrame to CSV file in account-specific folder within data folder
    
    Returns:
        tuple: (timestamped_filepath, latest_filepath)
    """
    # Create account-specific folder
    account_folder = os.path.join(data_folder, account_name)
    if not os.path.exists(account_folder):
        os.makedirs(account_folder)
        logger.info(f"Created account folder: {account_folder}")
    
    # Create timestamped file using Indian Standard Time (YYYY-MM-DD format for proper sorting)
    ist = pytz.timezone('Asia/Kolkata')
    current_time_ist = datetime.now(ist)
    date_str = current_time_ist.strftime("%Y-%m-%d")
    timestamped_filename = f"{date_str}.csv"
    timestamped_filepath = os.path.join(account_folder, timestamped_filename)
    
    # Create latest file (latest.csv)
    latest_filename = "latest.csv"
    latest_filepath = os.path.join(account_folder, latest_filename)
    
    try:
        # Save to timestamped file
        df.to_csv(timestamped_filepath, index=False)
        logger.info(f"Holdings exported to timestamped file: {timestamped_filepath}")
        
        # Save to latest file (overwrites previous latest)
        df.to_csv(latest_filepath, index=False)
        logger.info(f"Holdings exported to latest file: {latest_filepath}")
        
        return timestamped_filepath, latest_filepath
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        raise
