# main.py

import os
import requests
import pandas as pd
pd.options.mode.chained_assignment = None  # Suppress SettingWithCopyWarning
import numpy as np
from datetime import datetime
import logging

# Fuzzy matching libraries
from thefuzz import fuzz
from thefuzz import process

# Environment variables and request handling
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='betting_recommendation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# API key for Odds API
ODDS_API_KEY = '6e50e3b0da68259e7c526ebe4f9409c3'  
if not ODDS_API_KEY:
    logging.error("No ODDS_API_KEY found in environment variables.")
    raise ValueError("No ODDS_API_KEY found in environment variables.")

# Define the sport to leagues mapping
SPORTS_LEAGUES = {
    "American Football": [
        {"name": "NCAAF", "key": "americanfootball_ncaaf"},
        {"name": "NCAAF Championship Winner", "key": "americanfootball_ncaaf_championship_winner"},
        {"name": "NFL", "key": "americanfootball_nfl"},
        {"name": "NFL Super Bowl Winner", "key": "americanfootball_nfl_super_bowl_winner"},
    ],
    "Aussie Rules Football": [
        {"name": "AFL", "key": "aussierules_afl"},
    ],
    "Baseball": [
        {"name": "MLB World Series Winner", "key": "baseball_mlb_world_series_winner"},
    ],
    "Basketball": [
        {"name": "Basketball Euroleague", "key": "basketball_euroleague"},
        {"name": "NBA", "key": "basketball_nba"},
        {"name": "NBA Championship Winner", "key": "basketball_nba_championship_winner"},
        {"name": "NBL", "key": "basketball_nbl"},
        {"name": "NCAAB", "key": "basketball_ncaab"},
        {"name": "NCAAB Championship Winner", "key": "basketball_ncaab_championship_winner"},
    ],
    "Boxing": [
        {"name": "Boxing", "key": "boxing_boxing"},
    ],
    "Cricket": [
        {"name": "Big Bash", "key": "cricket_big_bash"},
        {"name": "International Twenty20", "key": "cricket_international_t20"},
        {"name": "Test Matches", "key": "cricket_test_match"},
    ],
    "Golf": [
        {"name": "Masters Tournament Winner", "key": "golf_masters_tournament_winner"},
        {"name": "PGA Championship Winner", "key": "golf_pga_championship_winner"},
        {"name": "The Open Winner", "key": "golf_the_open_championship_winner"},
        {"name": "US Open Winner", "key": "golf_us_open_winner"},
    ],
    "Ice Hockey": [
        {"name": "NHL", "key": "icehockey_nhl"},
        {"name": "NHL Championship Winner", "key": "icehockey_nhl_championship_winner"},
        {"name": "HockeyAllsvenskan", "key": "icehockey_sweden_allsvenskan"},
        {"name": "SHL", "key": "icehockey_sweden_hockey_league"},
    ],
    "MMA": [
        {"name": "MMA", "key": "mma_mixed_martial_arts"},
    ],
    "Rugby League": [
        {"name": "NRL", "key": "rugbyleague_nrl"},
    ],
    "Soccer": [
        {"name": "Primera División - Argentina", "key": "soccer_argentina_primera_division"},
        {"name": "A-League", "key": "soccer_australia_aleague"},
        {"name": "Austrian Football Bundesliga", "key": "soccer_austria_bundesliga"},
        {"name": "Belgium First Div", "key": "soccer_belgium_first_div"},
        {"name": "Brazil Série A", "key": "soccer_brazil_campeonato"},
        {"name": "Championship", "key": "soccer_efl_champ"},
        {"name": "EFL Cup", "key": "soccer_england_efl_cup"},
        {"name": "League 1", "key": "soccer_england_league1"},
        {"name": "League 2", "key": "soccer_england_league2"},
        {"name": "EPL", "key": "soccer_epl"},
        {"name": "FA Cup", "key": "soccer_fa_cup"},
        {"name": "FIFA World Cup Winner", "key": "soccer_fifa_world_cup_winner"},
        {"name": "Ligue 1 - France", "key": "soccer_france_ligue_one"},
        {"name": "Ligue 2 - France", "key": "soccer_france_ligue_two"},
        {"name": "Bundesliga - Germany", "key": "soccer_germany_bundesliga"},
        {"name": "Bundesliga 2 - Germany", "key": "soccer_germany_bundesliga2"},
        {"name": "3. Liga - Germany", "key": "soccer_germany_liga3"},
        {"name": "Super League - Greece", "key": "soccer_greece_super_league"},
        {"name": "Serie A - Italy", "key": "soccer_italy_serie_a"},
        {"name": "Serie B - Italy", "key": "soccer_italy_serie_b"},
        {"name": "J League", "key": "soccer_japan_j_league"},
        {"name": "K League 1", "key": "soccer_korea_kleague1"},
        {"name": "League of Ireland", "key": "soccer_league_of_ireland"},
        {"name": "Liga MX", "key": "soccer_mexico_ligamx"},
        {"name": "Dutch Eredivisie", "key": "soccer_netherlands_eredivisie"},
        {"name": "Ekstraklasa - Poland", "key": "soccer_poland_ekstraklasa"},
        {"name": "Primeira Liga - Portugal", "key": "soccer_portugal_primeira_liga"},
        {"name": "La Liga - Spain", "key": "soccer_spain_la_liga"},
        {"name": "La Liga 2 - Spain", "key": "soccer_spain_segunda_division"},
        {"name": "Premiership - Scotland", "key": "soccer_spl"},
        {"name": "Swiss Superleague", "key": "soccer_switzerland_superleague"},
        {"name": "Turkey Super League", "key": "soccer_turkey_super_league"},
        {"name": "UEFA Champions League", "key": "soccer_uefa_champs_league"},
        {"name": "MLS", "key": "soccer_usa_mls"},
    ],
}

def fetch_upcoming_events(sport_key):
    """Retrieves upcoming events and their odds for the selected sport."""
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us,uk,eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal',
        'dateFormat': 'iso',
    }

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    response = session.get(url, params=params)
    if response.status_code == 200:
        events = response.json()
        logging.info(f"Fetched {len(events)} events for {sport_key}.")
        return events
    else:
        logging.error(f"Error fetching events: {response.status_code} - {response.text}")
        return []

def prepare_fixture_data(events):
    """Formats fixture data from events."""
    fixtures = [{
        'sport': event.get('sport_title', ''),
        'home_team': event['home_team'],
        'away_team': event['away_team'],
        'date': pd.to_datetime(event['commence_time']).date(),
    } for event in events]
    X_fix = pd.DataFrame(fixtures)
    X_fix['date'] = pd.to_datetime(X_fix['date'])
    return X_fix

def prepare_odds_data(events):
    """Formats odds data from events."""
    odds_records = []
    for event in events:
        home_team = event['home_team']
        away_team = event['away_team']
        date = pd.to_datetime(event['commence_time']).date()
        for bookmaker in event.get('bookmakers', []):
            bookmaker_key = bookmaker['key']
            last_update = bookmaker['last_update']
            for market in bookmaker.get('markets', []):
                if market['key'] == 'h2h':
                    outcomes = market['outcomes']
                    record = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'bookmaker': bookmaker_key,
                        'last_update': last_update,
                        'date': date,
                    }
                    for outcome in outcomes:
                        if outcome['name'] == home_team:
                            record['home_win'] = outcome['price']
                        elif outcome['name'] == away_team:
                            record['away_win'] = outcome['price']
                        elif outcome['name'].lower() == 'draw':
                            record['draw'] = outcome['price']
                    odds_records.append(record)
    O_fix = pd.DataFrame(odds_records)
    O_fix['date'] = pd.to_datetime(O_fix['date'])
    O_fix.set_index(['date', 'home_team', 'away_team'], inplace=True)
    O_fix.sort_index(inplace=True)
    return O_fix

def calculate_implied_probability(odds):
    """Calculates implied probability from odds."""
    return 1 / odds if odds > 0 else 0

def map_market(row):
    """Creates a bet description based on the market."""
    if row['market'] == 'home_win':
        return f"Bet on {row['home_team']} to win"
    elif row['market'] == 'away_win':
        return f"Bet on {row['away_team']} to win"
    elif row['market'] == 'draw':
        return "Bet on a Draw"
    return "Unknown Bet"

def recommend_bets_based_on_current_odds(O_fix, total_funds, max_bets):
    """Generates bet recommendations based on current odds."""
    O_flat = O_fix.reset_index()
    O_melted = O_flat.melt(id_vars=['date', 'home_team', 'away_team', 'bookmaker', 'last_update'],
                           value_vars=['home_win', 'draw', 'away_win'],
                           var_name='market',
                           value_name='odds')
    O_melted.dropna(subset=['odds'], inplace=True)
    O_sorted = O_melted.sort_values(by='odds', ascending=True)

    unique_games = []
    top_bets = []

    for _, row in O_sorted.iterrows():
        game = (row['date'], row['home_team'], row['away_team'])
        if game not in unique_games:
            unique_games.append(game)
            top_bets.append(row)
            if len(top_bets) == max_bets:
                break

    if len(top_bets) < max_bets:
        logging.warning(f"Only {len(top_bets)} unique games available.")
        print(f"\nOnly {len(top_bets)} unique games are available for betting out of the requested {max_bets} bets.")
        print("Consider selecting another sport or reducing the number of bets.")
        return top_bets

    top_bets_df = pd.DataFrame(top_bets)
    total_odds = top_bets_df['odds'].sum()

    if total_odds == 0:
        logging.warning("No valid odds to recommend.")
        return []

    top_bets_df['stake'] = (top_bets_df['odds'] / total_odds) * total_funds
    top_bets_df['stake'] = top_bets_df['stake'].round(2)
    total_allocated = top_bets_df['stake'].sum()
    difference = round(total_funds - total_allocated, 2)
    if not np.isclose(difference, 0):
        top_bets_df.at[top_bets_df.index[-1], 'stake'] += difference

    top_bets_df['bet_description'] = top_bets_df.apply(map_market, axis=1)
    return top_bets_df.to_dict('records')

def recommend_bets(X_fix, O_fix, available_funds, max_bets):
    """Provides bet recommendations based on current odds."""
    # Current odds-based bets
    current_bets = recommend_bets_based_on_current_odds(O_fix, available_funds, max_bets)

    return {
        'current_bets': current_bets
    }

def display_current_odds_df(X_fix, O_fix):
    """Returns a DataFrame showing the current odds for upcoming events."""
    odds_list = []
    for _, row in X_fix.iterrows():
        date = row['date']
        home = row['home_team']
        away = row['away_team']
        try:
            odds = O_fix.loc[(row['date'], home, away)]
            if isinstance(odds, pd.Series):
                odds = pd.DataFrame([odds])
            for _, info in odds.iterrows():
                bet = {
                    'Date': date,
                    'Match': f"{home} vs {away}",
                    'Bookmaker': info.get('bookmaker', 'N/A'),
                    'Home Win Odds': info.get('home_win', 'N/A'),
                    'Draw Odds': info.get('draw', 'N/A') if 'draw' in info else 'N/A',
                    'Away Win Odds': info.get('away_win', 'N/A'),
                }
                odds_list.append(bet)
        except KeyError:
            bet = {
                'Date': date,
                'Match': f"{home} vs {away}",
                'Bookmaker': 'N/A',
                'Home Win Odds': 'N/A',
                'Draw Odds': 'N/A',
                'Away Win Odds': 'N/A',
            }
            odds_list.append(bet)
    return pd.DataFrame(odds_list)

def main():
    """Runs the betting recommendation workflow."""
    # This main function remains for command-line usage
    import sys

    # Check if running as a script with 'cli' argument
    if len(sys.argv) > 1 and sys.argv[1] == 'cli':
        # Implement command-line interface here if needed
        pass
    else:
        # Prevent automatic execution when imported
        pass

if __name__ == "__main__":
    main()
