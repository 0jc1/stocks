# 📈 US Stock Analyzer

A comprehensive Streamlit web application for analyzing US stocks in real-time.

## Features

- 🔍 **Search & Analyze** - Search any US stock by ticker symbol
- 📊 **Real-time Data** - Get current prices, market cap, volume, and more
- 📈 **Interactive Charts** - Candlestick price charts with volume analysis
- 💰 **Financial Metrics** - P/E ratio, dividend yield, beta, and key ratios
- 📰 **Company News** - Latest news and updates for stocks
- 💼 **Financial Statements** - View income statements, balance sheets, and cash flow
- 📉 **Multiple Timeframes** - Analyze data from 1 week to max history
- 💾 **Export Data** - Download historical data as CSV

## Installation

1. Install dependencies:
```bash
uv sync
```

## Usage

Run the Streamlit app:
```bash
uv run streamlit run main.py
```

The app will open in your default web browser at `http://localhost:8501`

## How to Use

1. **Search for a Stock**: Enter a ticker symbol (e.g., AAPL, MSFT, GOOGL) in the sidebar
2. **Select Timeframe**: Choose from 1 week to maximum historical data
3. **Analyze**: View comprehensive metrics, charts, and company information
4. **Quick Access**: Use popular stock buttons for quick analysis
5. **Download**: Export historical data as CSV for further analysis

## Popular Stock Tickers

- AAPL - Apple Inc.
- MSFT - Microsoft Corporation
- GOOGL - Alphabet Inc.
- AMZN - Amazon.com Inc.
- TSLA - Tesla Inc.
- META - Meta Platforms Inc.
- NVDA - NVIDIA Corporation
- JPM - JPMorgan Chase & Co.
- V - Visa Inc.
- WMT - Walmart Inc.

## Data Source

This app uses [yfinance](https://github.com/ranaroussi/yfinance) to fetch real-time stock data from Yahoo Finance.

## Technologies Used

- **Streamlit** - Web framework
- **yfinance** - Stock data API
- **Plotly** - Interactive charts
- **Pandas** - Data manipulation

