"""
Holdings Data Processor

This module provides functions for processing holdings data from different brokers
into consistent, clean DataFrames with standardized column names and calculations.
"""

import pandas as pd
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def process_zerodha_holdings(holdings: List[Dict], account_name: str) -> pd.DataFrame:
    """Process Zerodha holdings data into a clean DataFrame"""
    if not holdings:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(holdings)
    
    # Define the columns we want to keep and their display names
    column_mapping = {
        'tradingsymbol': 'symbol',
        'quantity': 'quantity',
        'average_price': 'average_price',
        'last_price': 'last_price',
        'pnl': 'pnl',
        'product': 'product',
        'exchange': 'exchange',
        'isin': 'isin'
    }
    
    # Select and rename columns
    df_clean = df[column_mapping.keys()].copy()
    df_clean.columns = column_mapping.values()
    
    # Calculate additional metrics
    df_clean['investment_value'] = df_clean['quantity'] * df_clean['average_price']
    df_clean['market_value'] = df_clean['quantity'] * df_clean['last_price']
    df_clean['return_percent'] = ((df_clean['last_price'] - df_clean['average_price']) / df_clean['average_price']) * 100
    
    # Round numeric columns
    numeric_columns = ['average_price', 'last_price', 'pnl', 'investment_value', 'market_value', 'return_percent']
    df_clean[numeric_columns] = df_clean[numeric_columns].round(2)
    
    # Add account information
    df_clean['account_name'] = account_name
    df_clean['broker'] = 'Zerodha'
    
    # Sort by market value (descending)
    df_clean = df_clean.sort_values('market_value', ascending=False)
    
    # Reset index
    df_clean = df_clean.reset_index(drop=True)
    
    return df_clean

def process_icici_holdings(holdings: List[Dict], account_name: str) -> pd.DataFrame:
    """Process ICICI Direct holdings data into a clean DataFrame"""
    try:
        if not holdings:
            logger.info("No holdings provided")
            return pd.DataFrame()
        
        # Check if response is successful and contains Success key
        if isinstance(holdings, dict) and 'Success' in holdings:
            # Extract the array of rows from response['Success']
            actual_holdings = holdings['Success']
            logger.info(f"Found {len(actual_holdings)} holdings in response['Success']")
        else:
            # Fallback to direct holdings data
            actual_holdings = holdings
            logger.info(f"Using direct holdings data: {len(actual_holdings)} holdings")
        
        if not actual_holdings:
            logger.warning("No holdings data found in ICICI response")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(actual_holdings)
        logger.info(f"DataFrame created with columns: {list(df.columns)}")
        
        # Define the columns we want to keep and their display names
        # Note: ICICI column names may differ from Zerodha
        column_mapping = {
            'stock_code': 'symbol',
            'stock_ISIN': 'isin',
            'quantity': 'quantity',
            'demat_total_bulk_quantity': 'total_quantity',
            'demat_avail_quantity': 'available_quantity',
            'blocked_quantity': 'blocked_quantity',
            'demat_allocated_quantity': 'allocated_quantity'
        }
        
        # Select and rename columns (handle missing columns gracefully)
        available_columns = [col for col in column_mapping.keys() if col in df.columns]
        df_clean = df[available_columns].copy()
        df_clean.columns = [column_mapping[col] for col in available_columns]
        
        # Add missing columns with default values
        missing_columns = set(column_mapping.values()) - set(df_clean.columns)
        for col in missing_columns:
            if col == 'product':
                df_clean[col] = 'CNC'  # Default for ICICI
            elif col in ['investment_value', 'market_value', 'return_percent']:
                continue  # Will be calculated below
            else:
                df_clean[col] = ''
        
        # Add default values for missing columns that ICICI doesn't provide
        df_clean['product'] = 'CNC'  # Default for ICICI
        df_clean['exchange'] = 'NSE'  # Default exchange
        df_clean['average_price'] = 0  # ICICI doesn't provide this
        df_clean['last_price'] = 0    # ICICI doesn't provide this
        df_clean['pnl'] = 0           # ICICI doesn't provide this
        
        # Calculate additional metrics (set to 0 since ICICI doesn't provide price data)
        df_clean['investment_value'] = 0
        df_clean['market_value'] = 0
        df_clean['return_percent'] = 0
        
        # Round numeric columns
        numeric_columns = ['quantity', 'total_quantity', 'available_quantity', 'blocked_quantity', 'allocated_quantity']
        df_clean[numeric_columns] = df_clean[numeric_columns].round(0)
        
        # Add account information
        df_clean['account_name'] = account_name
        df_clean['broker'] = 'ICICI Direct'
        
        # Sort by market value (descending)
        df_clean = df_clean.sort_values('market_value', ascending=False)
        
        # Reset index
        df_clean = df_clean.reset_index(drop=True)
        
        logger.info(f"Successfully processed ICICI holdings. Final DataFrame shape: {df_clean.shape}")
        return df_clean
        
    except Exception as e:
        logger.error(f"Error processing ICICI holdings: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
