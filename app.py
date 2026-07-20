import streamlit as st
import pandas as pd
import requests
from pybaseball import team_batting

st.set_page_config(page_title="MLB ML Analyst", layout="wide")
st.title("⚾ Moneyline Relentless Analyst")

try:
    api_key = st.secrets["ODDS_API_KEY"]
except:
    st.error("Missing API Key. Go to Settings > Secrets in Streamlit Cloud and add 'ODDS_API_KEY'.")
    st.stop()

@st.cache_data(ttl=3600)
def get_stats():
    return team_batting(2026)[['Team', 'wRC+']]

batting_df = get_stats()
url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={api_key}&regions=us&markets=h2h"
response = requests.get(url).json()

data = []
for game in response:
    try:
        h, a = game['home_team'], game['away_team']
        dk = next(b for b in game['bookmakers'] if b['key'] == 'draftkings')
        home_price = next(o['price'] for o in dk['markets'][0]['outcomes'] if o['name'] == h)
        h_wrc = batting_df.loc[batting_df['Team'] == h, 'wRC+'].values[0]
        a_wrc = batting_df.loc[batting_df['Team'] == a, 'wRC+'].values[0]
        model_win_prob = 0.50 + ((h_wrc - a_wrc) / 1000)
        implied_prob = 1 / home_price if home_price > 2 else (home_price - 1) / home_price
        data.append({"Matchup": f"{a} @ {h}", "Edge": round((model_win_prob - implied_prob) * 100, 1)})
    except: continue

st.dataframe(pd.DataFrame(data).sort_values(by="Edge", ascending=False), use_container_width=True)
