import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup

# --- APP CONFIG ---
st.set_page_config(page_title="IDX Whale Hunter: All 900+ Stocks", layout="wide")
st.title("🐋 IDX Whale Hunter: Full Market Screener")
st.caption("Analyzing all 900+ IDX stocks for Big Player 'Iceberg' accumulation.")

# --- STEP 1: DYNAMIC FULL TICKER LIST ---
@st.cache_data(ttl=86400)
def get_all_idx_tickers():
    """Scrapes IDNFinancials for the most current list of all 940+ companies"""
    try:
        url = "https://www.idnfinancials.com/company"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tickers = []
        # Find all 4-letter stock codes in the company directory
        for link in soup.find_all('a'):
            text = link.text.strip()
            if len(text) == 4 and text.isupper() and text.isalpha():
                tickers.append(f"{text}.JK")
        
        if len(tickers) > 500:
            return sorted(list(set(tickers)))
    except Exception as e:
        st.warning(f"Live scraping failed, using community backup list...")
    
    # Backup Source: Community maintained GitHub list
    try:
        url_csv = "https://raw.githubusercontent.com/man-c/idx-stocks/master/tickers.csv"
        df_csv = pd.read_csv(url_csv, header=None)
        return sorted([f"{t}.JK" for t in df_csv[0].tolist() if len(str(t)) == 4])
    except:
        return ["BBCA.JK", "BBRI.JK", "TLKM.JK"] # Last resort

# --- STEP 2: BULK ANALYSIS ---
def run_bulk_scan(ticker_list, sens_vol, sens_price):
    """Downloads and processes the whole market in one go (very fast)"""
    st.write(f"⏳ Downloading data for {len(ticker_list)} stocks...")
    
    # Bulk download 1 month of data for everyone
    data = yf.download(ticker_list, period="1mo", interval="1d", group_by='ticker', progress=True)
    
    signals = []
    
    for ticker in ticker_list:
        try:
            # Handle MultiIndex and extract OHLCV
            df = data[ticker].dropna()
            if df.empty or len(df) < 15:
                continue
            
            # 20-Day Volume Average
            df['Vol_Avg'] = df['Volume'].rolling(window=15).mean()
            
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            vol_ratio = last_row['Volume'] / last_row['Vol_Avg']
            price_change = (last_row['Close'] - prev_row['Close']) / prev_row['Close']
            
            # --- BIG PLAYER LOGIC ---
            # Accumulation: Huge volume spike, but price barely moved (Absorption)
            if vol_ratio > sens_vol and abs(price_change) < (sens_price / 100):
                signals.append({
                    "Ticker": ticker.replace(".JK", ""),
                    "Price": round(last_row['Close'], 2),
                    "Change%": round(price_change * 100, 2),
                    "Vol_Ratio": round(vol_ratio, 2),
                    "Phase": "Accumulation 💎",
                    "Sign": "Big player buying hiddenly"
                })
            
            # Markup: Huge volume spike with aggressive price jump
            elif vol_ratio > (sens_vol + 0.5) and price_change > (sens_price / 100):
                signals.append({
                    "Ticker": ticker.replace(".JK", ""),
                    "Price": round(last_row['Close'], 2),
                    "Change%": round(price_change * 100, 2),
                    "Vol_Ratio": round(vol_ratio, 2),
                    "Phase": "Markup 🚀",
                    "Sign": "Aggressive big player buying"
                })
        except:
            continue
            
    return signals

# --- STEP 3: 5% SHAREHOLDER NEWS (ONLY ON DEMAND) ---
def get_news(ticker):
    url = f"https://www.idnfinancials.com/{ticker}/news"
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        headlines = [a.text.strip() for a in soup.find_all('a') if 'kepemilikan' in a.text.lower() or 'shareholder' in a.text.lower()]
        return headlines[:3]
    except:
        return []

# --- UI ---
all_tickers = get_all_idx_tickers()
st.sidebar.header("Scanner Settings")
st.sidebar.write(f"🔍 Monitoring **{len(all_tickers)}** stocks")

sens_vol = st.sidebar.slider("Volume Sensitivity (1.5x is standard)", 1.0, 5.0, 1.8)
sens_price = st.sidebar.slider("Price Sensitivity % (Max movement for Accumulation)", 0.5, 3.0, 1.2)

if st.sidebar.button("🔥 Scan All 900+ Stocks"):
    results = run_bulk_scan(all_tickers, sens_vol, sens_price)
    
    if results:
        st.session_state.results = results
        st.success(f"Scan complete! Found {len(results)} Whale Signatures.")
    else:
        st.session_state.results = []
        st.warning("No significant signatures found. Try lowering Volume Sensitivity.")

# --- DISPLAY RESULTS ---
if 'results' in st.session_state and st.session_state.results:
    df = pd.DataFrame(st.session_state.results).sort_values(by="Vol_Ratio", ascending=False)
    st.dataframe(df, use_container_width=True)
    
    st.subheader("📊 Chart Analysis & Whale News")
    for r in st.session_state.results:
        with st.expander(f"Analysis for {r['Ticker']} (Vol Ratio: {r['Vol_Ratio']}x)"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Show 3 month chart
                c_data = yf.download(f"{r['Ticker']}.JK", period="3mo", progress=False)
                if isinstance(c_data.columns, pd.MultiIndex): c_data.columns = c_data.columns.get_level_values(0)
                fig = go.Figure(data=[go.Candlestick(x=c_data.index, open=c_data['Open'], high=c_data['High'], low=c_data['Low'], close=c_data['Close'])])
                fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,b=0,t=0))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write(f"**Current Status:** {r['Phase']}")
                st.write(f"**Logic:** {r['Sign']}")
                news = get_news(r['Ticker'])
                if news:
                    st.write("**Recent 5% Shareholder News:**")
                    for n in news: st.info(n)
                else:
                    st.write("No recent ownership news found.")

else:
    st.info("Click the 'Scan All Stocks' button in the sidebar to begin. This uses Yahoo Finance bulk-download for speed.")
