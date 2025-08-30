import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# Set page title
st.set_page_config(page_title="Family Portfolio Dashboard", layout="wide")
st.title("Family Portfolio Dashboard")

# Helper function for Indian number formatting (lakhs/crores)
def format_indian_currency(amount):
    """Format amount in Indian style (lakhs/crores)"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f} L"
    else:
        return f"₹{amount:,.2f}"

# Load the CSV file
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data/consolidated_holdings/latest.csv")
        return df
    except FileNotFoundError:
        st.error("Error: Could not find the CSV file at data/consolidated_holdings/latest.csv")
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Aggregate data across accounts
@st.cache_data
def aggregate_portfolio(df):
    # Group by Symbol and exchange
    grouped = df.groupby(['Symbol', 'exchange']).agg({
        'quantity': 'sum',
        'investment_value': 'sum',
        'market_value': 'sum'
    }).reset_index()
    
    # Calculate weighted average price
    weighted_avg_price = df.groupby(['Symbol', 'exchange']).apply(
        lambda x: (x['quantity'] * x['average_price']).sum() / x['quantity'].sum()
    ).reset_index(name='average_price')
    
    # Merge the weighted average price back
    aggregated_df = grouped.merge(weighted_avg_price, on=['Symbol', 'exchange'])
    
    # Calculate P&L directly from aggregated values
    aggregated_df['profit_loss'] = aggregated_df['market_value'] - aggregated_df['investment_value']
    
    # Calculate return percentage
    aggregated_df['return_percent'] = (
        (aggregated_df['market_value'] - aggregated_df['investment_value']) / 
        aggregated_df['investment_value'] * 100
    )
    
    # Round numeric columns for better display
    numeric_columns = ['quantity', 'investment_value', 'market_value', 'profit_loss', 'average_price', 'return_percent']
    for col in numeric_columns:
        if col in aggregated_df.columns:
            if col in ['quantity']:
                aggregated_df[col] = aggregated_df[col].round(0).astype(int)
            elif col in ['return_percent']:
                aggregated_df[col] = aggregated_df[col].round(2)
            else:
                aggregated_df[col] = aggregated_df[col].round(2)
    
    return aggregated_df

# Load the data
df = load_data()

if df is not None:
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Multiselect for accounts
    all_accounts = sorted(df['account_name'].unique())
    selected_accounts = st.sidebar.multiselect(
        "Select Accounts:",
        options=all_accounts,
        default=all_accounts,
        help="Choose which accounts to include in the analysis"
    )
    
    # Multiselect for exchange
    all_exchanges = sorted(df['exchange'].unique())
    selected_exchanges = st.sidebar.multiselect(
        "Select Exchanges:",
        options=all_exchanges,
        default=all_exchanges,
        help="Choose which exchanges to include in the analysis"
    )
    
    # Slider for return_percent range
    min_return = df['return_percent'].min()
    max_return = df['return_percent'].max()
    
    # Handle infinite values
    if np.isinf(min_return) or np.isinf(max_return):
        # Filter out infinite values for the slider
        finite_returns = df[~np.isinf(df['return_percent'])]['return_percent']
        if not finite_returns.empty:
            min_return = finite_returns.min()
            max_return = finite_returns.max()
        else:
            min_return, max_return = -100, 100
    
    return_range = st.sidebar.slider(
        "Return % Range:",
        min_value=float(min_return),
        max_value=float(max_return),
        value=(float(min_return), float(max_return)),
        step=0.1,
        help="Filter stocks by return percentage range"
    )
    
    # Apply filters to the data
    filtered_df = df[
        (df['account_name'].isin(selected_accounts)) &
        (df['exchange'].isin(selected_exchanges)) &
        (df['return_percent'] >= return_range[0]) &
        (df['return_percent'] <= return_range[1])
    ].copy()
    
    # Aggregate the filtered portfolio
    aggregated_df = aggregate_portfolio(filtered_df)
    
    # Show filter summary
    st.sidebar.write(f"**Filtered Results:**")
    st.sidebar.write(f"Accounts: {len(selected_accounts)}")
    st.sidebar.write(f"Exchanges: {len(selected_exchanges)}")
    st.sidebar.write(f"Return Range: {return_range[0]:.1f}% to {return_range[1]:.1f}%")
    st.sidebar.write(f"Stocks: {len(aggregated_df)}")
    
    # Portfolio Allocation by Account (moved from main dashboard)
    # st.sidebar.write("**Portfolio Allocation by Account**")
    
    # Group by account_name and sum market_value (using filtered data)
    account_allocation = filtered_df.groupby('account_name')['market_value'].sum().reset_index()
    
    fig_account = px.pie(
        account_allocation,
        values='market_value',
        names='account_name',
        title='Account Allocation (Market Value)'
    )
    fig_account.update_traces(textposition='inside', textinfo='percent+label')
    
    # Make the chart smaller to fit in sidebar
    fig_account.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    st.sidebar.plotly_chart(fig_account, use_container_width=True)
    
    st.header("Portfolio Summary")
    st.write(f"**Total unique stocks:** {len(aggregated_df)}")
    
    # Portfolio summary statistics at the top
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_investment = aggregated_df['investment_value'].sum()
        st.metric("Total Investment", format_indian_currency(total_investment))
    
    with col2:
        total_market_value = aggregated_df['market_value'].sum()
        st.metric("Total Market Value", format_indian_currency(total_market_value))
    
    with col3:
        total_pnl = aggregated_df['profit_loss'].sum()
        st.metric("Total P&L", format_indian_currency(total_pnl))
    
    with col4:
        overall_return = ((total_market_value - total_investment) / total_investment * 100) if total_investment > 0 else 0
        st.metric("Overall Return %", f"{overall_return:.2f}%")
    
    # Display the aggregated portfolio table
    st.header("Holdings")
    st.dataframe(aggregated_df, width='stretch')
    
    # Interactive stock breakdown section
    st.header("Stock Breakdown")
    
    # Create selectbox for stock selection
    stock_options = aggregated_df['Symbol'].unique()
    selected_stock = st.selectbox(
        "Select a stock to view breakdown by account:",
        options=stock_options,
        index=0 if len(stock_options) > 0 else None
    )
    
    if selected_stock:
        # Filter filtered data for selected stock
        stock_breakdown = filtered_df[filtered_df['Symbol'] == selected_stock].copy()
        
        if not stock_breakdown.empty:
            # Calculate return percentage for each account
            stock_breakdown['return_percent'] = (
                (stock_breakdown['market_value'] - stock_breakdown['investment_value']) / 
                stock_breakdown['investment_value'] * 100
            )
            
            # Round numeric columns for better display
            numeric_cols = ['quantity', 'average_price', 'investment_value', 'market_value', 'profit_loss', 'return_percent']
            for col in numeric_cols:
                if col in stock_breakdown.columns:
                    if col == 'quantity':
                        stock_breakdown[col] = stock_breakdown[col].round(0).astype(int)
                    elif col == 'return_percent':
                        stock_breakdown[col] = stock_breakdown[col].round(2)
                    else:
                        stock_breakdown[col] = stock_breakdown[col].round(2)
            
            # Select and reorder columns for display
            display_columns = ['account_name', 'quantity', 'average_price', 'investment_value', 'market_value', 'profit_loss', 'return_percent']
            display_df = stock_breakdown[display_columns]
            
            # Display the breakdown table
            st.write(f"**Breakdown for {selected_stock}**")
            st.dataframe(display_df, width='stretch')
            
            # Show summary for selected stock
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                total_qty = stock_breakdown['quantity'].sum()
                st.metric("Total Quantity", f"{total_qty:,}")
            
            with col2:
                total_inv = stock_breakdown['investment_value'].sum()
                st.metric("Total Investment", format_indian_currency(total_inv))
            
            with col3:
                total_mv = stock_breakdown['market_value'].sum()
                st.metric("Total Market Value", format_indian_currency(total_mv))
            
            with col4:
                total_pl = stock_breakdown['profit_loss'].sum()
                st.metric("Total P&L", format_indian_currency(total_pl))
            
            with col5:
                # Calculate weighted average return percentage
                weighted_return = (
                    (stock_breakdown['return_percent'] * stock_breakdown['investment_value']).sum() / 
                    stock_breakdown['investment_value'].sum()
                )
                st.metric("Avg Return %", f"{weighted_return:.2f}%")
        else:
            st.warning(f"No data found for {selected_stock}")
    
        # Top & Bottom Performers Analysis
    st.header("Top & Bottom Performers")
    
    # User input for number of stocks to display
    max_stocks = len(aggregated_df)
    num_stocks = st.slider(
        "Number of stocks to display:",
        min_value=5,
        max_value=min(max_stocks, 50),  # Cap at 50 for performance
        value=10,
        step=5,
        help="Choose how many top and bottom performers to display in the charts"
    )
     
    # Bar chart of top N performers by return percentage
    # st.write("**Top Performers by Return %**")
    
    top_performers = aggregated_df.nlargest(num_stocks, 'return_percent')
    
    fig_top_performers = px.bar(
        top_performers,
        x='Symbol',
        y='return_percent',
        color='return_percent',
        color_continuous_scale='greens',
        title=f'Top {num_stocks} Performers by Return %',
        labels={'return_percent': 'Return %', 'Symbol': 'Stock Symbol'}
    )
    
    fig_top_performers.update_layout(
        xaxis_title="Stock Symbol",
        yaxis_title="Return %",
        xaxis_tickangle=-45,
        showlegend=False
    )
    
    st.plotly_chart(fig_top_performers, use_container_width=True)
    
    # Bar chart of bottom N performers by return percentage
    # st.write("**Bottom Performers by Return %**")
    
    bottom_performers = aggregated_df.nsmallest(num_stocks, 'return_percent')
    
    fig_bottom_performers = px.bar(
        bottom_performers,
        x='Symbol',
        y='return_percent',
        color='return_percent',
        color_continuous_scale='reds',
        title=f'Bottom {num_stocks} Performers by Return %',
        labels={'return_percent': 'Return %', 'Symbol': 'Stock Symbol'}
    )
    
    fig_bottom_performers.update_layout(
        xaxis_title="Stock Symbol",
        yaxis_title="Return %",
        xaxis_tickangle=-45,
        showlegend=False
    )
    
    st.plotly_chart(fig_bottom_performers, use_container_width=True)
    
    # Charts section
    st.header("Visualizations")
    
    # 1. Pie chart of portfolio allocation by Symbol (based on market_value)
    col1, col2 = st.columns(2)
    
    with col1:
        # st.write("**Portfolio Allocation by Stock**")
        fig_symbol = px.pie(
            aggregated_df, 
            values='market_value', 
            names='Symbol',
            title='Portfolio Allocation by Stock (Market Value)'
        )
        fig_symbol.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_symbol, use_container_width=True)
    
    # 2. Concentration Analysis
    with col2:
        st.write("**Portfolio Concentration**")
        
        # Calculate concentration metrics
        largest_holding_pct = (aggregated_df['market_value'].max() / total_market_value * 100) if total_market_value > 0 else 0
        top_5_holdings_pct = (aggregated_df.nlargest(5, 'market_value')['market_value'].sum() / total_market_value * 100) if total_market_value > 0 else 0
        
        # Display concentration metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Largest Holding %", f"{largest_holding_pct:.2f}%")
        
        with col2:
            st.metric("Top 5 Holdings %", f"{top_5_holdings_pct:.2f}%")
        
        # Bar chart of top 10 holdings by market value
        #st.write("**Top 10 Holdings by Market Value**")
        top_10_holdings = aggregated_df.nlargest(10, 'market_value')
        
        fig_top_holdings = px.bar(
            top_10_holdings,
            x='Symbol',
            y='market_value',
            color='market_value',
            color_continuous_scale='viridis',
            title='Top 10 Holdings by Market Value',
            labels={'market_value': 'Market Value (₹)', 'Symbol': 'Stock Symbol'}
        )
        
        fig_top_holdings.update_layout(
            xaxis_title="Stock Symbol",
            yaxis_title="Market Value (₹)",
            xaxis_tickangle=-45,
            showlegend=False
        )
        
        st.plotly_chart(fig_top_holdings, use_container_width=True)
    
    # 3. Pie chart of portfolio allocation by account_name (market_value) - MOVED TO SIDEBAR
    # (Chart moved to sidebar below filters)
    
    # 4. Histogram of return_percent distribution
    # st.write("**Return Distribution Across Holdings**")
    
    # Calculate portfolio average return for the vertical line
    portfolio_avg_return = aggregated_df['return_percent'].mean()
    
         # Create histogram with 5% bins
     # Calculate the range and create bins of 5% each
    min_ret = aggregated_df['return_percent'].min()
    max_ret = aggregated_df['return_percent'].max()
    
    # Create bins with 5% intervals
    bin_size = 5.0
    bins = np.arange(min_ret - bin_size/2, max_ret + bin_size, bin_size)
    
    fig_hist = px.histogram(
        aggregated_df,
        x='return_percent',
        nbins=len(bins)-1,  # Number of bins based on 5% intervals
        title='Distribution of Returns Across Holdings (5% Bins)',
        labels={'return_percent': 'Return %', 'count': 'Number of Holdings'}
    )
    
    # Add borders to histogram bars for better visibility
    fig_hist.update_traces(
        marker=dict(
            line=dict(width=1, color='black')
        )
    )
    
    # Add vertical line for portfolio average return
    fig_hist.add_vline(
        x=portfolio_avg_return,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Portfolio Avg: {portfolio_avg_return:.2f}%",
        annotation_position="top right"
    )
    
    # Update layout for better readability with x-axis ticks every 10%
    fig_hist.update_layout(
        xaxis_title="Return %",
        yaxis_title="Number of Holdings",
        showlegend=False,
        xaxis=dict(
            tickmode='array',
            tickvals=np.arange(-60, 401, 20),  # Every 10% from -50% to 100%
            ticktext=[f"{x}%" for x in np.arange(-50, 401, 20)],
            tickangle=0
        )
    )
    
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # 5. Bubble scatter plot: investment_value vs return_percent
    # st.write("**Investment Value vs Return Analysis**")
    
    # Create bubble scatter plot
    fig_bubble = px.scatter(
        aggregated_df,
        x='investment_value',
        y='return_percent',
        size=abs(aggregated_df['profit_loss']),
        color=aggregated_df['profit_loss'].apply(lambda x: 'Profit' if x >= 0 else 'Loss'),
        hover_data=['Symbol', 'quantity', 'average_price', 'return_percent'],
        color_discrete_map={'Profit': 'green', 'Loss': 'red'},
        title='Investment Value vs Return %', # + '(Bubble Size = |Profit/Loss|, Color = Profit/Loss)',
        labels={
            'investment_value': 'Investment Value (₹)',
            'return_percent': 'Return %',
            'size': '|Profit/Loss| (₹)',
            'color': 'Profit/Loss'
        }
    )
    
    # Update layout for better readability
    fig_bubble.update_layout(
        xaxis_title="Investment Value (₹)",
        yaxis_title="Return %",
        showlegend=True,
        legend_title="Profit/Loss"
    )
    
    # Add a horizontal line at y=0 for reference
    fig_bubble.add_hline(
        y=0,
        line_dash="dash",
        line_color="black",
        annotation_text="Break-even Line",
        annotation_position="bottom right"
    )
    
    st.plotly_chart(fig_bubble, use_container_width=True)
    
    # Show original data in expandable section
    with st.expander("View Original Raw Data"):
        st.header("Raw Holdings Data")
        st.write(f"Dataset shape: {df.shape}")
        st.dataframe(df, width='stretch')
        
        st.header("Dataset Overview")
        st.write(f"Total records: {len(df)}")
        st.write(f"Columns: {list(df.columns)}")
        
        st.header("First 10 Rows")
        st.dataframe(df.head(10), width='stretch')
else:
    st.error("Failed to load data. Please check the file path and try again.")
