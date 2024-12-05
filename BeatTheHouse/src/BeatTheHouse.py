# BeatTheHouse.py

import streamlit as st
import pandas as pd
from main import (
    display_current_odds_df, fetch_upcoming_events,
    prepare_fixture_data, prepare_odds_data, recommend_bets, SPORTS_LEAGUES
)

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = 'welcome'


def set_page(page_name):
    st.session_state.page = page_name


def welcome_page():
    """Displays the welcome page."""
    st.markdown(
        """
        <style>
        .center {
            text-align: center;
        }
        .orange {
            color: #FF6600;
            font-size: 90px;
            font-weight: bold;
        }
        .blue {
            color: #0066FF;
            font-size: 50px;
        }
        .button {
            background-color: #FF6600;
            color: white;
            padding: 20px 40px;
            font-size: 20px;
            font-weight: bold;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<h1 class='center orange'>Welcome To Beat The House</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='center blue'>Authors:</h3>", unsafe_allow_html=True)
    st.markdown("<p class='center'>Aidan Ragan, Gabriel Bendix, Jorge Hernandez</p>", unsafe_allow_html=True)

    if st.button("Get Started", key="start_button"):
        set_page('betting')


def betting_calculator_page():
    """Displays the betting calculator interface."""
    st.markdown(
        """
        <style>
        .header {
            color: #FF6600;
            font-size: 50px;
            font-weight: bold;
        }
        .subheader {
            color: #0066FF;
            font-size: 30px;
            font-weight: bold;
        }
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #FF6600;
            color: white;
            text-align: center;
            padding: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<h2 class='header'>Betting Calculator</h2>", unsafe_allow_html=True)

    st.sidebar.header("🔧 Settings")

    try:
        # Step 1: Select Sport Category
        st.sidebar.subheader("1. Select Sport Category")
        sport_categories = list(SPORTS_LEAGUES.keys())
        selected_sport_category = st.sidebar.selectbox("", sport_categories)

        # Step 2: Select League within the Sport Category
        st.sidebar.subheader("2. Select League")
        leagues = SPORTS_LEAGUES[selected_sport_category]
        league_names = [league['name'] for league in leagues]
        league_keys = [league['key'] for league in leagues]
        selected_league_name = st.sidebar.selectbox("", league_names)
        selected_league_key = league_keys[league_names.index(selected_league_name)]

        # Step 3: View Current Game Odds
        st.sidebar.subheader("3. Options")
        view_odds = st.sidebar.checkbox("👁️ View Current Game Odds")

        # Step 4: User Inputs for Betting
        st.sidebar.subheader("4. Betting Parameters")
        available_funds = st.sidebar.number_input("💰 Available Funds ($)", min_value=1.0, step=10.0, value=100.0)
        max_bets = st.sidebar.number_input("🎯 Maximum Number of Bets", min_value=1, step=1, value=10)

        # Fetch Events and Odds based on selected league
        try:
            events = fetch_upcoming_events(selected_league_key)
            if not events:
                st.error("🚫 No upcoming events found for the selected league.")
                return

            X_fix = prepare_fixture_data(events)
            O_fix = prepare_odds_data(events)
        except Exception as e:
            st.error("An error occurred while fetching or preparing event data. Please try again later.")
            return

        # Display Current Odds if selected
        if view_odds:
            st.markdown("<h3 class='subheader'>📊 Current Game Odds</h3>", unsafe_allow_html=True)
            st.markdown(f"**Sport Category:** {selected_sport_category}")
            st.markdown(f"**League:** {selected_league_name}")

            try:
                # Get unique bookmakers
                bookmakers = O_fix.reset_index()['bookmaker'].unique()

                if len(bookmakers) == 0:
                    st.info("ℹ️ No bookmakers available for this league.")
                else:
                    for bookmaker in sorted(bookmakers):
                        with st.expander(f"**{bookmaker.capitalize()}**"):
                            bookmaker_odds = O_fix.reset_index()
                            bookmaker_odds = bookmaker_odds[bookmaker_odds['bookmaker'] == bookmaker]

                            if bookmaker_odds.empty:
                                st.write("No odds available.")
                            else:
                                display_odds = bookmaker_odds[
                                    ['date', 'home_team', 'away_team', 'home_win', 'draw', 'away_win']
                                ]

                                display_odds = display_odds.rename(columns={
                                    'date': 'Date',
                                    'home_team': 'Home Team',
                                    'away_team': 'Away Team',
                                    'home_win': 'Home Win Odds',
                                    'draw': 'Draw Odds',
                                    'away_win': 'Away Win Odds'
                                })

                                st.dataframe(display_odds)
            except Exception:
                st.error("An error occurred while displaying odds. Please try again later.")

        # Button to Get Recommendations
        if st.sidebar.button("📈 Get Betting Recommendations"):
            with st.spinner('Generating recommendations...'):
                try:
                    recommendations = recommend_bets(X_fix, O_fix, available_funds, max_bets)

                    current_bets = recommendations.get('current_bets', [])
                    if current_bets:
                        st.markdown("---")
                        st.markdown("<h3 class='subheader'>Recommended Bets Based on Current Odds</h3>", unsafe_allow_html=True)
                        for bet in current_bets:
                            with st.expander(f"{bet['home_team']} vs {bet['away_team']} on {bet['date'].date()}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"**Bet:** {bet['bet_description']}")
                                    st.markdown(f"**Bookmaker:** {bet.get('bookmaker', 'N/A')}")
                                with col2:
                                    st.markdown(f"**Odds:** {bet['odds']}")
                                    st.markdown(f"**Recommended Stake:** ${bet['stake']:.2f}")
                    else:
                        st.info("ℹ️ No current odds-based bets to recommend.")
                except Exception:
                    st.error("An error occurred while generating recommendations. Please try again later.")
    except Exception:
        st.error("An unexpected error occurred. Please restart the application.")

    # Add a footer
    st.markdown(
        """
        <div class="footer">
            <p>© 2024 Beat The House. All rights reserved.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def BeatTheHouse():
    if st.session_state.page == 'welcome':
        welcome_page()
    elif st.session_state.page == 'betting':
        betting_calculator_page()


if __name__ == "__main__":
    BeatTheHouse()
