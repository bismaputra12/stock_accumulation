import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import requests

# --- APP CONFIG ---
st.set_page_config(page_title="IDX Big Player Tracker", layout="wide")
st.title("🚀 IDX Big Player & Foreign Flow Tracker")

# --- FUNCTIONS ---

def get_stock_data(ticker):
    """Fetch stock data and fix multi-index column issues"""
    symbol = f"{ticker}.JK"
    # We download 4 months to ensure we have enough for the 20-day average
    df = yf.download(symbol, period="4mo", interval="1d", progress=False)
    
    if df.empty:
        return None

    # FIX: Recent yfinance versions return MultiIndex columns. We flatten them.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    return df

def analyze_accumulation(df):
    """Logic to detect big players using Price-Volume Divergence"""
    # Ensure columns are treated as floats
    close_prices = df['Close'].astype(float)
    volumes = df['Volume'].astype(float)
    
    # Calculate indicators
    vol_avg = volumes.rolling(window=20).mean()
    price_change = close_prices.pct_change()
    
    # Get the very last values (the most recent trading day)
    current_vol = float(volumes.iloc[-1])
    current_avg_vol = float(vol_avg.iloc[-1])
    current_price_change = float(price_change.iloc[-1])
    
    vol_ratio = current_vol / current_avg_vol
    
    status = "Neutral / Low Volume"
    color = "white"
    
    # Logic for Big Player Movements
    if vol_ratio > 1.5 and abs(current_price_change) < 0.01:
        status = "🔥 QUIET ACCUMULATION (Big Players buying hiddenly)"
        color = "#00FF00"
    elif vol_ratio > 2.0 and current_price_change > 0.02:
        status = "🚀 AGGRESSIVE BUYING (Big Players pushing price)"
        color = "#1E90FF"
    elif vol_ratio > 1.5 and current_price_change < -0.02:
        status = "⚠️ DISTRIBUTION (Big Players selling/dumping)"
        color = "#FF4500"
    elif vol_ratio > 1.2:
        status = "👀 Increasing Interest"
        color = "#FFFF00"
        
    return status, vol_ratio, color

def get_5percent_disclosures(ticker):
    """Scrape news for shareholder changes"""
    url = f"https://www.idnfinancials.com/{ticker}/news"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []
        keywords = ['kepemilikan', 'shareholder', 'persen', 'buyback', 'acquisition', 'tambah']
        
        for link in soup.find_all('a'):
            text = link.text.strip().lower()
            if any(k in text for k in keywords):
                news_items.append(link.text.strip())
        return list(set(news_items))[:5]
    except:
        return []

# --- UI LAYOUT ---
st.sidebar.header("Control Panel")
watch_list = st.sidebar.text_input("Enter Tickers (comma separated)", "BBCA,BBRI,TLKM,GOTO,AMMN,ASII,BBNI")
tickers = [t.strip().upper() for t in watch_list.split(",")]

for ticker in tickers:
    with st.expander(f"📊 Analysis for {ticker}", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        data = get_stock_data(ticker)
        
        if data is None or len(data) < 20:
            st.warning(f"Waiting for data or ticker {ticker} not found on Yahoo Finance.")
            continue
            
        try:
            status, ratio, color = analyze_accumulation(data)
            
            with col1:
                # Candlestick Chart
                fig = go.Figure(data=[go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='Price'
                )])
                fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown(f"### Detection:\n### <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
                st.metric("Volume vs 20D Avg", f"{ratio:.2f}x")
                
                st.markdown("---")
                st.write("**Recent Potential 'Whale' News:**")
                news = get_5percent_disclosures(ticker)
                if news:
                    for n in news:
                        st.write(f"✅ {n}")
                else:
                    st.write("No major ownership news found.")

        except Exception as e:
            st.error(f"Error analyzing {ticker}: {str(e)}")

st.sidebar.info("Tip: 'Quiet Accumulation' is the best time to buy. It means volume is high (Big Players entering) but the price hasn't exploded yet.")
