
import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
if not ODDS_API_KEY:
    raise ValueError("No ODDS_API_KEY found in environment variables.")

SPORTS_LEAGUES = {
    "Soccer": [{"name": "EPL", "key": "soccer_epl"}]
}

def fetch_upcoming_events(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {'apiKey': ODDS_API_KEY, 'regions': 'us', 'markets': 'h2h'}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return []

def prepare_fixture_data(events):
    fixtures = [{'sport': event.get('sport_title', ''),
                 'home_team': event['home_team'],
                 'away_team': event['away_team'],
                 'date': pd.to_datetime(event['commence_time']).date()}
                for event in events]
    return pd.DataFrame(fixtures)

def prepare_odds_data(events):
    odds_records = []
    for event in events:
        home_team = event['home_team']
        away_team = event['away_team']
        date = pd.to_datetime(event['commence_time']).date()
        for bookmaker in event.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market['key'] == 'h2h':
                    outcomes = market['outcomes']
                    record = {'home_team': home_team, 'away_team': away_team, 'date': date}
                    for outcome in outcomes:
                        if outcome['name'] == home_team:
                            record['home_win'] = outcome['price']
                        elif outcome['name'] == away_team:
                            record['away_win'] = outcome['price']
                        elif outcome['name'].lower() == 'draw':
                            record['draw'] = outcome['price']
                    odds_records.append(record)
    return pd.DataFrame(odds_records)

def recommend_bets(X_fix, O_fix, funds, max_bets):
    O_flat = O_fix.reset_index()
    O_melted = O_flat.melt(id_vars=['date', 'home_team', 'away_team'],
                           value_vars=['home_win', 'draw', 'away_win'],
                           var_name='market', value_name='odds')
    O_melted.dropna(subset=['odds'], inplace=True)
    O_sorted = O_melted.sort_values(by='odds', ascending=True)
    recommendations = O_sorted.head(max_bets)
    recommendations['stake'] = funds / max_bets
    return recommendations

