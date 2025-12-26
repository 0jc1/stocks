import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="US Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache data for 5 minutes
def get_stock_data(ticker, period="1y"):
    """Fetch stock data using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        info = stock.info
        return hist, info
    except Exception as e:
        return None, None


def get_stock_object(ticker):
    """Get yfinance Ticker object (not cached as it's not serializable)"""
    try:
        return yf.Ticker(ticker)
    except Exception as e:
        return None


def format_number(num):
    """Format large numbers with K, M, B, T suffixes"""
    if num is None or pd.isna(num):
        return "N/A"
    
    num = float(num)
    if abs(num) >= 1e12:
        return f"${num/1e12:.2f}T"
    elif abs(num) >= 1e9:
        return f"${num/1e9:.2f}B"
    elif abs(num) >= 1e6:
        return f"${num/1e6:.2f}M"
    elif abs(num) >= 1e3:
        return f"${num/1e3:.2f}K"
    else:
        return f"${num:.2f}"


def format_percentage(value):
    """Format percentage values"""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"


def format_financial_number(num):
    """Format financial statement numbers in millions or billions"""
    if num is None or pd.isna(num):
        return "N/A"
    
    num = float(num)
    if abs(num) >= 1e9:
        return f"{num/1e9:.2f}B"
    elif abs(num) >= 1e6:
        return f"{num/1e6:.2f}M"
    elif abs(num) >= 1e3:
        return f"{num/1e3:.2f}K"
    else:
        return f"{num:.2f}"


def order_financial_statement(df, statement_type):
    """Order financial statement rows in standard accounting order"""
    if df is None or df.empty:
        return df
    
    # Define standard ordering for each statement type
    income_statement_order = [
        'Total Revenue', 'Revenue', 'Operating Revenue',
        'Cost Of Revenue', 'Gross Profit',
        'Operating Expense', 'Selling General And Administration', 'Research And Development',
        'Operating Income', 'EBITDA', 'EBIT',
        'Interest Expense', 'Interest Income', 'Other Income Expense',
        'Pretax Income', 'Income Before Tax', 'Tax Provision',
        'Net Income From Continuing Operations', 'Net Income',
        'Diluted EPS', 'Basic EPS',
        'Diluted Average Shares', 'Basic Average Shares'
    ]
    
    balance_sheet_order = [
        # Assets
        'Total Assets', 'Current Assets',
        'Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments',
        'Receivables', 'Accounts Receivable', 'Inventory', 'Other Current Assets',
        'Total Non Current Assets', 'Net PPE', 'Gross PPE', 'Properties',
        'Goodwill', 'Other Intangible Assets', 'Investments And Advances',
        # Liabilities
        'Total Liabilities Net Minority Interest',
        'Current Liabilities', 'Accounts Payable', 'Current Debt',
        'Other Current Liabilities',
        'Total Non Current Liabilities Net Minority Interest',
        'Long Term Debt', 'Other Non Current Liabilities',
        # Equity
        'Stockholders Equity', 'Total Equity Gross Minority Interest',
        'Common Stock', 'Retained Earnings', 'Treasury Stock',
        'Total Capitalization', 'Share Issued'
    ]
    
    cash_flow_order = [
        # Operating Activities
        'Operating Cash Flow', 'Cash Flow From Continuing Operating Activities',
        'Net Income From Continuing Operations', 'Depreciation And Amortization',
        'Deferred Tax', 'Stock Based Compensation',
        'Change In Working Capital', 'Change In Receivables', 'Change In Inventory',
        'Change In Payables And Accrued Expense',
        # Investing Activities
        'Investing Cash Flow', 'Cash Flow From Continuing Investing Activities',
        'Net PPE Purchase And Sale', 'Purchase Of PPE',
        'Net Investment Purchase And Sale', 'Purchase Of Investment',
        'Sale Of Investment',
        # Financing Activities
        'Financing Cash Flow', 'Cash Flow From Continuing Financing Activities',
        'Net Issuance Payments Of Debt', 'Net Long Term Debt Issuance',
        'Net Short Term Debt Issuance', 'Repurchase Of Capital Stock',
        'Common Stock Dividend Paid',
        # Summary
        'End Cash Position', 'Beginning Cash Position',
        'Free Cash Flow'
    ]
    
    # Select the appropriate order based on statement type
    if statement_type == 'income':
        order = income_statement_order
    elif statement_type == 'balance':
        order = balance_sheet_order
    elif statement_type == 'cashflow':
        order = cash_flow_order
    else:
        return df
    
    # Get the current index values
    current_indices = df.index.tolist()
    
    # Create ordered index list
    ordered_indices = []
    for item in order:
        if item in current_indices:
            ordered_indices.append(item)
    
    # Add any remaining items not in our predefined order
    for item in current_indices:
        if item not in ordered_indices:
            ordered_indices.append(item)
    
    # Reorder the dataframe
    return df.reindex(ordered_indices)


def format_financial_dataframe(df, statement_type=None):
    """Format financial dataframe to show numbers in millions/billions and order rows"""
    if df is None or df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    df_formatted = df.copy()
    
    # Order the statement first if type is provided
    if statement_type:
        df_formatted = order_financial_statement(df_formatted, statement_type)
    
    # Apply formatting to all numeric values
    for col in df_formatted.columns:
        df_formatted[col] = df_formatted[col].apply(lambda x: format_financial_number(x) if pd.notna(x) and isinstance(x, (int, float)) else x)
    
    return df_formatted


def create_price_chart(hist_data, ticker):
    """Create an interactive price and volume chart"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'{ticker} Stock Price', 'Volume'),
        row_width=[0.2, 0.7]
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=hist_data.index,
            open=hist_data['Open'],
            high=hist_data['High'],
            low=hist_data['Low'],
            close=hist_data['Close'],
            name='Price'
        ),
        row=1, col=1
    )
    
    # Volume bar chart
    colors = ['red' if row['Close'] < row['Open'] else 'green' 
              for _, row in hist_data.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=hist_data.index,
            y=hist_data['Volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=700,
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        template='plotly_white'
    )
    
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    
    return fig


def display_key_metrics(info):
    """Display key stock metrics in columns"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        market_cap = format_number(info.get('marketCap'))
        st.metric("Market Cap", market_cap)
    
    with col2:
        st.metric(
            "Day Range",
            f"${info.get('dayLow', 'N/A')} - ${info.get('dayHigh', 'N/A')}"
        )

        week_52_low = info.get('fiftyTwoWeekLow', 'N/A')
        week_52_high = info.get('fiftyTwoWeekHigh', 'N/A')
        st.metric("52 Week Range", f"${week_52_low} - ${week_52_high}")
    
    
    with col3:
        avg_volume = info.get('averageVolume')
        st.metric("Avg Volume", format_number(avg_volume))

        pe_ratio = info.get('trailingPE', 'N/A')
        if pe_ratio and pe_ratio != 'N/A':
            pe_ratio = f"{pe_ratio:.2f}"
        st.metric("P/E Ratio", pe_ratio)
    
    with col4:
        div_yield = info.get('dividendYield')
        if div_yield:
            # dividendYield from yfinance appears to be in percentage form already
            div_yield = f"{div_yield:.2f}%"
        else:
            div_yield = "N/A"
        st.metric("Dividend Yield", div_yield)
        
        beta = info.get('beta', 'N/A')
        if beta and beta != 'N/A':
            beta = f"{beta:.2f}"
        st.metric("Beta", beta)

    with col5:
        # Forward PE
        forward_pe = info.get('forwardPE', 'N/A')
        if forward_pe and forward_pe != 'N/A':
            forward_pe = f"{forward_pe:.2f}"
        st.metric(f"Forward P/E", forward_pe)
        
        # PEG Ratio
        peg = info.get('pegRatio', 'N/A')
        if peg and peg != 'N/A':
            peg = f"{peg:.2f}"
        st.metric(f"PEG Ratio:", peg)


def display_company_info(info):
    """Display company information"""
    st.subheader("Company Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Company Name:** {info.get('longName', 'N/A')}")
        st.write(f"**Sector:** {info.get('sector', 'N/A')}")
        st.write(f"**Industry:** {info.get('industry', 'N/A')}")
        st.write(f"**Country:** {info.get('country', 'N/A')}")
        st.write(f"**Website:** {info.get('website', 'N/A')}")
    
    with col2:
        st.write(f"**Full Time Employees:** {info.get('fullTimeEmployees', 'N/A'):,}" if info.get('fullTimeEmployees') else "**Full Time Employees:** N/A")
        st.write(f"**Exchange:** {info.get('exchange', 'N/A')}")
        st.write(f"**Currency:** {info.get('currency', 'N/A')}")
    
    # Business Summary
    if info.get('longBusinessSummary'):
        st.write("**Business Summary:**")
        st.write(info.get('longBusinessSummary'))


def display_financial_highlights(info):
    """Display financial highlights"""
    st.subheader("Financial Highlights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Profitability**")
        profit_margin = info.get('profitMargins')
        if profit_margin:
            st.write(f"Profit Margin: {format_percentage(profit_margin * 100)}")
        else:
            st.write("Profit Margin: N/A")
        
        operating_margin = info.get('operatingMargins')
        if operating_margin:
            st.write(f"Operating Margin: {format_percentage(operating_margin * 100)}")
        else:
            st.write("Operating Margin: N/A")
    
    with col2:
        st.write("**Valuation**")
        st.write(f"Enterprise Value: {format_number(info.get('enterpriseValue'))}")
        
        price_to_book = info.get('priceToBook', 'N/A')
        if price_to_book and price_to_book != 'N/A':
            price_to_book = f"{price_to_book:.2f}"
        st.write(f"Price to Book: {price_to_book}")
    
    with col3:
        st.write("**Growth**")
        revenue_growth = info.get('revenueGrowth')
        if revenue_growth:
            st.write(f"Revenue Growth: {format_percentage(revenue_growth * 100)}")
        else:
            st.write("Revenue Growth: N/A")
        
        earnings_growth = info.get('earningsGrowth')
        if earnings_growth:
            st.write(f"Earnings Growth: {format_percentage(earnings_growth * 100)}")
        else:
            st.write("Earnings Growth: N/A")


def display_additional_data(stock, ticker):
    """Display additional data in tabs"""
    tab1, tab2, tab3 = st.tabs(["📊 Statistics", "📰 News", "💰 Financials"])
    
    with tab1:
        st.subheader("Key Statistics")
        info = stock.info
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Trading Information**")
            st.write(f"Previous Close: ${info.get('previousClose', 'N/A')}")
            st.write(f"Open: ${info.get('open', 'N/A')}")
            st.write(f"Bid: {info.get('bid', 'N/A')} x {info.get('bidSize', 'N/A')}")
            st.write(f"Ask: {info.get('ask', 'N/A')} x {info.get('askSize', 'N/A')}")
            st.write(f"Volume: {format_number(info.get('volume', 'N/A'))}" if info.get('volume') else "Volume: N/A")
        
        with col2:
            st.write("**Stock Price Info**")
            st.write(f"Regular Market Volume: {format_number(info.get('regularMarketVolume', 'N/A'))}" if info.get('regularMarketVolume') else "Regular Market Volume: N/A")
            st.write(f"Average Volume (10d): {format_number(info.get('averageVolume10days', 'N/A'))}" if info.get('averageVolume10days') else "Average Volume (10d): N/A")
            st.write(f"Shares Outstanding: {info.get('sharesOutstanding'):,}")
            st.write(f"Float Shares: {info.get('floatShares'):,}")
    
    with tab2:
        st.subheader("Recent News")
        try:
            news = stock.news
            if news:
                for article in news[:10]:  # Show top 10 news items
                    with st.expander(f"📰 {article.get('title', 'No title')}"):
                        st.write(f"**Publisher:** {article.get('publisher', 'Unknown')}")
                        if article.get('link'):
                            st.write(f"**Link:** {article.get('link')}")
                        if article.get('providerPublishTime'):
                            pub_time = datetime.fromtimestamp(article.get('providerPublishTime'))
                            st.write(f"**Published:** {pub_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.info("No recent news available for this stock.")
        except:
            st.info("News data not available.")
    
    with tab3:
        st.subheader("Financial Statements")
        st.caption("All values shown in Millions (M) or Billions (B)")
        
        fin_tab1, fin_tab2, fin_tab3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
        
        with fin_tab1:
            try:
                income_stmt = stock.financials
                if income_stmt is not None and not income_stmt.empty:
                    formatted_income = format_financial_dataframe(income_stmt, statement_type='income')
                    st.dataframe(formatted_income, use_container_width=True)
                else:
                    st.info("Income statement data not available.")
            except Exception as e:
                st.info("Income statement data not available.")
        
        with fin_tab2:
            try:
                balance_sheet = stock.balance_sheet
                if balance_sheet is not None and not balance_sheet.empty:
                    formatted_balance = format_financial_dataframe(balance_sheet, statement_type='balance')
                    st.dataframe(formatted_balance, use_container_width=True)
                else:
                    st.info("Balance sheet data not available.")
            except Exception as e:
                st.info("Balance sheet data not available.")
        
        with fin_tab3:
            try:
                cashflow = stock.cashflow
                if cashflow is not None and not cashflow.empty:
                    formatted_cashflow = format_financial_dataframe(cashflow, statement_type='cashflow')
                    st.dataframe(formatted_cashflow, use_container_width=True)
                else:
                    st.info("Cash flow data not available.")
            except Exception as e:
                st.info("Cash flow data not available.")


def main():
    # Initialize session state
    if 'current_ticker' not in st.session_state:
        st.session_state.current_ticker = "AAPL"
    
    # Header
    st.markdown('<h1 class="main-header">📈 US Stock Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("Search Settings")
        
        # Stock ticker input
        ticker_input = st.text_input(
            "Enter Stock Ticker",
            value=st.session_state.current_ticker,
            help="Enter a valid US stock ticker (e.g., AAPL, MSFT, GOOGL)"
        ).upper()
        
        # Search button
        search_button = st.button("Search", type="primary", use_container_width=True)
        
        # Update current ticker when search is clicked
        if search_button:
            st.session_state.current_ticker = ticker_input
        
        st.markdown("---")
        
        # Popular stocks quick access
        st.subheader("Popular Stocks")
        popular_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "WMT"]
        
        cols = st.columns(2)
        for idx, stock in enumerate(popular_stocks):
            col = cols[idx % 2]
            if col.button(stock, use_container_width=True):
                st.session_state.current_ticker = stock
                st.rerun()
        
        st.markdown("---")
        
        # Time period selection (moved below stock selection for better UX)
        if st.session_state.current_ticker:
            st.subheader("Time Period")
            period_options = {
                "1 Week": "1wk",
                "1 Month": "1mo",
                "3 Months": "3mo",
                "6 Months": "6mo",
                "1 Year": "1y",
                "2 Years": "2y",
                "5 Years": "5y",
                "Max": "max"
            }
            
            selected_period = st.selectbox(
                "Select Time Period",
                options=list(period_options.keys()),
                index=4,  # Default to 1 Year
                key="period_selector"
            )
            
            period = period_options[selected_period]
    
    # Main content - use session state ticker
    ticker_to_display = st.session_state.current_ticker
    
    if ticker_to_display:
        with st.spinner(f"Loading data for {ticker_to_display}..."):
            hist_data, info = get_stock_data(ticker_to_display, period)
            stock = get_stock_object(ticker_to_display)
        
        if hist_data is not None and info is not None and stock is not None and not hist_data.empty:
            # Display stock name and current info
            st.title(f"{info.get('longName', ticker_to_display)} ({ticker_to_display})")
            
            # Current price with change
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            previous_close = info.get('previousClose', 'N/A')
            
            if current_price != 'N/A' and previous_close != 'N/A':
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
                
                # Calculate monthly and yearly returns
                monthly_return = None
                yearly_return = None
                
                if not hist_data.empty and len(hist_data) > 0:
                    latest_price = hist_data['Close'].iloc[-1]
                    
                    # Monthly return (approximately 21 trading days = 1 month)
                    try:
                        if len(hist_data) >= 21:
                            price_month_ago = hist_data['Close'].iloc[-21]
                            monthly_return = ((latest_price - price_month_ago) / price_month_ago) * 100
                        elif len(hist_data) >= 10:  # If less than a month of data, use what we have
                            price_month_ago = hist_data['Close'].iloc[0]
                            monthly_return = ((latest_price - price_month_ago) / price_month_ago) * 100
                    except Exception as e:
                        pass
                    
                    # Yearly return (approximately 252 trading days = 1 year)
                    try:
                        if len(hist_data) >= 252:
                            price_year_ago = hist_data['Close'].iloc[-252]
                            yearly_return = ((latest_price - price_year_ago) / price_year_ago) * 100
                        elif len(hist_data) >= 100:  # If less than a year of data, use what we have
                            price_year_ago = hist_data['Close'].iloc[0]
                            yearly_return = ((latest_price - price_year_ago) / price_year_ago) * 100
                    except Exception as e:
                        pass
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Current Price", f"${current_price:.2f}")
                with col2:
                    st.metric(
                        "Change (24h)",
                        f"${change:.2f}",
                        f"{change_percent:.2f}%"
                    )
                with col3:
                    if monthly_return is not None:
                        st.metric(
                            "Monthly Return",
                            "",
                            delta=f"{monthly_return:.2f}%"
                        )
                    else:
                        st.metric("Monthly Return", "N/A")
                with col4:
                    if yearly_return is not None:
                        st.metric(
                            "Yearly Return",
                            "",
                            delta=f"{yearly_return:.2f}%"
                        )
                    else:
                        st.metric("Yearly Return", "N/A")
                
                # Last updated timestamp
                last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.caption(f"Last updated: {last_updated}")
            
            st.markdown("---")
            
            # Key metrics
            st.subheader("Key Metrics")
            display_key_metrics(info)
            
            st.markdown("---")
            
            # Price chart
            st.subheader(f"Price Chart ({selected_period})")
            fig = create_price_chart(hist_data, ticker_to_display)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Financial highlights
            display_financial_highlights(info)
            
            st.markdown("---")
            
            # Additional data
            display_additional_data(stock, ticker_to_display)

            st.markdown("---")

            display_company_info(info)
            
            # Download data option
            st.markdown("---")
            st.subheader("Download Data")
            csv = hist_data.to_csv()
            st.download_button(
                label="Download Historical Data as CSV",
                data=csv,
                file_name=f"{ticker_to_display}_historical_data.csv",
                mime="text/csv"
            )

            
        else:
            st.error(f"❌ Could not fetch data for ticker '{ticker_to_display}'. Please check if the ticker is valid and try again.")
            st.info("💡 Tip: Make sure you're using valid US stock tickers (e.g., AAPL, MSFT, GOOGL)")
    else:
        # Welcome message when no stock is selected
        st.info("Enter a stock ticker in the sidebar to begin analysis!")


if __name__ == "__main__":
    main()