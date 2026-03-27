import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

# --- APP CONFIG ---
st.set_page_config(page_title="IDX Big Player Tracker", layout="wide")
st.title("🚀 IDX Big Player & Foreign Flow Tracker")
st.sidebar.header("Settings")

# --- FUNCTIONS ---

def get_stock_data(ticker):
    """Fetch stock data from Yahoo Finance"""
    symbol = f"{ticker}.JK"
    data = yf.download(symbol, period="3mo", interval="1d")
    return data

def analyze_accumulation(df):
    """Logic to detect big players using Price-Volume Divergence"""
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    df['Price_Change'] = df['Close'].pct_change()
    
    # Big Player Rule: Volume > 150% of average AND price movement is small (Accumulation)
    # Or Volume > 200% of average AND price is rising (Markup)
    last_row = df.iloc[-1]
    vol_ratio = last_row['Volume'] / last_row['Vol_Avg']
    
    status = "Neutral"
    color = "white"
    
    if vol_ratio > 1.5 and abs(last_row['Price_Change']) < 0.01:
        status = "QUIET ACCUMULATION (Big Players buying hiddenly)"
        color = "#00FF00"
    elif vol_ratio > 2.0 and last_row['Price_Change'] > 0.02:
        status = "AGRESSIVE BUYING (Big Players pushing price)"
        color = "#1E90FF"
    elif vol_ratio > 1.5 and last_row['Price_Change'] < -0.02:
        status = "DISTRIBUTION (Big Players selling/dumping)"
        color = "#FF4500"
        
    return status, vol_ratio, color

def get_5percent_disclosures(ticker):
    """Scrape news for shareholder changes"""
    url = f"https://www.idnfinancials.com/{ticker}/news"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        keywords = ['kepemilikan', 'shareholder', 'persen', 'buyback', 'acquisition']
        
        for link in soup.find_all('a'):
            text = link.text.strip().lower()
            if any(k in text for k in keywords):
                news_items.append(link.text.strip())
        return list(set(news_items))[:5] # Return top 5 unique headlines
    except:
        return ["Could not connect to news source."]

# --- UI LAYOUT ---
watch_list = st.sidebar.text_input("Enter Tickers (comma separated)", "BBCA,BBRI,TLKM,GOTO,AMMN,ASII")
tickers = [t.strip().upper() for t in watch_list.split(",")]

all_data = []

for ticker in tickers:
    with st.expander(f"📊 Analysis for {ticker}", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        try:
            data = get_stock_data(ticker)
            if data.empty:
                st.error(f"No data found for {ticker}")
                continue
                
            status, ratio, color = analyze_accumulation(data)
            
            with col1:
                # Plotting
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Price'))
                fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown(f"### Detection: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
                st.metric("Volume vs 20D Avg", f"{ratio:.2f}x")
                
                st.write("**Recent Shareholder Disclosures (IDX):**")
                news = get_5percent_disclosures(ticker)
                if news:
                    for n in news:
                        st.write(f"🔹 {n}")
                else:
                    st.write("No major 5% changes detected recently.")

        except Exception as e:
            st.error(f"Error analyzing {ticker}: {e}")

st.sidebar.markdown("---")
st.sidebar.write("### Strategy Tip:")
st.sidebar.info("Look for 'Quiet Accumulation'. This happens when the volume is huge but the price isn't moving yet. This usually means a Big Player is absorbing all sell orders before a markup.")
