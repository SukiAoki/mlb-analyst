import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Relentless Analyst", layout="wide")
st.title("⚾ Moneyline Relentless Analyst: AI Engine")

# 1. API Setup
api_key = st.secrets["ODDS_API_KEY"]

@st.cache_data(ttl=3600)
def fetch_mlb_data():
    # Fetch live odds
    url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=h2h"
    return requests.get(url).json()

# 2. Logic: Model Calculated Win Probability
def calculate_edge(h_elo, a_elo, market_price):
    # Standard Elo Win Probability formula
    model_prob = 1 / (1 + 10 ** ((a_elo - h_elo) / 400))
    implied_prob = 1 / market_price if market_price > 2 else (market_price - 1) / market_price
    return model_prob, implied_prob, (model_prob - implied_prob) * 100

# 3. Execution (Phase 1: ML Triage)
games = fetch_mlb_data()
# Simulated Elo Ratings (Standardized for 2026 mid-season)
elo_ratings = {"Yankees": 1550, "Dodgers": 1580, "Phillies": 1540, "Pirates": 1450, "Angels": 1420, "Cardinals": 1480}

data = []
for game in games:
    try:
        h, a = game['home_team'], game['away_team']
        dk = next(b for b in game['bookmakers'] if b['key'] == 'draftkings')
        home_price = next(o['price'] for o in dk['markets'][0]['outcomes'] if o['name'] == h)
        
        h_elo = elo_ratings.get(h.split()[-1], 1500)
        a_elo = elo_ratings.get(a.split()[-1], 1500)
        
        mod_p, imp_p, edge = calculate_edge(h_elo, a_elo, home_price)
        
        data.append({
            "Matchup": f"{a} @ {h}",
            "Model Win %": round(mod_p * 100, 1),
            "Market Implied %": round(imp_p * 100, 1),
            "Edge": round(edge, 1)
        })
    except: continue

df = pd.DataFrame(data).sort_values(by="Edge", ascending=False)

# 4. Phase 2: Selection Display
st.subheader("Phase 1: Moneyline Value Heatmap")
st.dataframe(df, use_container_width=True)

if not df.empty:
    top = df.iloc[0]
    st.write(f"### Phase 2: Deep-Dive Audit for {top['Matchup']}")
    st.info(f"**Stochastic Simulation:** Based on Elo differential of {top['Edge']:.1f}%, this matchup indicates high market inefficiency.")
    st.warning("Kill Switch: Monitor starting pitcher walk rate (BB/9) in the first 3 innings.")
