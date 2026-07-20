import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Relentless Analyst", layout="wide")
st.title("⚾ Moneyline Relentless Analyst: Auto-Updating")

api_key = st.secrets["ODDS_API_KEY"]

# --- 1. AUTOMATED DATA FETCHING ---
@st.cache_data(ttl=86400) # Updates once every 24 hours
def get_live_elo():
    # Public CSV source for daily MLB Elo ratings
    url = "https://datahub.io/fivethirtyeight/mlb-elo/r/data/mlb_elo.csv"
    df = pd.read_csv(url)
    # Filter for the most recent ratings
    latest = df.sort_values("date").groupby("team1").tail(1)
    # Return mapping: {"Yankees": 1550, ...}
    return dict(zip(latest['team1'], latest['elo1_pre']))

@st.cache_data(ttl=3600)
def fetch_odds():
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=h2h"
    return requests.get(url).json()

# --- 2. LOGIC ---
elo_map = get_live_elo()
games = fetch_odds()
data = []

for g in games:
    try:
        h, a = g['home_team'], g['away_team']
        dk = next(b for b in g['bookmakers'] if b['key'] == 'draftkings')
        price = next(o['price'] for o in dk['markets'][0]['outcomes'] if o['name'] == h)
        
        # Elo math (default to 1500 if team not found)
        h_elo = elo_map.get(h, 1500)
        a_elo = elo_map.get(a, 1500)
        
        model_prob = 1 / (1 + 10 ** ((a_elo - h_elo) / 400))
        implied = 1/price if price > 2 else (price-1)/price
        
        edge = (model_prob - implied) * 100
        best_side = h if edge > 0 else a
        
        data.append({"Matchup": f"{a} @ {h}", "Best Side": best_side, "Edge": round(abs(edge), 1)})
    except: continue

# --- 3. DISPLAY ---
df = pd.DataFrame(data).sort_values("Edge", ascending=False)
st.subheader("🎯 Automated Daily Value Report")
st.dataframe(df, use_container_width=True, hide_index=True)

if not df.empty:
    top = df.iloc[0]
    rec = "MAX CONFIDENCE" if top['Edge'] > 4.0 else "CALCULATED RISK"
    st.success(f"### Top Play: {top['Best Side']} ({top['Edge']}% Edge)")
    st.write(f"Status: {rec} | Always verify starting pitchers before betting.")
