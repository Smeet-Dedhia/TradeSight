"""
Display Utilities

This module provides functions for displaying holdings summaries and
formatted console output with emojis and clear formatting.
"""

import os
import pandas as pd
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

def display_summary(df: pd.DataFrame, account_name: str, broker_type: str):
    """Display a summary of the holdings"""
    if df.empty:
        print(f"No holdings data to display for {account_name}")
        return
    
    print(f"\n" + "="*60)
    print(f"📊 HOLDINGS SUMMARY - {account_name} ({broker_type})")
    print("="*60)
    
    # Basic stats
    total_investment = df['investment_value'].sum()
    total_market_value = df['market_value'].sum()
    total_pnl = df['pnl'].sum() if 'pnl' in df.columns else 0
    total_return = ((total_market_value - total_investment) / total_investment) * 100 if total_investment > 0 else 0
    
    print(f"Total Holdings: {len(df)}")
    print(f"Total Investment: ₹{total_investment:,.2f}")
    print(f"Current Market Value: ₹{total_market_value:,.2f}")
    if 'pnl' in df.columns:
        print(f"Total P&L: ₹{total_pnl:,.2f}")
    print(f"Overall Return: {total_return:.2f}%")
    
    # Top 5 holdings by value
    print(f"\n🏆 Top 5 Holdings by Market Value:")
    print("-" * 50)
    for i, (_, row) in enumerate(df.head(5).iterrows(), 1):
        symbol = row.get('symbol', 'N/A')
        market_value = row.get('market_value', 0)
        return_percent = row.get('return_percent', 0)
        print(f"{i}. {symbol:<15} ₹{market_value:>10,.2f} ({return_percent:>6.1f}%)")
    
    # Performance breakdown
    profitable = df[df['return_percent'] > 0]
    loss_making = df[df['return_percent'] < 0]
    
    print(f"\n📈 Performance Breakdown:")
    print(f"   Profitable Holdings: {len(profitable)}")
    print(f"   Loss Making Holdings: {len(loss_making)}")
    
    if not profitable.empty:
        best_performer = profitable.loc[profitable['return_percent'].idxmax()]
        print(f"   Best Performer: {best_performer['symbol']} (+{best_performer['return_percent']:.1f}%)")
    
    if not loss_making.empty:
        worst_performer = loss_making.loc[loss_making['return_percent'].idxmin()]
        print(f"   Worst Performer: {worst_performer['symbol']} ({worst_performer['return_percent']:.1f}%)")

def display_completion_message(data_folder: str, token_manager):
    """Display completion message with token status"""
    # Get current IST time for completion message
    ist = pytz.timezone('Asia/Kolkata')
    current_time_ist = datetime.now(ist)
    completion_time = current_time_ist.strftime("%Y-%m-%d %H:%M:%S IST")
    
    print(f"\n🎉 Multi-broker holdings export completed at {completion_time}!")
    print(f"📁 Check the {data_folder} folder for exported CSV files.")
    print(f"📂 Each account has its own subfolder with daily timestamped files (YYYY-MM-DD.csv) and latest.csv")
    
    # Display token status
    token_manager.display_token_status()

def display_account_processing_header(account_name: str):
    """Display header for account processing"""
    print(f"\n{'='*20} Processing {account_name} {'='*20}")

def display_success_message(account_name: str, timestamped_filepath: str, latest_filepath: str):
    """Display success message for account processing"""
    print(f"✅ Success! Holdings exported to:")
    print(f"   📁 Account folder: data/{account_name}/")
    print(f"   📅 Timestamped file: {os.path.basename(timestamped_filepath)}")
    print(f"   🔄 Latest file: {os.path.basename(latest_filepath)}")

def display_no_holdings_message(account_name: str):
    """Display message when no holdings are found"""
    print(f"⚠️  No holdings found for {account_name}")

def display_no_data_message(account_name: str):
    """Display message when no holdings data is available"""
    print(f"⚠️  No holdings data available for {account_name}")

def display_error_message(account_name: str, error: str):
    """Display error message for account processing"""
    print(f"❌ Error processing {account_name}: {error}")

def display_startup_message():
    """Display startup message"""
    print("🚀 Starting Multi-Broker Holdings Export")
    print("=" * 50)

def display_accounts_found(accounts):
    """Display found broker accounts"""
    print(f"Found {len(accounts)} broker account(s)")
    for account in accounts:
        print(f"  - {account.name} ({account.broker_type})")

def display_no_accounts_message():
    """Display message when no broker accounts are found"""
    print("❌ No broker accounts found in environment variables")
    print("Please check your .env file and ensure you have configured at least one broker account.")

def display_cleanup_message(expired_count: int):
    """Display token cleanup message"""
    if expired_count > 0:
        print(f"🧹 Cleaned up {expired_count} expired tokens")
