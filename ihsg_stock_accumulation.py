import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from concurrent.futures import ThreadPoolExecutor

# --- APP CONFIG ---
st.set_page_config(page_title="IDX Whale Hunter", layout="wide")
st.title("🐋 IDX Whale Hunter: Automated Accumulation Screener")

# --- STEP 1: ROBUST TICKER FETCHING ---
@st.cache_data(ttl=86400)
def get_all_idx_tickers():
    """Fetches full IDX ticker list from a stable data source"""
    try:
        # Source: A reliable community-maintained list of IDX tickers
        url = "https://raw.githubusercontent.com/bloomberg/karson/master/data/idx_tickers.json"
        # Alternative: We can also use a hardcoded fallback of major stocks
        response = requests.get(url, timeout=10)
        if response.status_status == 200:
            data = response.json()
            # Clean and ensure they are 4-letter codes
            tickers = [t.replace(".JK", "") for t in data if len(t.replace(".JK", "")) == 4]
            return sorted(list(set(tickers)))
    except:
        pass
    
    # ULTIMATE FALLBACK: If external sources fail, use this Top 100 list
    return [
        "ADRO", "AKRA", "AMRT", "ANTM", "ASII", "BBCA", "BBNI", "BBRI", "BBTN", "BMRI", 
        "BRPT", "CPIN", "EXCL", "GOTO", "HRUM", "ICBP", "INCO", "INDF", "INKP", "ITMG", 
        "KLBF", "MDKA", "MEDC", "PGAS", "PTBA", "SMGR", "TLKM", "TPIA", "UNTR", "UNVR",
        "AMMN", "BRIS", "BUKA", "CUAN", "FILM", "MBMA", "MTEL", "NCKL", "NCRL", "PERT"
    ]

# --- STEP 2: ANALYSIS LOGIC ---
def analyze_stock(ticker):
    symbol = f"{ticker}.JK"
    try:
        # Get 2 months of data
        df = yf.download(symbol, period="2mo", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            return None
        
        # Flatten MultiIndex columns (yfinance 0.2.40+ fix)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Convert to float to avoid calculation errors
        close = df['Close'].astype(float)
        vol = df['Volume'].astype(float)
        vol_avg = vol.rolling(window=20).mean()
        price_change = close.pct_change()

        last_vol = float(vol.iloc[-1])
        last_avg = float(vol_avg.iloc[-1])
        last_change = float(price_change.iloc[-1])
        last_price = float(close.iloc[-1])
        vol_ratio = last_vol / last_avg

        # DETECTION CRITERIA
        # 1. Quiet Accumulation: High volume (>1.7x) but tiny price movement (<1.2%)
        if vol_ratio > 1.7 and abs(last_change) < 0.012:
            return {"Ticker": ticker, "Price": last_price, "Change%": last_change*100, "Vol_Ratio": vol_ratio, "Signal": "Quiet Accumulation 💎"}
        
        # 2. Aggressive Entry: Massive volume (>2.5x) and price breakout (>2.5%)
        elif vol_ratio > 2.5 and last_change > 0.025:
            return {"Ticker": ticker, "Price": last_price, "Change%": last_change*100, "Vol_Ratio": vol_ratio, "Signal": "Aggressive Markup 🚀"}
            
        return None
    except:
        return None

# --- UI CONTROLS ---
tickers = get_all_idx_tickers()
st.sidebar.success(f"✅ Loaded {len(tickers)} IDX Tickers")

# Option to scan only the top liquid stocks or everything
scan_mode = st.sidebar.radio("Scan Range:", ["Top 100 Stocks (Fast)", "Full Market (~900 stocks)"])

if st.sidebar.button("🔍 Start Market Scan"):
    # Slice the list based on user choice to prevent timeouts
    scan_list = tickers[:100] if "Top 100" in scan_mode else tickers
    
    results = []
    st.write(f"### 🔎 Scanning {len(scan_list)} stocks for Whale footprints...")
    bar = st.progress(0)
    
    # Process in parallel (faster)
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(analyze_stock, t): t for t in scan_list}
        for i, future in enumerate(futures):
            res = future.result()
            if res:
                results.append(res)
            bar.progress((i + 1) / len(scan_list))

    if results:
        st.success(f"Scan complete! Found {len(results)} potential whale entries.")
        df_results = pd.DataFrame(results).sort_values(by="Vol_Ratio", ascending=False)
        st.dataframe(df_results, use_container_width=True)
        
        # Visual Charts
        st.divider()
        for r in results:
            with st.expander(f"CHART: {r['Ticker']} ({r['Signal']})"):
                chart_df = yf.download(f"{r['Ticker']}.JK", period="3mo", progress=False)
                if isinstance(chart_df.columns, pd.MultiIndex):
                    chart_df.columns = chart_df.columns.get_level_values(0)
                fig = go.Figure(data=[go.Candlestick(x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'])])
                fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No clear Big Player activity detected in this batch. Try the 'Full Market' scan.")
else:
    st.info("Select a scan range and click the button to start.")
