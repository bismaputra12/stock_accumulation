import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor

# --- APP CONFIG ---
st.set_page_config(page_title="IDX Whale Hunter", layout="wide")
st.title("🐋 IDX Whale Hunter: Automated Accumulation Screener")
st.caption("Automatically fetching all IDX tickers and scanning for Big Player footprints...")

# --- STEP 1: AUTO-FETCH TICKERS ---
@st.cache_data(ttl=86400) # Refresh list once a day
def get_all_idx_tickers():
    """Scrapes the full list of tickers from a reliable public source"""
    try:
        # Using a reliable public list of Indonesian tickers
        url = "https://www.idnfinancials.com/company"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tickers = []
        # Find all stock codes in the table
        for link in soup.select('a[href*="/company/"]'):
            code = link.text.strip()
            if len(code) == 4 and code.isupper():
                tickers.append(code)
        
        return sorted(list(set(tickers)))
    except:
        # Fallback list if scraping fails
        return ["BBCA", "BBRI", "TLKM", "ASII", "GOTO", "BMRI", "BBNI", "ADRO"]

# --- STEP 2: SCANNING LOGIC ---
def analyze_stock(ticker):
    """The 'Brain' that detects Big Players"""
    symbol = f"{ticker}.JK"
    try:
        df = yf.download(symbol, period="1mo", interval="1d", progress=False)
        if df.empty or len(df) < 15:
            return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close'].astype(float)
        vol = df['Volume'].astype(float)
        vol_avg = vol.rolling(window=20).mean()
        price_change = close.pct_change()

        last_vol = float(vol.iloc[-1])
        last_avg_vol = float(vol_avg.iloc[-1])
        last_change = float(price_change.iloc[-1])
        last_price = float(close.iloc[-1])
        vol_ratio = last_vol / last_avg_vol

        # Criteria 1: "Quiet Accumulation" (The Lot Proxy)
        # High volume relative to 20-day avg, but price is stable.
        # This means someone is buying 'big lots' but not chasing the price.
        if vol_ratio > 1.8 and abs(last_change) < 0.012:
            return {
                "Ticker": ticker, 
                "Price": last_price, 
                "Change%": last_change*100, 
                "Vol_Ratio": vol_ratio, 
                "Signal": "Quiet Accumulation 💎",
                "Insight": "Big Player absorbing supply."
            }
        
        # Criteria 2: "Foreign/Aggressive Markup"
        # Massive volume spike and breaking out.
        elif vol_ratio > 2.5 and last_change > 0.025:
            return {
                "Ticker": ticker, 
                "Price": last_price, 
                "Change%": last_change*100, 
                "Vol_Ratio": vol_ratio, 
                "Signal": "Aggressive Markup 🚀",
                "Insight": "Whales pushing price higher."
            }
            
        return None
    except:
        return None

# --- UI CONTROLS ---
tickers = get_all_idx_tickers()
st.sidebar.write(f"✅ Automatically found **{len(tickers)}** IDX tickers.")

if st.sidebar.button("🔍 Scan Entire Market Now"):
    results = []
    st.write("### 🔎 Scanning for Big Player Footprints...")
    progress_text = st.empty()
    bar = st.progress(0)
    
    # We use ThreadPoolExecutor to scan 20 stocks at once (Speed!)
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(analyze_stock, t): t for t in tickers}
        
        for i, future in enumerate(futures):
            res = future.result()
            if res:
                results.append(res)
            # Update UI progress every 10 stocks
            if i % 10 == 0:
                bar.progress((i + 1) / len(tickers))
                progress_text.text(f"Checking {futures[future]}...")

    if results:
        st.success(f"Done! Found {len(results)} stocks being accumulated by Big Players.")
        df_results = pd.DataFrame(results).sort_values(by="Vol_Ratio", ascending=False)
        
        # Display Table
        st.dataframe(df_results.style.background_gradient(subset=['Vol_Ratio'], cmap='Greens'), use_container_width=True)
        
        # Detail View
        st.divider()
        st.subheader("Visual Confirmation")
        for r in results:
            with st.expander(f"SEE CHART: {r['Ticker']} - {r['Signal']}"):
                st.write(f"**Whale Insight:** {r['Insight']}")
                chart_df = yf.download(f"{r['Ticker']}.JK", period="3mo", progress=False)
                if isinstance(chart_df.columns, pd.MultiIndex):
                    chart_df.columns = chart_df.columns.get_level_values(0)
                
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_df.index,
                    open=chart_df['Open'], high=chart_df['High'],
                    low=chart_df['Low'], close=chart_df['Close']
                )])
                fig.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No clear Big Player activity detected right now. Markets might be quiet.")
else:
    st.info("Click the button in the sidebar to start the automated scan.")

# --- FOOTER ---
st.sidebar.markdown("""
---
**The 'Big Player' Rule used here:**
- **Vol Ratio > 1.8x:** Today's trading volume is nearly double the monthly average.
- **Price Stability:** If the price hasn't moved much despite huge volume, it's a 'Quiet Buy' (Accumulation).
- **Markup:** If price and volume explode together, the Big Player is 'Marking Up' the stock.
""")
