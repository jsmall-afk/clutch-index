import streamlit as st
import pandas as pd
import unicodedata

# Keep this! It's the translator you have in your terminal
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', str(s))
                  if unicodedata.category(c) != 'Mn')

# 1. Set up the page
st.set_page_config(page_title="Clutch Index Dashboard", layout="wide")
st.title("⚽ The Clutch Index Dashboard")

# Load your master database
@st.cache_data
def load_data():
    return pd.read_csv('clutch_data_master.csv')

master_df = load_data()

# 2. CREATE TABS
# This creates a menu at the top of the app to flip between views!
tab1, tab2 = st.tabs(["🔍 Player Search", "🏆 Leaderboards"])

# ==========================================
# TAB 1: PLAYER SEARCH & SEASONAL BREAKDOWN
# ==========================================
with tab1:
    st.write("Search for a player to see their underlying shot data.")
    player_search = st.text_input("Enter a player name (e.g., Messi):")

    if player_search:
            # Clean your search text
        search_clean = strip_accents(player_search).replace("'", "").lower().strip()
        
        # Clean the data names while searching
        player_df = master_df[
            master_df['player'].apply(lambda x: strip_accents(x).replace("'", "").lower())
            .str.contains(search_clean, case=False, na=False)
        ]    
        
        if player_df.empty:
            st.warning("No players found. Try checking the spelling!")
        else:
            st.success(f"Found {len(player_df)} shots for {player_search}!")
            
            # --- The Seasonal & Competition Breakdown ---
            st.subheader("📊 Seasonal & Competition Breakdown")
            
            # Group by BOTH season and competition to recreate your terminal hierarchy
            summary_df = player_df.groupby(['season', 'competition']).agg(
                Total_Shots=('outcome', 'count'),
                Goals=('outcome', lambda x: (x == 'Goal').sum()),
                Total_CIS=('CI:S', 'sum'),
                Avg_CIS=('CI:S', 'mean')
            ) 
            # (Note: We do NOT use .reset_index() here because Streamlit formats multi-index groups beautifully!)
            
            summary_df['Total_CIS'] = summary_df['Total_CIS'].round(4)
            summary_df['Avg_CIS'] = summary_df['Avg_CIS'].round(4)
            
            st.dataframe(summary_df, use_container_width=True)

            st.divider()

            # --- Top 10 Shots ---
            st.subheader("🔥 Top 10 Shots by Category")
            
            top_shots = player_df.sort_values(by='CI:S', ascending=False).head(10)
            
            # I added 'competition' into the columns here so you know what tournament the shot was in!
            clean_columns = ['opponent', 'season', 'competition', 'minute', 'score_differential', 'xg', 'outcome', 'CI:S']
            clean_shots_df = top_shots[clean_columns]
            
            st.dataframe(clean_shots_df, use_container_width=True)


# ==========================================
# TAB 2: THE GLOBAL LEADERBOARDS
# ==========================================
with tab2:
    st.header("🏆 Clutch Index Leaderboards")
    st.write("The top performers across the entire database.")
    
    # Define a clean list of columns to use for all our shot-based leaderboards
    shot_cols = ['player', 'team', 'opponent', 'season', 'minute', 'score_differential', 'xg', 'outcome', 'CI:S']
    
    # --- Leaderboard 1: Top 20 Most Clutch Shots (Overall) ---
    st.subheader("🔥 Top 20 Most Clutch Shots")
    top_shots_overall = master_df.sort_values(by='CI:S', ascending=False).head(20)
    clean_top_overall = top_shots_overall[shot_cols].copy()
    clean_top_overall['CI:S'] = clean_top_overall['CI:S'].round(4)
    clean_top_overall.index = range(1, 21)
    st.dataframe(clean_top_overall, use_container_width=True)
    
    st.divider()

    # --- Leaderboard 2: Top 20 Least Clutch Shots ---
    st.subheader("🥶 Top 20 LEAST Clutch Shots")
    least_shots = master_df.sort_values(by='CI:S', ascending=True).head(20)
    clean_least_shots = least_shots[shot_cols].copy()
    # Using scientific notation formatting so we can actually read those tiny numbers!
    clean_least_shots['CI:S'] = clean_least_shots['CI:S'].apply(lambda x: f"{x:.2e}")
    clean_least_shots.index = range(1, 21)
    st.dataframe(clean_least_shots, use_container_width=True)

    st.divider()

    # --- Leaderboard 3: Top 20 Least Clutch Goals ---
    st.subheader("😅 Top 20 LEAST Clutch Goals")
    least_goals = master_df[master_df['outcome'] == 'Goal'].sort_values(by='CI:S', ascending=True).head(20)
    clean_least_goals = least_goals[shot_cols].copy()
    clean_least_goals['CI:S'] = clean_least_goals['CI:S'].round(4)
    clean_least_goals.index = range(1, 21)
    st.dataframe(clean_least_goals, use_container_width=True)

    st.divider()

    # --- Leaderboard 4: Missed Big Chances ---
    st.subheader("🤦‍♂️ Top 20 'Most Clutch' Missed Big Chances (xG >= 0.50)")
    master_df['xg'] = pd.to_numeric(master_df['xg'], errors='coerce')
    missed_chances = master_df[(master_df['xg'] >= 0.50) & (master_df['outcome'] != 'Goal')]
    top_misses = missed_chances.sort_values(by='CI:S', ascending=False).head(20)
    
    if top_misses.empty:
        st.info("No missed big chances found!")
    else:
        clean_misses = top_misses[shot_cols].copy()
        clean_misses['CI:S'] = clean_misses['CI:S'].round(4)
        clean_misses.index = range(1, len(clean_misses) + 1)
        st.dataframe(clean_misses, use_container_width=True)

    st.divider()

    # --- Leaderboard 5: Top 20 Player Seasons (Accumulated) ---
    st.subheader("🥇 Top 20 Most Clutch Seasons (Total CI:S)")
    player_seasons = master_df.groupby(['player', 'team', 'season']).agg(
        total_shots=('outcome', 'count'),
        total_goals=('outcome', lambda x: (x == 'Goal').sum()),
        total_cis=('CI:S', 'sum'),
        avg_cis_per_shot=('CI:S', 'mean')
    ).reset_index()
    
    top_20_seasons = player_seasons.sort_values(by='total_cis', ascending=False).head(20)
    top_20_seasons['total_cis'] = top_20_seasons['total_cis'].round(4)
    top_20_seasons['avg_cis_per_shot'] = top_20_seasons['avg_cis_per_shot'].round(4)
    top_20_seasons.index = range(1, 21)
    st.dataframe(top_20_seasons, use_container_width=True)

    st.divider()

    # --- Leaderboard 6: Most Clutch Players Per Shot (Min 20 Shots) ---
    st.subheader("🎯 Most Clutch Players Per Shot (Min. 20 Shots)")
    # We filter the 'player_seasons' dataframe we just made in the step above!
    efficient_players = player_seasons[player_seasons['total_shots'] >= 20]
    top_efficient = efficient_players.sort_values(by='avg_cis_per_shot', ascending=False).head(20)
    
    top_efficient['total_cis'] = top_efficient['total_cis'].round(4)
    top_efficient['avg_cis_per_shot'] = top_efficient['avg_cis_per_shot'].round(4)
    top_efficient.index = range(1, len(top_efficient) + 1)
    st.dataframe(top_efficient, use_container_width=True)

    #python3 -m streamlit run app.py
