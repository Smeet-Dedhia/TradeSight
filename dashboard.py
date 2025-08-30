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
    
    # Charts section
    st.header("Visualizations")
    
    # 1. Pie chart of portfolio allocation by Symbol (based on market_value)
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Portfolio Allocation by Stock**")
        fig_symbol = px.pie(
            aggregated_df, 
            values='market_value', 
            names='Symbol',
            title='Portfolio Allocation by Stock (Market Value)'
        )
        fig_symbol.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_symbol, use_container_width=True)
    
    # 2. Bar chart of top 10 gainers/losers (sorted by profit_loss)
    with col2:
        st.write("**Top 10 Gainers/Losers**")
        # Sort by profit_loss and get top 10
        top_stocks = aggregated_df.nlargest(10, 'profit_loss')
        bottom_stocks = aggregated_df.nsmallest(10, 'profit_loss')
        
        # Combine and sort for display
        top_bottom = pd.concat([top_stocks, bottom_stocks]).drop_duplicates()
        top_bottom = top_bottom.sort_values('profit_loss', ascending=False)
        
        fig_pnl = px.bar(
            top_bottom,
            x='Symbol',
            y='profit_loss',
            color='profit_loss',
            color_continuous_scale=['red', 'yellow', 'green'],
            title='Top Gainers/Losers by P&L'
        )
        fig_pnl.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_pnl, use_container_width=True)
    
    # 3. Pie chart of portfolio allocation by account_name (market_value)
    st.write("**Portfolio Allocation by Account**")
    
    # Group by account_name and sum market_value (using filtered data)
    account_allocation = filtered_df.groupby('account_name')['market_value'].sum().reset_index()
    
    fig_account = px.pie(
        account_allocation,
        values='market_value',
        names='account_name',
        title='Portfolio Allocation by Account (Market Value)'
    )
    fig_account.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_account, use_container_width=True)
    
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
