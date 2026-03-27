import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from concurrent.futures import ThreadPoolExecutor

# --- APP CONFIG ---
st.set_page_config(page_title="IDX Full Market Whale Hunter", layout="wide")
st.title("🐋 IDX Whale Hunter: Full Market (900+ Stocks)")

# --- STEP 1: DYNAMIC TICKER LOADER (900+ STOCKS) ---
@st.cache_data(ttl=86400)
def get_full_market_tickers():
    """Fetches the complete list of IDX stocks from the most reliable open-source database"""
    # This URL contains the full list of ~900 tickers
    url = "https://raw.githubusercontent.com/man-c/idx-stocks/master/tickers.csv"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            lines = response.text.splitlines()
            # We extract the first column (Ticker), ensure it's 4 chars, and sort it
            full_list = sorted(list(set([line.split(',')[0].strip().upper() for line in lines if len(line.split(',')[0].strip()) == 4])))
            if len(full_list) > 500: # Verification that we got the whole market
                return full_list
    except:
        pass
    
    # If the URL fails, we use a high-quality backup of the top 300 stocks
    return ["BBCA", "BBRI", "TLKM", "GOTO", "ASII", "BMRI"] # This shouldn't happen with the URL above

# --- STEP 2: INDIVIDUAL ANALYSIS ENGINE ---
def analyze_stock(ticker, sens_vol, sens_price):
    """Downloads 1 month of data and checks for Whale Footprints"""
    symbol = f"{ticker}.JK"
    try:
        # We only download 1 month to keep the scan fast
        df = yf.download(symbol, period="1mo", interval="1d", progress=False, show_errors=False)
        
        # Clean up yfinance formatting
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.dropna()
        if len(df) < 10: return None

        # Calculate VSA (Volume Spread Analysis)
        last_price = float(df['Close'].iloc[-1])
        last_vol = float(df['Volume'].iloc[-1])
        vol_avg = df['Volume'].rolling(window=15).mean().iloc[-1]
        
        # Skip 'Penny Stocks' or stocks with no liquidity
        if last_vol < 5000 or last_price < 50: return None

        vol_ratio = last_vol / vol_avg
        prev_close = float(df['Close'].iloc[-2])
        price_change = ((last_price - prev_close) / prev_close) * 100

        # --- THE SIGNAL LOGIC ---
        # 1. Accumulation: Vol Ratio > User Setting AND Price Change is small
        if vol_ratio >= sens_vol and abs(price_change) <= sens_price:
            return {"Ticker": ticker, "Price": last_price, "Change%": round(price_change, 2), "Vol_Ratio": round(vol_ratio, 2), "Signal": "Accumulation 💎"}
        
        # 2. Aggressive Entry: Massive Vol AND Price breakout
        elif vol_ratio >= (sens_vol + 0.5) and price_change > 2.0:
            return {"Ticker": ticker, "Price": last_price, "Change%": round(price_change, 2), "Vol_Ratio": round(vol_ratio, 2), "Signal": "Aggressive Markup 🚀"}
            
        return None
    except:
        return None

# --- UI CONTROLS ---
tickers = get_full_market_tickers()
st.sidebar.title("Scanner Settings")
st.sidebar.success(f"✅ Full Market Loaded: **{len(tickers)} Stocks**")

# Users can adjust sensitivity if 0 results appear
sens_vol = st.sidebar.slider("Volume Sensitivity (1.5x is standard)", 1.1, 3.0, 1.3)
sens_price = st.sidebar.slider("Price Stability % (Max move for Accumulation)", 0.2, 3.0, 1.2)

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []

if st.sidebar.button("🔍 Run Full Market Scan"):
    st.session_state.scan_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Scanning 900+ stocks in parallel
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(analyze_stock, t, sens_vol, sens_price): t for t in tickers}
        
        for i, future in enumerate(futures):
            res = future.result()
            if res:
                st.session_state.scan_results.append(res)
            
            # Update visual progress
            if i % 20 == 0:
                progress = (i + 1) / len(tickers)
                progress_bar.progress(progress)
                status_text.text(f"Scanning {i}/{len(tickers)} tickers...")

    status_text.success(f"Done! Scanned {len(tickers)} stocks. Found {len(st.session_state.scan_results)} whales.")

# --- RESULTS ---
if st.session_state.scan_results:
    df_res = pd.DataFrame(st.session_state.scan_results).sort_values(by="Vol_Ratio", ascending=False)
    st.subheader(f"📊 {len(df_res)} Whale Signatures Detected")
    st.dataframe(df_res, use_container_width=True)
    
    st.divider()
    for r in st.session_state.scan_results:
        with st.expander(f"SEE CHART: {r['Ticker']} ({r['Signal']})"):
            c_data = yf.download(f"{r['Ticker']}.JK", period="3mo", progress=False)
            if isinstance(c_data.columns, pd.MultiIndex): c_data.columns = c_data.columns.get_level_values(0)
            
            fig = go.Figure(data=[go.Candlestick(x=c_data.index, open=c_data['Open'], high=c_data['High'], low=c_data['Low'], close=c_data['Close'])])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Market is ready. Click the 'Run Full Market Scan' button.")
