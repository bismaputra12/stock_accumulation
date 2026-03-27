import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from concurrent.futures import ThreadPoolExecutor

# --- APP CONFIG ---
st.set_page_config(page_title="IDX Whale Hunter", layout="wide")
st.title("🐋 IDX Whale Hunter: Pro Edition")
st.caption("Detecting Big Player accumulation using Volume Spread Analysis (VSA).")

# --- STEP 1: STABLE TICKER FETCHING ---
@st.cache_data(ttl=86400)
def get_all_idx_tickers():
    """Fetches full IDX ticker list from a stable, sorted source"""
    # Source: Community-maintained list of all IDX stocks
    url = "https://raw.githubusercontent.com/man-c/idx-stocks/master/tickers.csv"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            lines = response.text.splitlines()
            # Extract ticker, ensure 4 chars, and SORT alphabetically for stability
            tickers = sorted(list(set([line.split(',')[0].strip() for line in lines if len(line.split(',')[0].strip()) == 4])))
            if tickers:
                return tickers
    except Exception as e:
        st.error(f"Error fetching tickers: {e}")
    
    # Standard 100 most liquid if the source is down
    return ["BBCA", "BBRI", "TLKM", "ASII", "GOTO", "BMRI", "BBNI", "ADRO"]

def clean_data(df):
    """Deep cleaning to prevent DuplicateError and Narwhals crashes"""
    if df is None or df.empty:
        return None
    # Flatten MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # Drop duplicates by name
    df = df.loc[:, ~df.columns.duplicated()].copy()
    # Force float type
    return df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)

# --- STEP 2: ANALYSIS LOGIC ---
def analyze_stock(ticker):
    symbol = f"{ticker}.JK"
    try:
        raw_df = yf.download(symbol, period="2mo", interval="1d", progress=False)
        df = clean_data(raw_df)
        
        if df is None or len(df) < 20:
            return None

        # Logic for Big Player (VSA)
        vol_avg = df['Volume'].rolling(window=20).mean()
        last_vol = df['Volume'].iloc[-1]
        last_avg = vol_avg.iloc[-1]
        vol_ratio = last_vol / last_avg
        
        last_change = df['Close'].pct_change().iloc[-1]
        last_price = df['Close'].iloc[-1]

        # LOGIC:
        # Quiet Accumulation: Vol > 1.7x average, but price spread is tiny.
        # This is a classic "Big Player absorbing shares" sign.
        if vol_ratio > 1.7 and abs(last_change) < 0.012:
            return {
                "Ticker": ticker, 
                "Price": last_price, 
                "Change%": round(last_change*100, 2), 
                "Vol_Ratio": round(vol_ratio, 2), 
                "Status": "Accumulation 💎"
            }
        
        # Aggressive Markup: Vol > 2.5x average, price is breaking out.
        elif vol_ratio > 2.2 and last_change > 0.025:
            return {
                "Ticker": ticker, 
                "Price": last_price, 
                "Change%": round(last_change*100, 2), 
                "Vol_Ratio": round(vol_ratio, 2), 
                "Status": "Markup 🚀"
            }
        return None
    except:
        return None

# --- UI ---
tickers = get_all_idx_tickers()
st.sidebar.info(f"Connected to IDX database. Ready to scan {len(tickers)} stocks.")

# Persist the scan results using Session State so they don't disappear on refresh
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []

col1, col2 = st.sidebar.columns(2)
start_scan = col1.button("🔍 Scan Full Market")
clear_scan = col2.button("🗑️ Clear")

if clear_scan:
    st.session_state.scan_results = []
    st.rerun()

if start_scan:
    st.session_state.scan_results = [] # Reset for new scan
    progress_bar = st.progress(0)
    st.write(f"### 🚀 Scanning the whole market... (This takes ~45 seconds)")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(analyze_stock, t): t for t in tickers}
        for i, future in enumerate(futures):
            res = future.result()
            if res:
                st.session_state.scan_results.append(res)
            # Update progress every 20 tickers
            if i % 20 == 0:
                progress_bar.progress((i + 1) / len(tickers))
    
    st.success(f"Scan complete. Found {len(st.session_state.scan_results)} alerts.")

# --- DISPLAY RESULTS ---
if st.session_state.scan_results:
    # Sort results by Volume Ratio (Highest first) so the list is always consistent
    df_results = pd.DataFrame(st.session_state.scan_results).sort_values(by="Vol_Ratio", ascending=False)
    
    st.subheader("📋 Stocks showing Big Player activity")
    st.dataframe(df_results, use_container_width=True)
    
    st.divider()
    st.subheader("📈 Detailed Analysis")
    
    for r in st.session_state.scan_results:
        with st.expander(f"{r['Status']} detected in {r['Ticker']} (Vol: {r['Vol_Ratio']}x)"):
            chart_raw = yf.download(f"{r['Ticker']}.JK", period="3mo", progress=False)
            chart_df = clean_data(chart_raw)
            if chart_df is not None:
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_df.index,
                    open=chart_df['Open'], high=chart_df['High'],
                    low=chart_df['Low'], close=chart_df['Close']
                )])
                fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0))
                st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Click 'Scan Full Market' in the sidebar to start.")

st.sidebar.markdown("""
---
**VSA Strategy Guide:**
- **Accumulation (💎):** Large Volume but no price change. Big players are using "Iceberg Orders" to buy without moving the price.
- **Markup (🚀):** Big players are done buying and are now aggressively pushing the price up.
""")
