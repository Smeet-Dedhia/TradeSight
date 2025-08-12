#!/usr/bin/env python3
"""
Example usage of TradeSight Zerodha integration
This script demonstrates how to fetch portfolio data and perform analysis
"""

import os
from dotenv import load_dotenv
from zerodha_client import ZerodhaClient
from portfolio_manager import PortfolioManager

def main():
    """Main function demonstrating portfolio fetching and analysis"""
    
    # Load environment variables
    load_dotenv()
    
    print("🚀 TradeSight - Zerodha Portfolio Tracker")
    print("=" * 50)
    
    try:
        # Initialize Zerodha client
        print("📡 Initializing Zerodha client...")
        client = ZerodhaClient()
        
        # Get user credentials (in production, use secure input methods)
        print("\n🔐 Please provide your Zerodha credentials:")
        user_id = input("User ID: ").strip()
        password = input("Password: ").strip()
        pin = input("PIN: ").strip()
        
        # Login to Zerodha
        print("\n🔑 Logging in to Zerodha...")
        if client.login(user_id, password, pin):
            print("✅ Login successful!")
            
            # Initialize portfolio manager
            portfolio_mgr = PortfolioManager(client)
            
            # Get portfolio overview
            print("\n📊 Fetching portfolio data...")
            overview = portfolio_mgr.get_portfolio_overview()
            
            if overview:
                print("\n📈 Portfolio Overview:")
                print("-" * 30)
                
                summary = overview["summary"]
                print(f"Total Holdings: {summary['total_holdings']}")
                print(f"Total Investment: ₹{summary['total_investment']:,.2f}")
                print(f"Current Value: ₹{summary['total_market_value']:,.2f}")
                print(f"Total P&L: ₹{summary['total_pnl']:,.2f}")
                print(f"Total Return: {summary['total_return_percent']:.2f}%")
                
                # Display top holdings
                print("\n🏆 Top 5 Holdings:")
                print("-" * 20)
                for i, holding in enumerate(overview["top_holdings"], 1):
                    print(f"{i}. {holding['symbol']}: ₹{holding['market_value']:,.2f} ({holding['return_percent']:+.2f}%)")
                
                # Display risk metrics
                risk_metrics = overview["risk_metrics"]
                print(f"\n⚠️  Risk Metrics:")
                print(f"Portfolio Return: {risk_metrics['portfolio_return_percent']:.2f}%")
                print(f"Concentration Risk: {risk_metrics['concentration_risk']:.4f}")
                print(f"Max Single Holding: {risk_metrics['max_single_holding_weight']:.2f}%")
                print(f"Top 5 Holdings Weight: {risk_metrics['top_5_holdings_weight']:.2f}%")
                
                # Display performance metrics
                perf_metrics = overview["performance_metrics"]
                print(f"\n📊 Performance Metrics:")
                print(f"Weighted Average Return: {perf_metrics['weighted_average_return']:.2f}%")
                print(f"Best Performer: {perf_metrics['best_performer']['symbol']} ({perf_metrics['best_performer']['return_percent']:+.2f}%)")
                print(f"Worst Performer: {perf_metrics['worst_performer']['symbol']} ({perf_metrics['worst_performer']['return_percent']:+.2f}%)")
                print(f"Profitable Holdings: {perf_metrics['profitable_holdings']}")
                print(f"Loss-making Holdings: {perf_metrics['loss_making_holdings']}")
                
                # Generate watchlists
                print("\n👀 Generating Watchlists:")
                print("-" * 25)
                
                # Top gainers watchlist
                top_gainers = portfolio_mgr.generate_watchlist("top_gainers", 5)
                print("\n🔥 Top Gainers:")
                for _, stock in top_gainers.iterrows():
                    print(f"  {stock['symbol']}: {stock['return_percent']:+.2f}% (₹{stock['market_value']:,.2f})")
                
                # Top losers watchlist
                top_losers = portfolio_mgr.generate_watchlist("top_losers", 5)
                print("\n📉 Top Losers:")
                for _, stock in top_losers.iterrows():
                    print(f"  {stock['symbol']}: {stock['return_percent']:+.2f}% (₹{stock['market_value']:,.2f})")
                
                # Check for alerts
                alerts = portfolio_mgr.get_portfolio_alerts()
                if alerts:
                    print(f"\n🚨 Portfolio Alerts ({len(alerts)}):")
                    print("-" * 25)
                    for alert in alerts:
                        print(f"  {alert['severity']}: {alert['message']}")
                else:
                    print("\n✅ No portfolio alerts at this time.")
                
                # Export portfolio data
                print("\n💾 Exporting portfolio data...")
                export_file = portfolio_mgr.export_portfolio("csv")
                if export_file:
                    print(f"✅ Portfolio exported to: {export_file}")
                
                # Plot portfolio distribution
                print("\n📊 Generating portfolio charts...")
                try:
                    portfolio_mgr.plot_portfolio_distribution()
                    print("✅ Charts generated successfully!")
                except Exception as e:
                    print(f"⚠️  Chart generation failed: {str(e)}")
                
            else:
                print("❌ Failed to fetch portfolio data")
        
        else:
            print("❌ Login failed. Please check your credentials.")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        # Cleanup
        try:
            if 'client' in locals():
                client.logout()
                print("\n🔒 Logged out successfully")
        except:
            pass
        
        print("\n👋 Thank you for using TradeSight!")

def demo_without_login():
    """Demo function that shows the structure without actual login"""
    print("🚀 TradeSight - Zerodha Portfolio Tracker (Demo Mode)")
    print("=" * 60)
    
    print("\n📁 Project Structure:")
    print("├── config.py              # Configuration and environment variables")
    print("├── zerodha_client.py      # Zerodha API client")
    print("├── portfolio_manager.py   # Portfolio analysis and management")
    print("├── example_usage.py       # This demo script")
    print("├── requirements.txt       # Python dependencies")
    print("└── .env                  # Environment variables (create this)")
    
    print("\n🔧 Setup Instructions:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Create .env file with your Zerodha credentials:")
    print("   ZERODHA_API_KEY=your_api_key")
    print("   ZERODHA_API_SECRET=your_api_secret")
    print("   ZERODHA_TOTP_SECRET=your_totp_secret")
    print("3. Run: python example_usage.py")
    
    print("\n📊 Features:")
    print("✅ Fetch portfolio from Zerodha")
    print("✅ Portfolio analysis and metrics")
    print("✅ Risk assessment")
    print("✅ Performance tracking")
    print("✅ Watchlist generation")
    print("✅ Data export (CSV, Excel, JSON)")
    print("✅ Portfolio visualization")
    print("✅ Alert system")
    
    print("\n🔐 Security Notes:")
    print("• Never commit .env file to version control")
    print("• Use environment variables for sensitive data")
    print("• Implement proper session management")
    print("• Add rate limiting for API calls")

if __name__ == "__main__":
    # Check if environment variables are set
    load_dotenv()
    
    if os.getenv('ZERODHA_API_KEY') and os.getenv('ZERODHA_API_SECRET'):
        print("🔑 Credentials found in .env file")
        main()
    else:
        print("⚠️  No credentials found in .env file")
        demo_without_login() 