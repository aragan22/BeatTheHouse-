
# BeatTheHouse.py

import streamlit as st
import pandas as pd
from main import (
    fetch_upcoming_events, prepare_fixture_data, prepare_odds_data, recommend_bets, SPORTS_LEAGUES
)

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = 'welcome'


def set_page(page_name):
    st.session_state.page = page_name


def welcome_page():
    st.title("Welcome to Beat The House!")
    st.write("Optimize your sports betting experience with data-driven recommendations.")

    if st.button("Get Started"):
        set_page('betting')


def betting_calculator_page():
    st.title("Betting Calculator")

    st.sidebar.header("Settings")

    try:
        sport_categories = list(SPORTS_LEAGUES.keys())
        selected_sport_category = st.sidebar.selectbox("Select Sport Category", sport_categories)

        leagues = SPORTS_LEAGUES[selected_sport_category]
        league_names = [league['name'] for league in leagues]
        league_keys = [league['key'] for league in leagues]
        selected_league_name = st.sidebar.selectbox("Select League", league_names)
        selected_league_key = league_keys[league_names.index(selected_league_name)]

        available_funds = st.sidebar.number_input("Available Funds ($)", min_value=1.0, value=100.0)
        max_bets = st.sidebar.number_input("Maximum Number of Bets", min_value=1, value=5)

        events = fetch_upcoming_events(selected_league_key)
        if not events:
            st.error("No upcoming events found for the selected league.")
            return

        X_fix = prepare_fixture_data(events)
        O_fix = prepare_odds_data(events)

        if st.sidebar.button("Get Betting Recommendations"):
            recommendations = recommend_bets(X_fix, O_fix, available_funds, max_bets)
            st.write("Betting Recommendations:")
            st.dataframe(recommendations)

    except Exception as e:
        st.error(f"An error occurred: {e}")


def BeatTheHouse():
    if st.session_state.page == 'welcome':
        welcome_page()
    elif st.session_state.page == 'betting':
        betting_calculator_page()


if __name__ == "__main__":
    BeatTheHouse()
