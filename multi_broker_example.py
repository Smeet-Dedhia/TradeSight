#!/usr/bin/env python3
"""
Multi-Broker Portfolio Management Example
This script demonstrates how to manage multiple broker accounts and consolidate portfolios
"""

import os
from dotenv import load_dotenv
from multi_broker_manager import MultiBrokerManager

def main():
    """Main function demonstrating multi-broker portfolio management"""
    
    # Load environment variables
    load_dotenv()
    
    print("🚀 TradeSight - Multi-Broker Portfolio Tracker")
    print("=" * 60)
    
    try:
        # Initialize multi-broker manager
        print("📡 Initializing multi-broker manager...")
        manager = MultiBrokerManager()
        
        if not manager.initialize_brokers():
            print("❌ Failed to initialize brokers")
            return
        
        # Get account information
        all_accounts = manager.broker_clients
        print(f"\n📋 Found {len(all_accounts)} broker accounts:")
        for account_name, info in all_accounts.items():
            print(f"  • {account_name} ({info['broker']})")
        
        # Get user credentials for all accounts
        print("\n🔐 Please provide credentials for each account:")
        credentials = {}
        
        for account_name in all_accounts.keys():
            print(f"\n--- {account_name} ---")
            user_id = input(f"User ID: ").strip()
            password = input(f"Password: ").strip()
            pin = input(f"PIN: ").strip()
            
            credentials[account_name] = {
                "user_id": user_id,
                "password": password,
                "pin": pin
            }
        
        # Login to all accounts
        print("\n🔑 Logging into all accounts...")
        login_results = manager.login_all_accounts(credentials)
        
        successful_logins = sum(1 for success in login_results.values() if success)
        print(f"\n✅ Successfully logged into {successful_logins}/{len(login_results)} accounts")
        
        if successful_logins == 0:
            print("❌ No accounts could be logged into. Exiting.")
            return
        
        # Fetch all portfolios
        print("\n📊 Fetching portfolios from all accounts...")
        if not manager.fetch_all_portfolios():
            print("❌ Failed to fetch portfolios")
            return
        
        # Get consolidated overview
        print("\n📈 Generating consolidated portfolio overview...")
        overview = manager.get_consolidated_overview()
        
        if overview:
            print("\n" + "="*60)
            print("📊 CONSOLIDATED PORTFOLIO OVERVIEW")
            print("="*60)
            
            # Display account summaries
            print(f"\n🏦 Account Summaries ({overview['total_accounts']} accounts):")
            print("-" * 40)
            for account_name, summary in overview['account_summaries'].items():
                print(f"\n{account_name} ({summary['broker']}):")
                print(f"  Holdings: {summary['total_holdings']}")
                print(f"  Investment: ₹{summary['total_investment']:,.2f}")
                print(f"  Current Value: ₹{summary['total_market_value']:,.2f}")
                print(f"  P&L: ₹{summary['total_pnl']:,.2f}")
                print(f"  Return: {summary['total_return_percent']:.2f}%")
            
            # Display consolidated summary
            consolidated = overview['consolidated_summary']
            print(f"\n📊 CONSOLIDATED SUMMARY:")
            print(f"  Total Holdings: {overview['total_holdings']}")
            print(f"  Total Investment: ₹{consolidated['total_investment']:,.2f}")
            print(f"  Total Current Value: ₹{consolidated['total_market_value']:,.2f}")
            print(f"  Total P&L: ₹{consolidated['total_pnl']:,.2f}")
            print(f"  Total Return: {consolidated['total_return_percent']:.2f}%")
            
            # Display broker breakdown
            print(f"\n🏛️  Broker Breakdown:")
            print("-" * 30)
            for broker, stats in overview['broker_breakdown'].items():
                print(f"\n{broker}:")
                print(f"  Holdings: {stats['holdings_count']}")
                print(f"  Total Value: ₹{stats['total_value']:,.2f}")
                print(f"  Total P&L: ₹{stats['total_pnl']:,.2f}")
                print(f"  Avg Return: {stats['avg_return']:.2f}%")
            
            # Display top holdings
            print(f"\n🏆 Top 10 Holdings:")
            print("-" * 30)
            for i, holding in enumerate(overview['top_holdings'], 1):
                print(f"{i:2d}. {holding['symbol']:15} ₹{holding['market_value']:10,.0f} "
                      f"({holding['return_percent']:+6.2f}%) [{holding['account_name']}]")
            
            # Display risk metrics
            risk_metrics = overview['risk_metrics']
            print(f"\n⚠️  Risk Metrics:")
            print(f"  Portfolio Return: {risk_metrics['portfolio_return_percent']:.2f}%")
            print(f"  Concentration Risk: {risk_metrics['concentration_risk']:.4f}")
            print(f"  Max Single Holding: {risk_metrics['max_single_holding_weight']:.2f}%")
            print(f"  Top 10 Holdings Weight: {risk_metrics['top_10_holdings_weight']:.2f}%")
            
            # Display performance metrics
            perf_metrics = overview['performance_metrics']
            print(f"\n📊 Performance Metrics:")
            print(f"  Weighted Average Return: {perf_metrics['weighted_average_return']:.2f}%")
            print(f"  Best Performer: {perf_metrics['best_performer']['symbol']} "
                  f"({perf_metrics['best_performer']['return_percent']:+.2f}%) "
                  f"[{perf_metrics['best_performer']['account']}]")
            print(f"  Worst Performer: {perf_metrics['worst_performer']['symbol']} "
                  f"({perf_metrics['worst_performer']['return_percent']:+.2f}%) "
                  f"[{perf_metrics['worst_performer']['account']}]")
            print(f"  Profitable Holdings: {perf_metrics['profitable_holdings']}")
            print(f"  Loss-making Holdings: {perf_metrics['loss_making_holdings']}")
            
            # Generate consolidated watchlists
            print("\n👀 Generating Consolidated Watchlists:")
            print("-" * 40)
            
            # Top gainers watchlist
            top_gainers = manager.generate_consolidated_watchlist("top_gainers", 10)
            print("\n🔥 Top 10 Gainers:")
            for _, stock in top_gainers.iterrows():
                print(f"  {stock['symbol']:15} {stock['return_percent']:+6.2f}% "
                      f"₹{stock['market_value']:10,.0f} [{stock['account_name']}]")
            
            # Top losers watchlist
            top_losers = manager.generate_consolidated_watchlist("top_losers", 10)
            print("\n📉 Top 10 Losers:")
            for _, stock in top_losers.iterrows():
                print(f"  {stock['symbol']:15} {stock['return_percent']:+6.2f}% "
                      f"₹{stock['market_value']:10,.0f} [{stock['account_name']}]")
            
            # Check for alerts
            alerts = manager.get_consolidated_alerts()
            if alerts:
                print(f"\n🚨 Portfolio Alerts ({len(alerts)}):")
                print("-" * 30)
                for alert in alerts:
                    print(f"  {alert['severity']}: {alert['message']}")
            else:
                print("\n✅ No portfolio alerts at this time.")
            
            # Export consolidated portfolio data
            print("\n💾 Exporting consolidated portfolio data...")
            export_file = manager.export_consolidated_portfolio("csv")
            if export_file:
                print(f"✅ Consolidated portfolio exported to: {export_file}")
            
            # Plot consolidated portfolio distribution
            print("\n📊 Generating consolidated portfolio charts...")
            try:
                manager.plot_consolidated_portfolio()
                print("✅ Charts generated successfully!")
            except Exception as e:
                print(f"⚠️  Chart generation failed: {str(e)}")
            
        else:
            print("❌ Failed to generate portfolio overview")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        # Cleanup
        try:
            if 'manager' in locals():
                manager.logout_all_accounts()
                print("\n🔒 Logged out from all accounts successfully")
        except:
            pass
        
        print("\n👋 Thank you for using TradeSight Multi-Broker!")

def demo_without_login():
    """Demo function that shows the structure without actual login"""
    print("🚀 TradeSight - Multi-Broker Portfolio Tracker (Demo Mode)")
    print("=" * 70)
    
    print("\n📁 Project Structure:")
    print("├── config.py                    # Multi-broker configuration")
    print("├── zerodha_client.py            # Zerodha API client")
    print("├── icici_client.py              # ICICI Direct API client")
    print("├── multi_broker_manager.py      # Multi-broker portfolio manager")
    print("├── multi_broker_example.py      # This demo script")
    print("├── requirements.txt             # Python dependencies")
    print("└── .env                        # Environment variables (create this)")
    
    print("\n🔧 Setup Instructions:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Create .env file with your broker credentials:")
    print("\n   # Zerodha Accounts (up to 4)")
    print("   ZERODHA_1_API_KEY=your_api_key_1")
    print("   ZERODHA_1_API_SECRET=your_api_secret_1")
    print("   ZERODHA_1_TOTP_SECRET=your_totp_secret_1")
    print("   ZERODHA_1_ACCOUNT_NAME=Zerodha Account 1")
    print("   ZERODHA_2_API_KEY=your_api_key_2")
    print("   ZERODHA_2_API_SECRET=your_api_secret_2")
    print("   ZERODHA_2_TOTP_SECRET=your_totp_secret_2")
    print("   ZERODHA_2_ACCOUNT_NAME=Zerodha Account 2")
    print("   # ... repeat for accounts 3 and 4")
    print("\n   # ICICI Direct Accounts (up to 2)")
    print("   ICICI_1_API_KEY=your_api_key_1")
    print("   ICICI_1_API_SECRET=your_api_secret_1")
    print("   ICICI_1_TOTP_SECRET=your_totp_secret_1")
    print("   ICICI_1_ACCOUNT_NAME=ICICI Account 1")
    print("   ICICI_2_API_KEY=your_api_key_2")
    print("   ICICI_2_API_SECRET=your_api_secret_2")
    print("   ICICI_2_TOTP_SECRET=your_totp_secret_2")
    print("   ICICI_2_ACCOUNT_NAME=ICICI Account 2")
    print("\n3. Run: python multi_broker_example.py")
    
    print("\n📊 Multi-Broker Features:")
    print("✅ Support for multiple Zerodha accounts (up to 4)")
    print("✅ Support for multiple ICICI Direct accounts (up to 2)")
    print("✅ Consolidated portfolio analysis across all accounts")
    print("✅ Broker-wise breakdown and comparison")
    print("✅ Account-wise performance tracking")
    print("✅ Unified watchlist generation")
    print("✅ Consolidated risk assessment")
    print("✅ Multi-account alerts and notifications")
    print("✅ Comprehensive data export")
    print("✅ Advanced portfolio visualization")
    
    print("\n🔐 Security Notes:")
    print("• Never commit .env file to version control")
    print("• Use environment variables for sensitive data")
    print("• Implement proper session management for each account")
    print("• Add rate limiting for API calls")
    print("• Secure credential storage")

if __name__ == "__main__":
    # Check if environment variables are set
    load_dotenv()
    
    # Check for any broker accounts
    from config import MultiBrokerConfig
    total_accounts = MultiBrokerConfig.get_total_accounts()
    
    if total_accounts > 0:
        print(f"🔑 Found {total_accounts} broker accounts in .env file")
        main()
    else:
        print("⚠️  No broker accounts found in .env file")
        demo_without_login() 