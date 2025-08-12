import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import MultiBrokerConfig, BrokerConfig
from zerodha_client import ZerodhaClient
from icici_client import ICICIClient


class MultiBrokerManager:
    """Manager for multiple broker accounts and portfolio analysis"""
    
    def __init__(self):
        """Initialize multi-broker manager"""
        self.broker_clients = {}
        self.consolidated_portfolio = None
        self.account_summaries = {}
        
    def initialize_brokers(self) -> bool:
        """Initialize all broker clients"""
        try:
            all_accounts = MultiBrokerConfig.get_all_accounts()
            
            # Initialize Zerodha clients
            for account_config in all_accounts["zerodha"]:
                client = ZerodhaClient(account_config)
                self.broker_clients[account_config.name] = {
                    "client": client,
                    "broker": "Zerodha",
                    "config": account_config
                }
            
            # Initialize ICICI Direct clients
            for account_config in all_accounts["icici"]:
                client = ICICIClient(account_config)
                self.broker_clients[account_config.name] = {
                    "client": client,
                    "broker": "ICICI Direct",
                    "config": account_config
                }
            
            print(f"✅ Initialized {len(self.broker_clients)} broker accounts")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing brokers: {str(e)}")
            return False
    
    def login_all_accounts(self, credentials: Dict[str, Dict]) -> Dict[str, bool]:
        """Login to all broker accounts"""
        login_results = {}
        
        for account_name, client_info in self.broker_clients.items():
            if account_name in credentials:
                creds = credentials[account_name]
                client = client_info["client"]
                
                print(f"🔐 Logging into {account_name}...")
                success = client.login(
                    creds["user_id"],
                    creds["password"],
                    creds["pin"]
                )
                
                login_results[account_name] = success
                if success:
                    print(f"✅ Successfully logged into {account_name}")
                else:
                    print(f"❌ Failed to login to {account_name}")
            else:
                print(f"⚠️  No credentials found for {account_name}")
                login_results[account_name] = False
        
        return login_results
    
    def fetch_all_portfolios(self) -> bool:
        """Fetch portfolio data from all accounts"""
        try:
            all_holdings = []
            all_summaries = []
            
            for account_name, client_info in self.broker_clients.items():
                client = client_info["client"]
                broker = client_info["broker"]
                
                print(f"📊 Fetching portfolio from {account_name}...")
                
                # Get portfolio holdings
                holdings_df = client.get_portfolio_as_dataframe()
                if holdings_df is not None and not holdings_df.empty:
                    all_holdings.append(holdings_df)
                    print(f"✅ Fetched {len(holdings_df)} holdings from {account_name}")
                else:
                    print(f"⚠️  No holdings found in {account_name}")
                
                # Get portfolio summary
                summary = client.get_portfolio_summary()
                if summary:
                    all_summaries.append(summary)
                    self.account_summaries[account_name] = summary
            
            # Consolidate all portfolios
            if all_holdings:
                self.consolidated_portfolio = pd.concat(all_holdings, ignore_index=True)
                print(f"✅ Consolidated portfolio: {len(self.consolidated_portfolio)} total holdings")
                return True
            else:
                print("❌ No portfolio data fetched from any account")
                return False
                
        except Exception as e:
            print(f"❌ Error fetching portfolios: {str(e)}")
            return False
    
    def get_consolidated_overview(self) -> Dict:
        """Get comprehensive overview of all portfolios"""
        if self.consolidated_portfolio is None:
            if not self.fetch_all_portfolios():
                return {}
        
        overview = {
            "total_accounts": len(self.broker_clients),
            "total_holdings": len(self.consolidated_portfolio),
            "account_summaries": self.account_summaries,
            "consolidated_summary": self._calculate_consolidated_summary(),
            "broker_breakdown": self._get_broker_breakdown(),
            "top_holdings": self.consolidated_portfolio.head(10).to_dict('records'),
            "risk_metrics": self._calculate_consolidated_risk_metrics(),
            "performance_metrics": self._calculate_consolidated_performance_metrics()
        }
        
        return overview
    
    def _calculate_consolidated_summary(self) -> Dict:
        """Calculate consolidated portfolio summary"""
        if self.consolidated_portfolio is None:
            return {}
        
        total_investment = self.consolidated_portfolio['investment_value'].sum()
        total_market_value = self.consolidated_portfolio['market_value'].sum()
        total_pnl = self.consolidated_portfolio['pnl'].sum()
        
        return {
            "total_investment": total_investment,
            "total_market_value": total_market_value,
            "total_pnl": total_pnl,
            "total_return_percent": (total_pnl / total_investment * 100) if total_investment > 0 else 0
        }
    
    def _get_broker_breakdown(self) -> Dict:
        """Get breakdown by broker"""
        if self.consolidated_portfolio is None:
            return {}
        
        broker_stats = {}
        for broker in self.consolidated_portfolio['broker'].unique():
            broker_data = self.consolidated_portfolio[self.consolidated_portfolio['broker'] == broker]
            broker_stats[broker] = {
                "holdings_count": len(broker_data),
                "total_value": broker_data['market_value'].sum(),
                "total_pnl": broker_data['pnl'].sum(),
                "avg_return": broker_data['return_percent'].mean()
            }
        
        return broker_stats
    
    def _calculate_consolidated_risk_metrics(self) -> Dict:
        """Calculate consolidated risk metrics"""
        if self.consolidated_portfolio is None:
            return {}
        
        # Calculate individual stock weights
        total_value = self.consolidated_portfolio['market_value'].sum()
        weights = self.consolidated_portfolio['market_value'] / total_value
        
        # Calculate portfolio volatility (simplified)
        returns = self.consolidated_portfolio['return_percent'] / 100
        portfolio_return = (weights * returns).sum()
        
        # Calculate concentration risk
        concentration_risk = (weights ** 2).sum()  # Herfindahl index
        
        return {
            "portfolio_return_percent": round(portfolio_return * 100, 2),
            "concentration_risk": round(concentration_risk, 4),
            "max_single_holding_weight": round(weights.max() * 100, 2),
            "top_10_holdings_weight": round(weights.head(10).sum() * 100, 2)
        }
    
    def _calculate_consolidated_performance_metrics(self) -> Dict:
        """Calculate consolidated performance metrics"""
        if self.consolidated_portfolio is None:
            return {}
        
        # Calculate various performance metrics
        total_investment = self.consolidated_portfolio['investment_value'].sum()
        total_market_value = self.consolidated_portfolio['market_value'].sum()
        total_pnl = self.consolidated_portfolio['pnl'].sum()
        
        # Calculate weighted average return
        weights = self.consolidated_portfolio['market_value'] / total_market_value
        weighted_return = (weights * self.consolidated_portfolio['return_percent']).sum()
        
        # Find best and worst performers
        best_performer = self.consolidated_portfolio.loc[self.consolidated_portfolio['return_percent'].idxmax()]
        worst_performer = self.consolidated_portfolio.loc[self.consolidated_portfolio['return_percent'].idxmin()]
        
        return {
            "total_return_percent": round((total_pnl / total_investment * 100), 2),
            "weighted_average_return": round(weighted_return, 2),
            "best_performer": {
                "symbol": best_performer['symbol'],
                "return_percent": round(best_performer['return_percent'], 2),
                "account": best_performer['account_name']
            },
            "worst_performer": {
                "symbol": worst_performer['symbol'],
                "return_percent": round(worst_performer['return_percent'], 2),
                "account": worst_performer['account_name']
            },
            "profitable_holdings": len(self.consolidated_portfolio[self.consolidated_portfolio['pnl'] > 0]),
            "loss_making_holdings": len(self.consolidated_portfolio[self.consolidated_portfolio['pnl'] < 0])
        }
    
    def generate_consolidated_watchlist(self, criteria: str = "top_gainers", limit: int = 15) -> pd.DataFrame:
        """Generate watchlist from all portfolios"""
        if self.consolidated_portfolio is None:
            if not self.fetch_all_portfolios():
                return pd.DataFrame()
        
        if criteria == "top_gainers":
            watchlist = self.consolidated_portfolio.nlargest(limit, 'return_percent')
        elif criteria == "top_losers":
            watchlist = self.consolidated_portfolio.nsmallest(limit, 'return_percent')
        elif criteria == "highest_value":
            watchlist = self.consolidated_portfolio.nlargest(limit, 'market_value')
        elif criteria == "highest_volume":
            watchlist = self.consolidated_portfolio.nlargest(limit, 'quantity')
        else:
            watchlist = self.consolidated_portfolio.head(limit)
        
        return watchlist[['symbol', 'quantity', 'average_price', 'last_price', 
                         'market_value', 'pnl', 'return_percent', 'account_name', 'broker']]
    
    def plot_consolidated_portfolio(self, save_path: str = None) -> None:
        """Plot consolidated portfolio analysis"""
        if self.consolidated_portfolio is None:
            if not self.fetch_all_portfolios():
                print("No portfolio data available for plotting")
                return
        
        # Create subplots
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('Multi-Broker Portfolio Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Holdings by Broker (Pie Chart)
        broker_values = self.consolidated_portfolio.groupby('broker')['market_value'].sum()
        axes[0, 0].pie(broker_values.values, labels=broker_values.index, autopct='%1.1f%%')
        axes[0, 0].set_title('Portfolio Allocation by Broker')
        
        # 2. Holdings by Account (Pie Chart)
        account_values = self.consolidated_portfolio.groupby('account_name')['market_value'].sum()
        top_accounts = account_values.nlargest(8)
        other_value = account_values.iloc[8:].sum() if len(account_values) > 8 else 0
        
        if other_value > 0:
            plot_data = pd.concat([top_accounts, pd.Series({'Others': other_value})])
        else:
            plot_data = top_accounts
        
        axes[0, 1].pie(plot_data.values, labels=plot_data.index, autopct='%1.1f%%')
        axes[0, 1].set_title('Portfolio Allocation by Account')
        
        # 3. Returns Distribution (Histogram)
        axes[0, 2].hist(self.consolidated_portfolio['return_percent'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 2].axvline(self.consolidated_portfolio['return_percent'].mean(), color='red', linestyle='--', 
                           label=f'Mean: {self.consolidated_portfolio["return_percent"].mean():.1f}%')
        axes[0, 2].set_title('Returns Distribution (All Accounts)')
        axes[0, 2].set_xlabel('Return (%)')
        axes[0, 2].set_ylabel('Frequency')
        axes[0, 2].legend()
        
        # 4. Market Value vs Returns (Scatter Plot)
        scatter = axes[1, 0].scatter(self.consolidated_portfolio['return_percent'], 
                                    self.consolidated_portfolio['market_value'], 
                                    alpha=0.6, s=50, 
                                    c=pd.Categorical(self.consolidated_portfolio['broker']).codes,
                                    cmap='Set1')
        axes[1, 0].set_xlabel('Return (%)')
        axes[1, 0].set_ylabel('Market Value (₹)')
        axes[1, 0].set_title('Market Value vs Returns (Colored by Broker)')
        
        # 5. Top Holdings by Value (Bar Chart)
        top_15 = self.consolidated_portfolio.head(15)
        axes[1, 1].barh(range(len(top_15)), top_15['market_value'])
        axes[1, 1].set_yticks(range(len(top_15)))
        axes[1, 1].set_yticklabels([f"{row['symbol']}\n({row['account_name']})" for _, row in top_15.iterrows()])
        axes[1, 1].set_xlabel('Market Value (₹)')
        axes[1, 1].set_title('Top 15 Holdings by Market Value')
        
        # 6. Account Performance Comparison
        account_performance = self.consolidated_portfolio.groupby('account_name').agg({
            'return_percent': 'mean',
            'market_value': 'sum'
        }).round(2)
        
        axes[1, 2].bar(range(len(account_performance)), account_performance['return_percent'])
        axes[1, 2].set_xticks(range(len(account_performance)))
        axes[1, 2].set_xticklabels(account_performance.index, rotation=45, ha='right')
        axes[1, 2].set_ylabel('Average Return (%)')
        axes[1, 2].set_title('Account Performance Comparison')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def export_consolidated_portfolio(self, format: str = "csv", filepath: str = None) -> str:
        """Export consolidated portfolio data"""
        if self.consolidated_portfolio is None:
            if not self.fetch_all_portfolios():
                return ""
        
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"consolidated_portfolio_{timestamp}.{format}"
        
        try:
            if format.lower() == "csv":
                self.consolidated_portfolio.to_csv(filepath, index=False)
            elif format.lower() == "excel":
                self.consolidated_portfolio.to_excel(filepath, index=False)
            elif format.lower() == "json":
                self.consolidated_portfolio.to_json(filepath, orient='records', indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            print(f"Consolidated portfolio exported to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error exporting consolidated portfolio: {str(e)}")
            return ""
    
    def get_consolidated_alerts(self) -> List[Dict]:
        """Get alerts from all portfolios"""
        alerts = []
        
        if self.consolidated_portfolio is None:
            if not self.fetch_all_portfolios():
                return alerts
        
        # Check for significant losses
        significant_losses = self.consolidated_portfolio[self.consolidated_portfolio['return_percent'] < -10]
        for _, holding in significant_losses.iterrows():
            alerts.append({
                "type": "LOSS_ALERT",
                "symbol": holding['symbol'],
                "account": holding['account_name'],
                "broker": holding['broker'],
                "message": f"{holding['symbol']} in {holding['account_name']} is down {abs(holding['return_percent']):.1f}%",
                "severity": "HIGH" if holding['return_percent'] < -20 else "MEDIUM"
            })
        
        # Check for concentration risk
        weights = self.consolidated_portfolio['market_value'] / self.consolidated_portfolio['market_value'].sum()
        if weights.max() > 0.15:  # More than 15% in single stock
            max_weight_stock = self.consolidated_portfolio.loc[weights.idxmax()]
            alerts.append({
                "type": "CONCENTRATION_ALERT",
                "symbol": max_weight_stock['symbol'],
                "account": max_weight_stock['account_name'],
                "broker": max_weight_stock['broker'],
                "message": f"{max_weight_stock['symbol']} represents {weights.max()*100:.1f}% of total portfolio",
                "severity": "MEDIUM"
            })
        
        return alerts
    
    def logout_all_accounts(self):
        """Logout from all broker accounts"""
        for account_name, client_info in self.broker_clients.items():
            try:
                client_info["client"].logout()
                print(f"🔒 Logged out from {account_name}")
            except Exception as e:
                print(f"⚠️  Error logging out from {account_name}: {str(e)}") 