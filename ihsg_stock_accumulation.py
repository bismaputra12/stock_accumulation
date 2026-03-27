import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from concurrent.futures import ThreadPoolExecutor

# --- APP CONFIG ---
st.set_page_config(page_title="IDX Whale Hunter", layout="wide")
st.title("🐋 IDX Whale Hunter")

# --- STEP 1: ROBUST TICKER FETCHING ---
@st.cache_data(ttl=86400)
def get_all_idx_tickers():
    """Fetches full IDX ticker list from a stable source"""
    try:
        # A reliable public list of Indonesian tickers
        url = "https://raw.githubusercontent.com/man-c/idx-stocks/master/tickers.csv"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # This CSV usually has a header "ticker"
            lines = response.text.splitlines()
            tickers = [line.split(',')[0].strip() for line in lines if len(line.split(',')[0].strip()) == 4]
            return sorted(list(set(tickers)))
    except:
        pass
    
    # HARDCODED FALLBACK (Top 50)
    return [
        "ADRO", "AKRA", "AMRT", "ANTM", "ASII", "BBCA", "BBNI", "BBRI", "BBTN", "BMRI", 
        "BRPT", "CPIN", "EXCL", "GOTO", "HRUM", "ICBP", "INCO", "INDF", "INKP", "ITMG", 
        "KLBF", "MDKA", "MEDC", "PGAS", "PTBA", "SMGR", "TLKM", "TPIA", "UNTR", "UNVR",
        "AMMN", "BRIS", "BUKA", "CUAN", "FILM", "MBMA", "DEWA", "NCKL", "NCRL", "INDY"
    ]

def clean_yfinance_df(df):
    """Fixes the 'DuplicateError' by ensuring column names are unique and simple"""
    if df is None or df.empty:
        return None
    
    # 1. Flatten MultiIndex if it exists
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 2. REMOVE DUPLICATE COLUMNS (This fixes your Narwhals error)
    df = df.loc[:, ~df.columns.duplicated()].copy()
    
    # 3. Ensure we have the standard OHLCV columns
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    if all(col in df.columns for col in required):
        return df[required].astype(float)
    return None

# --- STEP 2: ANALYSIS LOGIC ---
def analyze_stock(ticker):
    symbol = f"{ticker}.JK"
    try:
        raw_df = yf.download(symbol, period="2mo", interval="1d", progress=False)
        df = clean_yfinance_df(raw_df)
        
        if df is None or len(df) < 15:
            return None

        # Calculations
        vol_avg = df['Volume'].rolling(window=20).mean()
        price_change = df['Close'].pct_change()

        last_vol = df['Volume'].iloc[-1]
        last_avg = vol_avg.iloc[-1]
        last_change = price_change.iloc[-1]
        last_price = df['Close'].iloc[-1]
        vol_ratio = last_vol / last_avg

        # DETECTION CRITERIA
        if vol_ratio > 1.8 and abs(last_change) < 0.012:
            return {"Ticker": ticker, "Price": last_price, "Change%": last_change*100, "Vol_Ratio": vol_ratio, "Signal": "Quiet Accumulation 💎"}
        elif vol_ratio > 2.5 and last_change > 0.025:
            return {"Ticker": ticker, "Price": last_price, "Change%": last_change*100, "Vol_Ratio": vol_ratio, "Signal": "Aggressive Markup 🚀"}
        return None
    except:
        return None

# --- UI CONTROLS ---
tickers = get_all_idx_tickers()
st.sidebar.success(f"✅ Loaded {len(tickers)} IDX Tickers")
scan_mode = st.sidebar.radio("Scan Range:", ["Top 100 Stocks (Fast)", "Full Market (~900)"])

if st.sidebar.button("🔍 Start Market Scan"):
    scan_list = tickers[:100] if "Top 100" in scan_mode else tickers
    results = []
    st.write(f"### 🔎 Scanning {len(scan_list)} stocks...")
    bar = st.progress(0)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(analyze_stock, t): t for t in scan_list}
        for i, future in enumerate(futures):
            res = future.result()
            if res:
                results.append(res)
            bar.progress((i + 1) / len(scan_list))

    if results:
        st.success(f"Found {len(results)} potential whale entries.")
        df_results = pd.DataFrame(results).sort_values(by="Vol_Ratio", ascending=False)
        st.table(df_results) # Using table for stability
        
        st.divider()
        for r in results:
            with st.expander(f"CHART: {r['Ticker']} ({r['Signal']})"):
                # Fetch again for chart
                raw_chart_df = yf.download(f"{r['Ticker']}.JK", period="3mo", progress=False)
                chart_df = clean_yfinance_df(raw_chart_df)
                
                if chart_df is not None:
                    fig = go.Figure(data=[go.Candlestick(
                        x=chart_df.index,
                        open=chart_df['Open'], 
                        high=chart_df['High'], 
                        low=chart_df['Low'], 
                        close=chart_df['Close']
                    )])
                    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0))
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No accumulation detected in this batch.")
else:
    st.info("Select a scan range and click the button.")
