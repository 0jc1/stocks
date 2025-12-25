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

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
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
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Current Price",
            f"${info.get('currentPrice', 'N/A')}" if info.get('currentPrice') else "N/A"
        )
        st.metric(
            "Day Range",
            f"${info.get('dayLow', 'N/A')} - ${info.get('dayHigh', 'N/A')}"
        )
    
    with col2:
        market_cap = format_number(info.get('marketCap'))
        st.metric("Market Cap", market_cap)
        
        pe_ratio = info.get('trailingPE', 'N/A')
        if pe_ratio and pe_ratio != 'N/A':
            pe_ratio = f"{pe_ratio:.2f}"
        st.metric("P/E Ratio", pe_ratio)
    
    with col3:
        week_52_low = info.get('fiftyTwoWeekLow', 'N/A')
        week_52_high = info.get('fiftyTwoWeekHigh', 'N/A')
        st.metric("52 Week Range", f"${week_52_low} - ${week_52_high}")
        
        avg_volume = info.get('averageVolume', 'N/A')
        if avg_volume and avg_volume != 'N/A':
            avg_volume = f"{avg_volume:,}"
        st.metric("Avg Volume", avg_volume)
    
    with col4:
        div_yield = info.get('dividendYield')
        if div_yield:
            div_yield = format_percentage(div_yield * 100)
        else:
            div_yield = "N/A"
        st.metric("Dividend Yield", div_yield)
        
        beta = info.get('beta', 'N/A')
        if beta and beta != 'N/A':
            beta = f"{beta:.2f}"
        st.metric("Beta", beta)


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
        
        # Forward PE
        forward_pe = info.get('forwardPE', 'N/A')
        if forward_pe and forward_pe != 'N/A':
            forward_pe = f"{forward_pe:.2f}"
        st.write(f"**Forward P/E:** {forward_pe}")
        
        # PEG Ratio
        peg = info.get('pegRatio', 'N/A')
        if peg and peg != 'N/A':
            peg = f"{peg:.2f}"
        st.write(f"**PEG Ratio:** {peg}")
    
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
            st.write(f"Volume: {info.get('volume', 'N/A'):,}" if info.get('volume') else "Volume: N/A")
        
        with col2:
            st.write("**Stock Price Info**")
            st.write(f"Regular Market Volume: {info.get('regularMarketVolume', 'N/A'):,}" if info.get('regularMarketVolume') else "Regular Market Volume: N/A")
            st.write(f"Average Volume (10d): {info.get('averageVolume10days', 'N/A'):,}" if info.get('averageVolume10days') else "Average Volume (10d): N/A")
            st.write(f"Shares Outstanding: {format_number(info.get('sharesOutstanding'))}")
            st.write(f"Float Shares: {format_number(info.get('floatShares'))}")
    
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
        
        fin_tab1, fin_tab2, fin_tab3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
        
        with fin_tab1:
            try:
                income_stmt = stock.financials
                if income_stmt is not None and not income_stmt.empty:
                    st.dataframe(income_stmt, use_container_width=True)
                else:
                    st.info("Income statement data not available.")
            except:
                st.info("Income statement data not available.")
        
        with fin_tab2:
            try:
                balance_sheet = stock.balance_sheet
                if balance_sheet is not None and not balance_sheet.empty:
                    st.dataframe(balance_sheet, use_container_width=True)
                else:
                    st.info("Balance sheet data not available.")
            except:
                st.info("Balance sheet data not available.")
        
        with fin_tab3:
            try:
                cashflow = stock.cashflow
                if cashflow is not None and not cashflow.empty:
                    st.dataframe(cashflow, use_container_width=True)
                else:
                    st.info("Cash flow data not available.")
            except:
                st.info("Cash flow data not available.")


def main():
    # Header
    st.markdown('<h1 class="main-header">📈 US Stock Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("Search Settings")
        
        # Stock ticker input
        ticker_input = st.text_input(
            "Enter Stock Ticker",
            value="AAPL",
            help="Enter a valid US stock ticker (e.g., AAPL, MSFT, GOOGL)"
        ).upper()
        
        # Time period selection
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
            index=4  # Default to 1 Year
        )
        
        period = period_options[selected_period]
        
        # Search button
        search_button = st.button("🔍 Search Stock", type="primary", use_container_width=True)
        
        st.markdown("---")
        
        # Popular stocks quick access
        st.subheader("Popular Stocks")
        popular_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "WMT"]
        
        cols = st.columns(2)
        for idx, stock in enumerate(popular_stocks):
            col = cols[idx % 2]
            if col.button(stock, use_container_width=True):
                ticker_input = stock
                search_button = True
    
    # Main content
    if ticker_input:
        with st.spinner(f"Loading data for {ticker_input}..."):
            hist_data, info = get_stock_data(ticker_input, period)
            stock = get_stock_object(ticker_input)
        
        if hist_data is not None and info is not None and stock is not None and not hist_data.empty:
            # Display stock name and current info
            st.title(f"{info.get('longName', ticker_input)} ({ticker_input})")
            
            # Current price with change
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            previous_close = info.get('previousClose', 'N/A')
            
            if current_price != 'N/A' and previous_close != 'N/A':
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
                
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    st.metric("Current Price", f"${current_price:.2f}")
                with col2:
                    st.metric(
                        "Change",
                        f"${change:.2f}",
                        f"{change_percent:.2f}%"
                    )
                with col3:
                    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.caption(f"Last updated: {last_updated}")
            
            st.markdown("---")
            
            # Key metrics
            st.subheader("📊 Key Metrics")
            display_key_metrics(info)
            
            st.markdown("---")
            
            # Price chart
            st.subheader(f"📈 Price Chart ({selected_period})")
            fig = create_price_chart(hist_data, ticker_input)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Company info
            display_company_info(info)
            
            st.markdown("---")
            
            # Financial highlights
            display_financial_highlights(info)
            
            st.markdown("---")
            
            # Additional data
            display_additional_data(stock, ticker_input)
            
            # Download data option
            st.markdown("---")
            st.subheader("💾 Download Data")
            csv = hist_data.to_csv()
            st.download_button(
                label="Download Historical Data as CSV",
                data=csv,
                file_name=f"{ticker_input}_historical_data.csv",
                mime="text/csv"
            )
            
        else:
            st.error(f"❌ Could not fetch data for ticker '{ticker_input}'. Please check if the ticker is valid and try again.")
            st.info("💡 Tip: Make sure you're using valid US stock tickers (e.g., AAPL, MSFT, GOOGL)")
    else:
        # Welcome message when no stock is selected
        st.info("👈 Enter a stock ticker in the sidebar to begin analysis")
        
        st.markdown("### 🌟 Features")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📊 Real-time Data**
            - Current price & market cap
            - Volume & trading info
            - 52-week highs/lows
            """)
        
        with col2:
            st.markdown("""
            **📈 Interactive Charts**
            - Candlestick price charts
            - Volume analysis
            - Multiple timeframes
            """)
        
        with col3:
            st.markdown("""
            **💼 Financial Analysis**
            - Key ratios & metrics
            - Financial statements
            - Company information
            """)


if __name__ == "__main__":
    main()
