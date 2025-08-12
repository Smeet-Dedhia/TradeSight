import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from zerodha_client import ZerodhaClient


class PortfolioManager:
    """High-level portfolio management and analysis"""
    
    def __init__(self, zerodha_client: ZerodhaClient):
        """Initialize portfolio manager with Zerodha client"""
        self.client = zerodha_client
        self.holdings_df = None
        self.summary = None
        
    def refresh_portfolio(self) -> bool:
        """Refresh portfolio data from Zerodha"""
        try:
            self.holdings_df = self.client.get_portfolio_as_dataframe()
            self.summary = self.client.get_portfolio_summary()
            
            if self.holdings_df is not None and self.summary is not None:
                return True
            return False
        except Exception as e:
            print(f"Error refreshing portfolio: {str(e)}")
            return False
    
    def get_portfolio_overview(self) -> Dict:
        """Get comprehensive portfolio overview"""
        if not self.refresh_portfolio():
            return {}
        
        overview = {
            "summary": self.summary,
            "holdings_count": len(self.holdings_df),
            "top_holdings": self.holdings_df.head(5).to_dict('records'),
            "sector_breakdown": self._get_sector_breakdown(),
            "risk_metrics": self._calculate_risk_metrics(),
            "performance_metrics": self._calculate_performance_metrics()
        }
        
        return overview
    
    def _get_sector_breakdown(self) -> Dict:
        """Get sector-wise breakdown of portfolio"""
        # This would require additional data from Zerodha API
        # For now, returning a placeholder
        return {
            "note": "Sector breakdown requires additional API calls to get instrument details"
        }
    
    def _calculate_risk_metrics(self) -> Dict:
        """Calculate portfolio risk metrics"""
        if self.holdings_df is None or len(self.holdings_df) == 0:
            return {}
        
        # Calculate individual stock weights
        total_value = self.holdings_df['market_value'].sum()
        weights = self.holdings_df['market_value'] / total_value
        
        # Calculate portfolio volatility (simplified)
        returns = self.holdings_df['return_percent'] / 100
        portfolio_return = (weights * returns).sum()
        
        # Calculate concentration risk
        concentration_risk = (weights ** 2).sum()  # Herfindahl index
        
        return {
            "portfolio_return_percent": round(portfolio_return * 100, 2),
            "concentration_risk": round(concentration_risk, 4),
            "max_single_holding_weight": round(weights.max() * 100, 2),
            "top_5_holdings_weight": round(weights.head(5).sum() * 100, 2)
        }
    
    def _calculate_performance_metrics(self) -> Dict:
        """Calculate portfolio performance metrics"""
        if self.holdings_df is None or len(self.holdings_df) == 0:
            return {}
        
        # Calculate various performance metrics
        total_investment = self.holdings_df['investment_value'].sum()
        total_market_value = self.holdings_df['market_value'].sum()
        total_pnl = self.holdings_df['pnl'].sum()
        
        # Calculate weighted average return
        weights = self.holdings_df['market_value'] / total_market_value
        weighted_return = (weights * self.holdings_df['return_percent']).sum()
        
        # Find best and worst performers
        best_performer = self.holdings_df.loc[self.holdings_df['return_percent'].idxmax()]
        worst_performer = self.holdings_df.loc[self.holdings_df['return_percent'].idxmin()]
        
        return {
            "total_return_percent": round((total_pnl / total_investment * 100), 2),
            "weighted_average_return": round(weighted_return, 2),
            "best_performer": {
                "symbol": best_performer['symbol'],
                "return_percent": round(best_performer['return_percent'], 2)
            },
            "worst_performer": {
                "symbol": worst_performer['symbol'],
                "return_percent": round(worst_performer['return_percent'], 2)
            },
            "profitable_holdings": len(self.holdings_df[self.holdings_df['pnl'] > 0]),
            "loss_making_holdings": len(self.holdings_df[self.holdings_df['pnl'] < 0])
        }
    
    def generate_watchlist(self, criteria: str = "top_gainers", limit: int = 10) -> pd.DataFrame:
        """Generate watchlist based on specified criteria"""
        if not self.refresh_portfolio():
            return pd.DataFrame()
        
        if criteria == "top_gainers":
            watchlist = self.holdings_df.nlargest(limit, 'return_percent')
        elif criteria == "top_losers":
            watchlist = self.holdings_df.nsmallest(limit, 'return_percent')
        elif criteria == "highest_value":
            watchlist = self.holdings_df.nlargest(limit, 'market_value')
        elif criteria == "highest_volume":
            # This would require additional data from Zerodha
            watchlist = self.holdings_df.nlargest(limit, 'quantity')
        else:
            watchlist = self.holdings_df.head(limit)
        
        return watchlist[['symbol', 'quantity', 'average_price', 'last_price', 
                         'market_value', 'pnl', 'return_percent']]
    
    def plot_portfolio_distribution(self, save_path: str = None) -> None:
        """Plot portfolio distribution charts"""
        if not self.refresh_portfolio():
            print("No portfolio data available for plotting")
            return
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Portfolio Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Holdings by Market Value (Pie Chart)
        top_holdings = self.holdings_df.head(8)
        other_value = self.holdings_df.iloc[8:]['market_value'].sum() if len(self.holdings_df) > 8 else 0
        
        if other_value > 0:
            plot_data = pd.concat([top_holdings, pd.DataFrame({
                'symbol': ['Others'],
                'market_value': [other_value]
            })])
        else:
            plot_data = top_holdings
        
        axes[0, 0].pie(plot_data['market_value'], labels=plot_data['symbol'], autopct='%1.1f%%')
        axes[0, 0].set_title('Portfolio Allocation (Top Holdings)')
        
        # 2. Returns Distribution (Histogram)
        axes[0, 1].hist(self.holdings_df['return_percent'], bins=15, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 1].axvline(self.holdings_df['return_percent'].mean(), color='red', linestyle='--', 
                           label=f'Mean: {self.holdings_df["return_percent"].mean():.1f}%')
        axes[0, 1].set_title('Returns Distribution')
        axes[0, 1].set_xlabel('Return (%)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].legend()
        
        # 3. Market Value vs Returns (Scatter Plot)
        axes[1, 0].scatter(self.holdings_df['return_percent'], self.holdings_df['market_value'], 
                           alpha=0.6, s=50)
        axes[1, 0].set_xlabel('Return (%)')
        axes[1, 0].set_ylabel('Market Value (₹)')
        axes[1, 0].set_title('Market Value vs Returns')
        
        # 4. Top 10 Holdings by Value (Bar Chart)
        top_10 = self.holdings_df.head(10)
        axes[1, 1].barh(range(len(top_10)), top_10['market_value'])
        axes[1, 1].set_yticks(range(len(top_10)))
        axes[1, 1].set_yticklabels(top_10['symbol'])
        axes[1, 1].set_xlabel('Market Value (₹)')
        axes[1, 1].set_title('Top 10 Holdings by Market Value')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def export_portfolio(self, format: str = "csv", filepath: str = None) -> str:
        """Export portfolio data to file"""
        if not self.refresh_portfolio():
            return ""
        
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"portfolio_export_{timestamp}.{format}"
        
        try:
            if format.lower() == "csv":
                self.holdings_df.to_csv(filepath, index=False)
            elif format.lower() == "excel":
                self.holdings_df.to_excel(filepath, index=False)
            elif format.lower() == "json":
                self.holdings_df.to_json(filepath, orient='records', indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            print(f"Portfolio exported to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error exporting portfolio: {str(e)}")
            return ""
    
    def get_portfolio_alerts(self) -> List[Dict]:
        """Get portfolio alerts and notifications"""
        alerts = []
        
        if not self.refresh_portfolio():
            return alerts
        
        # Check for significant losses
        significant_losses = self.holdings_df[self.holdings_df['return_percent'] < -10]
        for _, holding in significant_losses.iterrows():
            alerts.append({
                "type": "LOSS_ALERT",
                "symbol": holding['symbol'],
                "message": f"{holding['symbol']} is down {abs(holding['return_percent']):.1f}%",
                "severity": "HIGH" if holding['return_percent'] < -20 else "MEDIUM"
            })
        
        # Check for concentration risk
        weights = self.holdings_df['market_value'] / self.holdings_df['market_value'].sum()
        if weights.max() > 0.2:  # More than 20% in single stock
            max_weight_stock = self.holdings_df.loc[weights.idxmax()]
            alerts.append({
                "type": "CONCENTRATION_ALERT",
                "symbol": max_weight_stock['symbol'],
                "message": f"{max_weight_stock['symbol']} represents {weights.max()*100:.1f}% of portfolio",
                "severity": "MEDIUM"
            })
        
        return alerts 