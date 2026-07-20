import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="MLB ML Analyst", layout="wide")
st.title("⚾ Moneyline Relentless Analyst")

api_key = st.secrets["ODDS_API_KEY"]

# 1. Fetch Today's Games
url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=h2h"
games = requests.get(url).json()

# 2. Get Live Power Rankings (JSON source)
# This replaces the manual list with live, updated data
rankings_url = "https://projects.fivethirtyeight.com/mlb-api/mlb_elo_latest.csv"
try:
    df_elo = pd.read_csv(rankings_url)
    # Map team names to Elo rating
    elo_map = dict(zip(df_elo['team_name'], df_elo['elo_rating']))
except:
    # Fallback if source is down
    elo_map = {"Yankees": 1550, "Dodgers": 1580, "Pirates": 1450} 

data = []
for game in games:
    try:
        h, a = game['home_team'], game['away_team']
        dk = next(b for b in game['bookmakers'] if b['key'] == 'draftkings')
        home_price = next(o['price'] for o in dk['markets'][0]['outcomes'] if o['name'] == h)
        
        # Calculate Win Probability based on Elo difference
        h_elo = elo_map.get(h.split()[-1], 1500)
        a_elo = elo_map.get(a.split()[-1], 1500)
        model_prob = 1 / (1 + 10 ** ((a_elo - h_elo) / 400))
        
        implied_prob = 1 / home_price if home_price > 2 else (home_price - 1) / home_price
        
        data.append({"Matchup": f"{a} @ {h}", "Edge": round((model_prob - implied_prob) * 100, 1)})
    except: continue

st.dataframe(pd.DataFrame(data).sort_values(by="Edge", ascending=False), use_container_width=True)
