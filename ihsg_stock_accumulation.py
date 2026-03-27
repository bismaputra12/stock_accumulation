import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor
import time

# --- APP CONFIG ---
st.set_page_config(page_title="IDX Whale Hunter: Diagnostic Edition", layout="wide")
st.title("🐋 IDX Whale Hunter (Diagnostics Active)")

# --- STEP 1: THE FULL LIST (942 STOCKS) ---
def get_master_list():
    return [
        "AALI","ABBA","ABDA","ABMM","ACES","ACST","ADCP","ADHI","ADMF","ADMR","ADRO","AGII","AGRO","AGRS","AHAP","AISA","AKRA","AKSI","ALDO","ALKA","ALMI","ALPN","AMAG","AMAR","AMFG","AMIN","AMMS","AMOR","AMRT","ANDI","ANJT","ANTM","APEX","APIC","APLI","APLN","ARCI","ARGO","ARII","ARKA","ARKO","ARNA","ARTA","ARTO","ASBI","ASCL","ASDM","ASGR","ASII","ASJT","ASMI","ASPI","ASRI","ASSA","ATAU","ATIC","AUTO","AVIA","AYLS","BACA","BAJA","BALI","BANK","BAPA","BAPI","BATA","BATP","BAUT","BBCA","BBHI","BBKP","BBLD","BBMD","BBNI","BBRI","BBSW","BBTN","BBYB","BCAP","BCIC","BCIP","BDMN","BEBS","BEEF","BEER","BELI","BESS","BEST","BFIN","BGTG","BHIT","BIKA","BINA","BIPI","BIPP","BIRD","BISI","BKDP","BKSL","BKSW","BLTZ","BLUE","BMAS","BMRI","BMTR","BNBA","BNGA","BNII","BNLI","BOLA","BPII","BPTR","BRAM","BRIS","BRMS","BRNA","BRPT","BSDE","BSIM","BSML","BSSR","BSSR","BTEK","BTPS","BTSR","BUKA","BULL","BUMI","BUVA","BVIC","BWPT","BYAN","CARS","CASH","CASS","CEKA","CENT","CFIN","CINT","CITA","CITY","CLAY","CLEO","CLPI","CMNP","CMNT","CNKO","CNMA","CNTX","COCO","CPIN","CPRI","CPRO","CSAP","CSIS","CSRA","CTBN","CTRA","CTTH","CUAN","DART","DAYA","DEAL","DEFI","DEWA","DFAM","DGIK","DGNS","DIGI","DILD","DIVA","DKFT","DLTA","DMMX","DMND","DNAA","DNAR","DNET","DOID","DPNS","DPUM","DRMA","DSFI","DSNG","DSSA","DUTI","DVLA","DWGL","DYAN","EAST","ECII","EKAD","ELIT","ELPI","ELSA","EMTK","ENRG","EPMT","ERAA","ERTX","ESIP","ESSA","ESTA","ESTI","ETWA","EXCL","FAPA","FAST","FASW","FILM","FIMP","FIRE","FISH","FITT","FLMC","FMII","FORU","FPNI","FREN","FUJI","GAMA","GDST","GDYR","GEMA","GEMS","GGRM","GIBAS","GJTL","GLOB","GLVA","GMCW","GMTD","GOLD","GOLL","GOTO","GPRA","GRIA","GRIV","GRPM","GSPT","GTBO","GWSA","GZRE","HADE","HDFA","HDIT","HEAL","HELI","HERO","HEXA","HFEV","HITS","HMSP","HOKI","HOME","HOPE","HOTL","HRTA","HRUM","IATA","IBFN","IBOS","ICBP","ICON","IDPR","IFII","IFSH","IGAR","IIKP","IKAI","IKAN","IKBI","IMAS","IMJS","IMPC","INAF","INAI","INCF","INCO","INDF","INDO","INDS","INDX","INDY","INKP","INPC","INPP","INPS","INRU","INTA","INTD","INTP","IPCC","IPCM","IPPE","IPTV","IRRA","ISAT","ISIG","ISSUR","ITIC","ITMA","ITMG","JECC","JGLE","JIHD","JKON","JKSW","JMAS","JPFA","JRPT","JSMR","JSPT","JTPE","KAEF","KARY","KAST","KAYU","KBAG","KBLI","KBLM","KBLV","KBRE","KDSI","KEEN","KEJU","KIAS","KICI","KIJA","KINO","KIOS","KJEN","KKGI","KLBF","KLAS","KMDS","KMTR","KOBX","KOIN","KOKA","KOKI","KONI","KOPI","KOTA","KPAS","KPIG","KRAH","KRAS","KREN","LABA","LCAS","LIFE","LION","LPCK","LPGI","LPIN","LPKR","LPPF","LPPS","LRNA","LSIP","LUCY","MAIN","MAMI","MAPA","MAPB","MAPI","MARI","MARK","MASA","MAYA","MBAP","MBMA","MBSS","MBTO","MCAS","MCEI","MCOR","MDIA","MDKA","MDKI","MDLN","MDRN","MEDC","MEGA","MERK","METI","METR","MFIN","MFMI","MGNA","MGTR","MIKA","MIRA","MITI","MKNT","MKPI","MLBI","MLIA","MLPL","MLPT","MNCN","MPMX","MPPA","MPRO","MRAT","MREI","MSKY","MTDL","MTEL","MTFN","MTLA","MTMH","MTPS","MTRN","MTWI","MYOR","MYTX","NANO","NASA","NATW","NAYK","NBON","NCKL","NELY","NETV","NFCX","NICK","NIRO","NISP","NOBU","NRCA","NREI","NTAS","NZIA","OASA","OBMD","OCAP","OKAS","OMRE","OPMS","PADI","PALM","PANB","PANI","PANR","PANS","PBID","PBRX","PBSA","PCAR","PDES","PEGE","PEHA","PGAS","PGEO","PGUN","PICO","PJAA","PKPK","PLIN","PMJS","PMMP","PNBS","PNIN","PNLF","PNSE","POLI","POLL","POLU","POLY","POOL","PORT","POWR","PPGL","PPRO","PRAS","PRDA","PRIM","PSAB","PSDN","PSGO","PSKT","PSSI","PTBA","PTDU","PTIS","PTPW","PTRO","PTSN","PTSP","PUDP","PURA","PURE","PURI","PWON","PYFA","RAJA","RAKK","RALS","RANC","RBMS","RCCC","RELI","RICY","RIGS","RIMO","RISE","RMBA","RMKE","RODA","ROLY","RONY","ROTI","SAFE","SAME","SAMF","SAMI","SAMP","SAPX","SATU","SBAT","SCCO","SCMA","SCNP","SDMU","SDPC","SEMA","SGER","SGRO","SHID","SHIP","SIAP","SIER","SILO","SIMA","SIMP","SINI","SIPD","SKBM","SKLT","SKYB","SLIS","SMAR","SMBR","SMCB","SMDM","SMDR","SMGR","SMMA","SMMT","SMRA","SMSM","SNLK","SOHO","SONA","SOSS","SOTS","SPMA","SPOT","SPTO","SQMI","SRAJ","SRIL","SRSN","SRTG","SSIA","SSMS","SSTM","STAA","STTP","SUGI","SULI","SUMI","SUNU","SUPR","SURE","SURF","SWAT","TAMA","TAMU","TAPG","TARA","TAXI","TBIG","TBLA","TBMS","TCID","TCPI","TEBE","TECH","TELE","TFAS","TFCO","TGKA","TGRA","TIFA","TINS","TIRA","TIRT","TKIM","TLKM","TMAS","TMPO","TNCA","TOBA","TOTO","TOWR","TPIA","TPMA","TRAM","TRGU","TRIL","TRIM","TRIN","TRIS","TRJA","TRST","TRUE","TRUK","TRUS","TSPC","TUGU","TURI","UCID","UDNG","UFOE","ULTJ","UNIC","UNIT","UNTR","UNVR","URBN","UVCR","VICI","VICO","VINS","VIVA","VOKI","VOSS","VRNA","WAPO","WEGE","WEHA","WGSH","WICO","WIFI","WIIM","WIKA","WINS","WIRG","WJKT","WOMF","WOOD","WSBP","WSKT","WTON","YELO","YPAS","ZATA","ZBRA","ZINC"
    ]

# --- STEP 2: REWRITTEN ANALYSIS ENGINE ---
def analyze_stock(ticker, sens_vol, sens_price):
    symbol = f"{ticker}.JK"
    try:
        # Download 22 days of data
        df = yf.download(symbol, period="1mo", interval="1d", progress=False, show_errors=False)
        
        # Robust column flattening
        if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1:
            df.columns = df.columns.get_level_values(0)
        
        df = df.dropna()
        if len(df) < 5: return None

        # Data extraction using iloc to ensure we hit the last row
        last_close = float(df['Close'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2])
        last_vol = float(df['Volume'].iloc[-1])
        
        # Calculate 20-day Average Volume
        vol_avg = df['Volume'].rolling(window=min(len(df), 20)).mean().iloc[-1]
        
        if vol_avg == 0: return None

        vol_ratio = last_vol / vol_avg
        price_change = ((last_close - prev_close) / prev_close) * 100

        # DIAGNOSTIC LOGIC: Capture anything even slightly interesting
        if vol_ratio > sens_vol:
            if abs(price_change) <= sens_price:
                return {"Ticker": ticker, "Price": last_close, "Change%": round(price_change, 2), "Vol_Ratio": round(vol_ratio, 2), "Type": "Accumulation 💎"}
            elif price_change > 0:
                return {"Ticker": ticker, "Price": last_close, "Change%": round(price_change, 2), "Vol_Ratio": round(vol_ratio, 2), "Type": "Aggressive Buy 🚀"}
            
        return None
    except Exception as e:
        return None

# --- UI CONTROLS ---
tickers = get_master_list()
st.sidebar.success(f"Database: {len(tickers)} Stocks")

# Looser default settings to ensure we see SOMETHING
sens_vol = st.sidebar.slider("Volume Sensitivity (1.0 = Average)", 0.5, 3.0, 1.0)
sens_price = st.sidebar.slider("Price Stability Limit %", 0.5, 5.0, 2.0)

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []

if st.sidebar.button("🔍 START FULL MARKET SCAN"):
    st.session_state.scan_results = []
    progress_bar = st.progress(0)
    status_msg = st.empty()
    live_feed = st.empty()
    
    found_count = 0
    
    # Using 30 threads for speed
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(analyze_stock, t, sens_vol, sens_price): t for t in tickers}
        
        for i, future in enumerate(futures):
            res = future.result()
            if res:
                s
