#!/usr/bin/env python3
"""
TradeSight Dummy Data Generator

This script creates realistic mock portfolio data for the TradeSight dashboard.
It generates:
1. A consolidated 'latest.csv' file containing diverse stock holdings across multiple accounts.
2. A series of historical monthly files (e.g. YYYY-MM-DD.csv) spanning the past 12 months,
   simulating a realistic, positive growth trend with authentic market volatility.

This is highly useful for demonstrating or screenshotting the Streamlit dashboard
without exposing sensitive personal financial data.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_data():
    print("Starting mock portfolio data generation...")

    # Define directory path
    folder_path = os.path.join("data", "consolidated_holdings")
    os.makedirs(folder_path, exist_ok=True)
    print(f"Target folder ensured: {folder_path}")

    # 1. Define Stock Portfolio Configuration
    # We use popular Indian blue-chip and high-growth stocks for realistic presentation
    stocks_pool = [
        {"Symbol": "RELIANCE", "exchange": "NSE", "base_buy": 2100.0, "qty_range": (30, 80), "accounts": ["Zerodha_Personal", "ICICI_Family"]},
        {"Symbol": "TCS", "exchange": "NSE", "base_buy": 3200.0, "qty_range": (15, 40), "accounts": ["Zerodha_Personal", "Zerodha_Spouse"]},
        {"Symbol": "HDFCBANK", "exchange": "NSE", "base_buy": 1350.0, "qty_range": (50, 150), "accounts": ["Zerodha_Personal", "ICICI_Family", "Zerodha_Spouse"]},
        {"Symbol": "INFY", "exchange": "NSE", "base_buy": 1250.0, "qty_range": (40, 100), "accounts": ["Zerodha_Spouse"]},
        {"Symbol": "ITC", "exchange": "NSE", "base_buy": 210.0, "qty_range": (200, 500), "accounts": ["ICICI_Family", "Zerodha_Personal"]},
        {"Symbol": "L&T", "exchange": "NSE", "base_buy": 1800.0, "qty_range": (10, 30), "accounts": ["Zerodha_Personal"]},
        {"Symbol": "SBIN", "exchange": "NSE", "base_buy": 420.0, "qty_range": (100, 300), "accounts": ["ICICI_Family"]},
        {"Symbol": "TATASTEEL", "exchange": "NSE", "base_buy": 95.0, "qty_range": (300, 800), "accounts": ["Zerodha_Spouse", "Zerodha_Personal"]},
        {"Symbol": "BHARTIRTIL", "exchange": "NSE", "base_buy": 680.0, "qty_range": (50, 120), "accounts": ["Zerodha_Personal"]},
        {"Symbol": "ICICIBANK", "exchange": "NSE", "base_buy": 710.0, "qty_range": (60, 180), "accounts": ["ICICI_Family", "Zerodha_Spouse"]}
    ]

    # Seed for deterministic yet realistic outputs
    np.random.seed(42)

    # 2. Build the current portfolio (latest.csv)
    latest_rows = []
    
    # Simulating current price adjustments (mostly gains for a cool looking portfolio)
    price_multipliers = {
        "RELIANCE": 1.35,     # +35%
        "TCS": 1.18,          # +18%
        "HDFCBANK": 1.22,     # +22%
        "INFY": 1.15,         # +15%
        "ITC": 1.85,          # +85% (the classic ITC rally!)
        "L&T": 1.50,          # +50%
        "SBIN": 1.62,         # +62%
        "TATASTEEL": 1.40,    # +40%
        "BHARTIRTIL": 1.28,   # +28%
        "ICICIBANK": 1.45     # +45%
    }

    for stock in stocks_pool:
        for acc in stock["accounts"]:
            qty = np.random.randint(stock["qty_range"][0], stock["qty_range"][1])
            # Add minor random noise to average buy price per account
            avg_price = round(stock["base_buy"] * np.random.uniform(0.96, 1.04), 2)
            
            # Current price based on multipliers
            last_price = round(stock["base_buy"] * price_multipliers[stock["Symbol"]] * np.random.uniform(0.98, 1.02), 2)
            
            inv_val = round(qty * avg_price, 2)
            mkt_val = round(qty * last_price, 2)
            pnl = round(mkt_val - inv_val, 2)
            ret_pct = round((pnl / inv_val) * 100, 2)

            latest_rows.append({
                "Symbol": stock["Symbol"],
                "exchange": stock["exchange"],
                "quantity": qty,
                "average_price": avg_price,
                "last_price": last_price,
                "investment_value": inv_val,
                "market_value": mkt_val,
                "account_name": acc,
                "profit_loss": pnl,
                "return_percent": ret_pct
            })

    df_latest = pd.DataFrame(latest_rows)
    latest_path = os.path.join(folder_path, "latest.csv")
    df_latest.to_csv(latest_path, index=False)
    print(f"Generated current holdings: {latest_path} ({len(df_latest)} holdings)")

    # 3. Build Historical Portfolio Growth over past 12 months
    # We will generate monthly files to showcase beautiful line chart progression
    history_dates = []
    today = datetime.now()
    
    # Generate dates for the last 12 months (end of each month)
    for i in range(12, -1, -1):
        # Go back i months
        date = today - timedelta(days=30 * i)
        # Standardize to last day of that month roughly
        if i == 0:
            history_dates.append(today)
        else:
            # Set to last day of that month
            next_month = date.replace(day=28) + timedelta(days=4)
            last_day = next_month - timedelta(days=next_month.day)
            history_dates.append(last_day)

    # Let's generate a time series where the portfolio values grow steadily
    # We will scale historical market values down for older dates
    # June 2025 starts at ~70% value, climbing to 100% (today) with some realistic dips
    growth_trend = [0.70, 0.73, 0.71, 0.76, 0.81, 0.84, 0.80, 0.86, 0.91, 0.94, 0.93, 0.97, 1.00]
    
    for idx, date in enumerate(history_dates):
        date_str = date.strftime("%Y-%m-%d")
        scale = growth_trend[idx]
        
        hist_rows = []
        for _, row in df_latest.iterrows():
            # Scale down the last price and quantities for older dates to simulate growth
            hist_qty = int(row["quantity"] * (0.85 + (scale * 0.15)))  # Slightly less quantity in the past
            if hist_qty <= 0:
                hist_qty = 1
                
            # Scale last price based on the historical trend
            hist_last_price = round(row["last_price"] * (scale * np.random.uniform(0.97, 1.03)), 2)
            
            # Keep buy price the same or slightly different
            hist_avg_price = row["average_price"]
            
            inv_val = round(hist_qty * hist_avg_price, 2)
            mkt_val = round(hist_qty * hist_last_price, 2)
            pnl = round(mkt_val - inv_val, 2)
            ret_pct = round((pnl / inv_val) * 100, 2)

            hist_rows.append({
                "Symbol": row["Symbol"],
                "exchange": row["exchange"],
                "quantity": hist_qty,
                "average_price": hist_avg_price,
                "last_price": hist_last_price,
                "investment_value": inv_val,
                "market_value": mkt_val,
                "account_name": row["account_name"],
                "profit_loss": pnl,
                "return_percent": ret_pct
            })

        df_hist = pd.DataFrame(hist_rows)
        hist_path = os.path.join(folder_path, f"{date_str}.csv")
        df_hist.to_csv(hist_path, index=False)
        print(f"Generated historical snapshot for {date_str}: {hist_path}")

    print("\nPortfolio mock data generation completed successfully!")
    print("You can now run streamlit run dashboard.py to view the beautiful dashboard.")

if __name__ == "__main__":
    generate_mock_data()
