# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dutchess DairyBoys Analytics", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('data/processed/merged_stats.csv')
    df['scraped_at'] = pd.to_datetime(df['scraped_at'])
    df['game_date'] = pd.to_datetime(df['timestamp'], unit='s')
    return df

df = load_data()

# Helper functions
def get_team_record(data):
    """Calculate team record based on score comparison"""
    games = data.groupby('match_id').agg({
        'score': 'first',
        'opponent_score': 'first'
    })
    wins = (games['score'] > games['opponent_score']).sum()
    losses = (games['score'] < games['opponent_score']).sum()
    return f"{wins}-{losses}"

def get_result_emoji(score, opponent_score):
    """Return W or L based on score comparison"""
    if score > opponent_score:
        return "W"
    else:
        return "L"

# Sidebar
st.sidebar.title("Filters")

result_filter = st.sidebar.radio(
    "Game Result Filter",
    options=["All Games", "Wins Only", "Losses Only"],
    index=0
)

selected_players = st.sidebar.multiselect(
    "Players",
    options=df['player_name'].unique(),
    default=df['player_name'].unique()
)

# Apply filters
filtered_df = df[df['player_name'].isin(selected_players)].copy()

# Create win/loss indicator based on score comparison
filtered_df['is_win'] = filtered_df['score'] > filtered_df['opponent_score']

if result_filter == "Wins Only":
    filtered_df = filtered_df[filtered_df['is_win'] == True]
elif result_filter == "Losses Only":
    filtered_df = filtered_df[filtered_df['is_win'] == False]

# Main header
st.title("Dutchess Dairyboys - Season Analytics")
st.markdown(f"*Last updated: {df['scraped_at'].max().strftime('%Y-%m-%d %H:%M')}*")

# Top metrics row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Record", get_team_record(df))

with col2:
    total_gf = filtered_df.groupby('match_id')['goals'].sum().sum()
    st.metric("Goals For", int(total_gf))

with col3:
    total_ga = filtered_df.groupby('match_id')['opponent_score'].first().sum()
    st.metric("Goals Against", int(total_ga))

with col4:
    avg_war = filtered_df['war'].mean()
    st.metric("Avg WAR", f"{avg_war:.1f}%")

with col5:
    games_played = filtered_df['match_id'].nunique()
    st.metric("Games Played", games_played)

st.markdown("---")

# Win/Loss Comparison Section
st.header("Team Performance: Wins vs Losses")

# Calculate wins and losses based on score comparison
game_results = df.groupby('match_id').agg({
    'score': 'first',
    'opponent_score': 'first'
})
win_match_ids = game_results[game_results['score'] >= game_results['opponent_score']].index
loss_match_ids = game_results[game_results['score'] < game_results['opponent_score']].index

wins_df = df[df['match_id'].isin(win_match_ids)]
losses_df = df[df['match_id'].isin(loss_match_ids)]

if len(wins_df) > 0 and len(losses_df) > 0:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("When We Win")
        win_metrics = {
            'Avg Pass %': f"{wins_df['pass_pct'].mean():.1f}%",
            'Team Giveaways/Game': f"{wins_df.groupby('match_id')['giveaways'].sum().mean():.1f}",
            'Team Hits/Game': f"{wins_df.groupby('match_id')['hits'].sum().mean():.1f}",
            'Avg Team WAR': f"{wins_df.groupby('match_id')['war'].mean().mean():.1f}%",
            'Avg Shot %': f"{wins_df['shot_pct'].mean():.1f}%",
            'Avg TO%': f"{wins_df['total_offense'].mean():.1f}%",
            'Avg TD%': f"{wins_df['total_defense'].mean():.1f}%"
        }
        
        for metric, value in win_metrics.items():
            st.metric(metric, value)
    
    with col2:
        st.subheader("When We Lose")
        loss_metrics = {
            'Avg Pass %': f"{losses_df['pass_pct'].mean():.1f}%",
            'Team Giveaways/Game': f"{losses_df.groupby('match_id')['giveaways'].sum().mean():.1f}",
            'Team Hits/Game': f"{losses_df.groupby('match_id')['hits'].sum().mean():.1f}",
            'Avg Team WAR': f"{losses_df.groupby('match_id')['war'].mean().mean():.1f}%",
            'Avg Shot %': f"{losses_df['shot_pct'].mean():.1f}%",
            'Avg TO%': f"{losses_df['total_offense'].mean():.1f}%",
            'Avg TD%': f"{losses_df['total_defense'].mean():.1f}%"
        }
        
        for metric, value in loss_metrics.items():
            st.metric(metric, value)
    
    # Key Insights
    st.subheader("Key Insights")
    
    pass_diff = wins_df['pass_pct'].mean() - losses_df['pass_pct'].mean()
    give_diff = wins_df.groupby('match_id')['giveaways'].sum().mean() - losses_df.groupby('match_id')['giveaways'].sum().mean()
    hits_diff = wins_df.groupby('match_id')['hits'].sum().mean() - losses_df.groupby('match_id')['hits'].sum().mean()
    war_diff = wins_df.groupby('match_id')['war'].mean().mean() - losses_df.groupby('match_id')['war'].mean().mean()
    
    insights = []
    if abs(pass_diff) > 2:
        insights.append(f"Pass completion is {abs(pass_diff):.1f}% {'higher' if pass_diff > 0 else 'lower'} in wins")
    if abs(give_diff) > 2:
        insights.append(f"Team giveaways are {abs(give_diff):.1f} {'lower' if give_diff < 0 else 'higher'} per game in wins")
    if abs(hits_diff) > 2:
        insights.append(f"Team hits are {abs(hits_diff):.1f} {'higher' if hits_diff > 0 else 'lower'} per game in wins")
    if abs(war_diff) > 5:
        insights.append(f"Team WAR is {abs(war_diff):.1f}% {'higher' if war_diff > 0 else 'lower'} in wins")
    
    if insights:
        for insight in insights:
            st.write(f"- {insight}")
    else:
        st.write("- Not enough data yet to identify clear patterns")
else:
    st.info("Need both wins and losses to show comparison")

st.markdown("---")

# Team Trends Over Time
st.header("Team Trends Over Time")

game_trends = df.groupby(['match_id', 'game_date', 'result']).agg({
    'war': 'mean',
    'pass_pct': 'mean',
    'giveaways': 'sum',
    'total_offense': 'mean',
    'total_defense': 'mean'
}).reset_index().sort_values('game_date')

# Create color mapping for wins/losses
colors = ['green' if r == 1 else 'red' if r == 2 else 'orange' for r in game_trends['result']]

col1, col2 = st.columns(2)

with col1:
    fig_war_trend = go.Figure()
    fig_war_trend.add_trace(go.Scatter(
        x=game_trends['game_date'],
        y=game_trends['war'],
        mode='lines+markers',
        name='Avg Team WAR',
        marker=dict(size=12, color=colors, line=dict(width=2, color='white')),
        line=dict(color='gray', width=1)
    ))
    fig_war_trend.update_layout(
        title='Team WAR Over Time',
        xaxis_title='Game Date',
        yaxis_title='Avg WAR %',
        hovermode='x unified'
    )
    st.plotly_chart(fig_war_trend, use_container_width=True)

with col2:
    fig_give_trend = go.Figure()
    fig_give_trend.add_trace(go.Scatter(
        x=game_trends['game_date'],
        y=game_trends['giveaways'],
        mode='lines+markers',
        name='Team Giveaways',
        marker=dict(size=12, color=colors, line=dict(width=2, color='white')),
        line=dict(color='gray', width=1)
    ))
    fig_give_trend.update_layout(
        title='Team Giveaways Over Time',
        xaxis_title='Game Date',
        yaxis_title='Total Giveaways',
        hovermode='x unified'
    )
    st.plotly_chart(fig_give_trend, use_container_width=True)

st.markdown("---")

# Player Performance Comparison
st.header("Player Performance Comparison")

# Aggregate player stats with efficiency metrics
player_stats = filtered_df.groupby('player_name').agg({
    'goals': 'sum',
    'assists': 'sum',
    'points': 'sum',
    'war': 'mean',
    'total_offense': 'mean',
    'total_defense': 'mean',
    'efficiency': 'mean',
    'shots': 'sum',
    'shot_pct': 'mean',
    'pass_pct': 'mean',
    'passes': 'sum',
    'hits': 'sum',
    'giveaways': 'sum',
    'takeaways': 'sum',
    'interceptions': 'sum',
    'possession_minutes': 'sum',
    'match_id': 'count'
}).round(2)

player_stats.columns = ['Goals', 'Assists', 'Points', 'Avg WAR', 'Avg TO%', 'Avg TD%', 
                        'Avg Efficiency', 'Shots', 'Shot%', 'Pass%', 'Passes', 'Hits', 
                        'Giveaways', 'Takeaways', 'Ints', 'Poss Min', 'Games']

# Calculate per-game metrics
player_stats['Goals/Game'] = (player_stats['Goals'] / player_stats['Games']).round(2)
player_stats['Shots/Game'] = (player_stats['Shots'] / player_stats['Games']).round(1)
player_stats['Pass Attempts/Game'] = (player_stats['Passes'] / player_stats['Games']).round(1)
player_stats['Takeaways/Game'] = (player_stats['Takeaways'] / player_stats['Games']).round(2)
player_stats['Giveaways/Min'] = (player_stats['Giveaways'] / player_stats['Poss Min']).round(3)
player_stats['Points/Game'] = (player_stats['Points'] / player_stats['Games']).round(2)
player_stats['Hits/Game'] = (player_stats['Hits'] / player_stats['Games']).round(2)
player_stats['Avg T.O.P (min)'] = (player_stats['Poss Min'] / player_stats['Games']).round(2)
player_stats['Ints/Game'] = (player_stats['Ints'] / player_stats['Games']).round(2)

player_stats = player_stats.sort_values('player_name', ascending=False)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Offensive Stats")
    st.dataframe(
        player_stats[['Games', 'Goals', 'Goals/Game', 'Assists', 'Pass%', 'Pass Attempts/Game', 'Points', 'Points/Game', 
                      'Shots', 'Shots/Game', 'Shot%']], 
        use_container_width=True
    )

with col2:
    st.subheader("Defensive and Advanced Analytics")
    st.dataframe(
        player_stats[['Games', 'Avg T.O.P (min)', 'Avg WAR', 'Avg TO%', 'Avg TD%', 'Avg Efficiency', 
                      'Giveaways/Min', 'Takeaways', 'Takeaways/Game', 'Ints', 'Ints/Game', 'Hits/Game']], 
        use_container_width=True
    )

# Player comparison charts
col1, col2, col3 = st.columns(3)

with col1:
    fig_war = px.bar(
        player_stats.reset_index(),
        x='player_name',
        y='Avg WAR',
        title='Average WAR by Player',
        labels={'player_name': 'Player', 'Avg WAR': 'WAR (%)'},
        color='Avg WAR',
        color_continuous_scale='RdYlGn'
    )
    fig_war.update_layout(showlegend=False)
    st.plotly_chart(fig_war, use_container_width=True)

with col2:
    # Offense vs Defense scatter
    fig_scatter = px.scatter(
        player_stats.reset_index(),
        x='Avg TO%',
        y='Avg TD%',
        size='Avg WAR',
        color='Avg WAR',
        text='player_name',
        title='Offensive vs Defensive Contribution',
        labels={'Avg TO%': 'Total Offense %', 'Avg TD%': 'Total Defense %'},
        color_continuous_scale='RdYlGn'
    )
    fig_scatter.update_traces(textposition='top center')
    fig_scatter.update_layout(showlegend=False)
    st.plotly_chart(fig_scatter, use_container_width=True)

with col3:
    fig_give = px.bar(
        player_stats.reset_index(),
        x='player_name',
        y='Giveaways/Min',
        title='Giveaways per Minute of Possession',
        labels={'player_name': 'Player', 'Giveaways/Min': 'Giveaways/Min'},
        color='Giveaways/Min',
        color_continuous_scale='RdYlGn_r'
    )
    fig_give.update_layout(showlegend=False)
    st.plotly_chart(fig_give, use_container_width=True)

st.markdown("---")

# Player Performance in Wins vs Losses
st.header("Player Performance: Wins vs Losses")

if len(wins_df) > 0 and len(losses_df) > 0:
    player_wins = wins_df.groupby('player_name').agg({
        'war': 'mean',
        'total_offense': 'mean',
        'total_defense': 'mean',
        'pass_pct': 'mean',
        'giveaways': 'mean',
        'points': 'mean'
    }).round(1)
    
    player_losses = losses_df.groupby('player_name').agg({
        'war': 'mean',
        'total_offense': 'mean',
        'total_defense': 'mean',
        'pass_pct': 'mean',
        'giveaways': 'mean',
        'points': 'mean'
    }).round(1)
    
    comparison_df = pd.DataFrame({
        'Player': player_wins.index,
        'WAR (Wins)': player_wins['war'].values,
        'WAR (Losses)': player_losses.reindex(player_wins.index, fill_value=0)['war'].values,
        'Pass% (Wins)': player_wins['pass_pct'].values,
        'Pass% (Losses)': player_losses.reindex(player_wins.index, fill_value=0)['pass_pct'].values,
        'Giveaways (Wins)': player_wins['giveaways'].values,
        'Giveaways (Losses)': player_losses.reindex(player_wins.index, fill_value=0)['giveaways'].values
    })
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
else:
    st.info("Need both wins and losses to show player comparison")

st.markdown("---")

# Game Log
st.header("Game Log")

game_log = []
for match_id in df['match_id'].unique():
    game_data = df[df['match_id'] == match_id].iloc[0]
    team_goals = df[df['match_id'] == match_id]['goals'].sum()
    team_giveaways = df[df['match_id'] == match_id]['giveaways'].sum()
    
    game_log.append({
        'Date': game_data['game_date'].strftime('%Y-%m-%d'),
        'Result': get_result_emoji(game_data['score'], game_data['opponent_score']),
        'Score': f"{int(game_data['score'])}-{int(game_data['opponent_score'])}",
        'Goals': int(team_goals),
        'Shots': int(df[df['match_id'] == match_id]['shots'].sum()),
        'Pass%': f"{df[df['match_id'] == match_id]['pass_pct'].mean():.1f}%",
        'Giveaways': int(team_giveaways),
        'Avg WAR': f"{df[df['match_id'] == match_id]['war'].mean():.1f}%",
        'Match ID': match_id
    })

game_log_df = pd.DataFrame(game_log).sort_values('Date', ascending=False)
st.dataframe(game_log_df, use_container_width=True, hide_index=True)

st.markdown("---")

# Individual Player Details
st.header("Individual Player Performance")

selected_player_detail = st.selectbox("Select Player for Detailed View", df['player_name'].unique())

player_df = df[df['player_name'] == selected_player_detail].sort_values('game_date')

col1, col2 = st.columns(2)

with col1:
    st.subheader(f"{selected_player_detail} - Game by Game")
    player_game_log = player_df[[
        'game_date', 'goals', 'assists', 'points', 'score', 'opponent_score', 'result',
        'plus_minus', 'shots', 'pass_pct', 'giveaways', 'war', 'efficiency'
    ]].copy()
    player_game_log['game_date'] = player_game_log['game_date'].dt.strftime('%Y-%m-%d')
    player_game_log['result'] = player_game_log.apply(lambda row: get_result_emoji(row['score'], row['opponent_score']), axis=1)
    player_game_log.columns = ['Date', 'G', 'A', 'P', 'Score', 'Op Score', 'Result', '+/-', 'Shots', 'Pass%', 'Gives', 'WAR%', 'Eff%']
    st.dataframe(player_game_log, use_container_width=True, hide_index=True)

with col2:
    st.subheader(f"{selected_player_detail} - Season Totals")
    
    totals = {
        'Games Played': str(len(player_df)),
        'Goals': str(int(player_df['goals'].sum())),
        'Assists': str(int(player_df['assists'].sum())),
        'Points': str(int(player_df['points'].sum())),
        'Points/Game': f"{player_df['points'].mean():.2f}",
        'Plus/Minus': str(int(player_df['plus_minus'].sum())),
        'Avg WAR': f"{player_df['war'].mean():.1f}%",
        'Avg TO%': f"{player_df['total_offense'].mean():.1f}%",
        'Avg TD%': f"{player_df['total_defense'].mean():.1f}%",
        'Avg Efficiency': f"{player_df['efficiency'].mean():.1f}%",
        'Shot%': f"{player_df['shot_pct'].mean():.1f}%",
        'Pass%': f"{player_df['pass_pct'].mean():.1f}%",
        'Total Shots': str(int(player_df['shots'].sum())),
        'Total Hits': str(int(player_df['hits'].sum())),
        'Takeaways': str(int(player_df['takeaways'].sum())),
        'Giveaways': str(int(player_df['giveaways'].sum())),
        'Giveaways/Min': f"{(player_df['giveaways'].sum() / player_df['possession_minutes'].sum()):.3f}"
    }
    
    totals_df = pd.DataFrame(list(totals.items()), columns=['Stat', 'Value'])
    st.dataframe(totals_df, use_container_width=True, hide_index=True)

# Performance metrics chart for selected player
fig_player = go.Figure()

# Color markers by win/loss
player_colors = ['green' if r == 1 else 'red' if r == 2 else 'orange' for r in player_df['result']]

fig_player.add_trace(go.Scatter(
    x=player_df['game_date'],
    y=player_df['points'],
    mode='lines+markers',
    name='Points',
    line=dict(color='blue', width=2),
    marker=dict(size=10, color=player_colors, line=dict(width=2, color='white'))
))

fig_player.add_trace(go.Scatter(
    x=player_df['game_date'],
    y=player_df['war'],
    mode='lines+markers',
    name='WAR %',
    yaxis='y2',
    line=dict(color='green', width=2),
    marker=dict(size=10, color=player_colors, line=dict(width=2, color='white'))
))

fig_player.update_layout(
    title=f'{selected_player_detail} - Points & WAR Over Time (Green=Win, Red=Loss)',
    xaxis_title='Game Date',
    yaxis_title='Points',
    yaxis2=dict(
        title='WAR %',
        overlaying='y',
        side='right'
    ),
    hovermode='x unified'
)

st.plotly_chart(fig_player, use_container_width=True)

st.markdown("---")

# Heat Maps Section (replaces your current heat map section)
st.header("The Danger Zones")

# Load shot location data
@st.cache_data
def load_shot_data():
    try:
        return pd.read_csv('data/processed/shot_locations.csv')
    except:
        return pd.DataFrame()

shot_df = load_shot_data()

if not shot_df.empty:
    selected_heatmap_player = st.selectbox(
        "Select Player for Heat Map", 
        shot_df['player_name'].unique(), 
        key='heatmap'
    )
    
    player_shot_data = shot_df[shot_df['player_name'] == selected_heatmap_player].iloc[0]
    games_played = int(player_shot_data['games_played'])
    
    # Show games played context
    st.info(f"📊 Based on {games_played} career games played")
    
    # Define danger zones
    HIGH_DANGER = [4, 7]
    MID_DANGER = [5, 6, 9, 10, 11]
    LOW_DANGER = [1, 2, 3, 8, 12, 13, 14, 15, 16]
    
    # Create tabs
    tab1, tab2 = st.tabs(["Career Totals", "Per Game Average"])
    
    with tab1:

        title_col1, title_col2 = st.columns([0.9, 1.0])
        with title_col1:
            st.subheader(f"{selected_heatmap_player} - Career Shot Analysis")

        with title_col2:
            st.subheader("Shooting Efficiency by Zone")
        
        # Calculate totals
        total_shots = sum(player_shot_data[f'shots_zone_{z}'] for z in range(1, 17))
        total_goals = sum(player_shot_data[f'goals_zone_{z}'] for z in range(1, 17))
        
        high_shots = sum(player_shot_data[f'shots_zone_{z}'] for z in HIGH_DANGER)
        mid_shots = sum(player_shot_data[f'shots_zone_{z}'] for z in MID_DANGER)
        low_shots = sum(player_shot_data[f'shots_zone_{z}'] for z in LOW_DANGER)
        
        high_goals = sum(player_shot_data[f'goals_zone_{z}'] for z in HIGH_DANGER)
        mid_goals = sum(player_shot_data[f'goals_zone_{z}'] for z in MID_DANGER)
        low_goals = sum(player_shot_data[f'goals_zone_{z}'] for z in LOW_DANGER)
        
        high_pct = (high_shots / total_shots * 100) if total_shots > 0 else 0
        mid_pct = (mid_shots / total_shots * 100) if total_shots > 0 else 0
        low_pct = (low_shots / total_shots * 100) if total_shots > 0 else 0
        
        col1, col2 = st.columns([.9, 1.0])
        
        with col1:
            # Left side - Danger level breakdown
            subcol1, subcol2, subcol3, subcol4 = st.columns([1.5, 1, 0.6, 1])
            
            with subcol1:
                st.markdown(f"""
                <div style='border: 2px solid #444; padding: 20px; margin: 5px; border-radius: 5px;'>
                    <div style='font-weight: bold; font-size: 18px; margin-bottom: 10px;'>CHANCES</div>
                    <div style='text-align: center; font-size: 72px; margin-top: -10px;'>{int(total_shots)}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='border: 2px solid #444; padding: 20px; margin: 5px; border-radius: 5px; margin-top: 20px;'>
                    <div style='font-weight: bold; font-size: 18px; margin-bottom: 10px;'>GOALS SCORED</div>
                    <div style='text-align: center; font-size: 48px; color: #8B0000; margin-top: -10px;'>{int(total_goals)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with subcol2:
                st.markdown(f"""
                <div style='background-color: #2d5016; padding: 15px 10px; margin: 5px; border-radius: 5px;'>
                    <div style='color: white; font-weight: bold; margin-bottom: 5px;'>HIGH %</div>
                    <div style='color: white; font-size: 32px; margin-bottom: 8px;'>{int(high_shots)}</div>
                    <div style='color: #ccc; font-size: 11px;'>CONV %</div>
                    <div style='color: white; font-size: 16px;'>{(high_goals/high_shots*100) if high_shots > 0 else 0:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='background-color: #5a5a2d; padding: 15px 10px; margin: 5px; border-radius: 5px;'>
                    <div style='color: white; font-weight: bold; margin-bottom: 5px;'>MID %</div>
                    <div style='color: white; font-size: 32px; margin-bottom: 8px;'>{int(mid_shots)}</div>
                    <div style='color: #ccc; font-size: 11px;'>CONV %</div>
                    <div style='color: white; font-size: 16px;'>{(mid_goals/mid_shots*100) if mid_shots > 0 else 0:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='background-color: #5a1616; padding: 15px 10px; margin: 5px; border-radius: 5px;'>
                    <div style='color: white; font-weight: bold; margin-bottom: 5px;'>LOW %</div>
                    <div style='color: white; font-size: 32px; margin-bottom: 8px;'>{int(low_shots)}</div>
                    <div style='color: #ccc; font-size: 11px;'>CONV %</div>
                    <div style='color: white; font-size: 16px;'>{(low_goals/low_shots*100) if low_shots > 0 else 0:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with subcol3:
                st.markdown(f"""
                <div style='height: 140px; display: flex; align-items: center; justify-content: center; margin: 5px;'>
                    <div style='background-color: #1a1a1a; padding: 10px; border-radius: 5px;'>
                        <div style='color: white; font-weight: bold;'>GOALS</div>
                        <div style='color: white; font-size: 32px;'>{int(high_goals)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='height: 170px; display: flex; align-items: center; justify-content: center; margin: 5px;'>
                    <div style='background-color: #1a1a1a; padding: 10px; border-radius: 5px;'>
                        <div style='color: white; font-weight: bold;'>GOALS</div>
                        <div style='color: white; font-size: 32px;'>{int(mid_goals)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='height: 180px; display: flex; align-items: center; justify-content: center; margin: 5px;'>
                    <div style='background-color: #1a1a1a; padding: 10px; border-radius: 5px;'>
                        <div style='color: white; font-weight: bold;'>GOALS</div>
                        <div style='color: white; font-size: 32px;'>{int(low_goals)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with subcol4:
                # Pie chart
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['High Danger', 'Mid Danger', 'Low Danger'],
                    values=[high_shots, mid_shots, low_shots],
                    marker=dict(colors=['#00ff00', '#ffff00', '#ff0000']),
                    hole=0,
                    textinfo='none',
                    showlegend=False
                )])
                fig_pie.update_layout(
                    height=300,
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig_pie, use_container_width=True, key='pie_career')
        
        with col2:
            # Right side - Rink layout with colored text overlay
            # Load the rink image
            try:
                rink_img = Image.open('data/assets/rink_layout.png')
            except:
                st.error("Rink layout image not found. Please add rink_layout.png to data/assets/")
                rink_img = None
            
            if rink_img is not None:
                # Create figure
                fig, ax = plt.subplots(1, 1, figsize=(7, 8))
                ax.imshow(rink_img, extent=[0, 100, 0, 120], aspect='auto')
                ax.set_xlim(0, 100)
                ax.set_ylim(0, 120)
                ax.axis('off')
                
                # Function to get text color based on efficiency
                def get_text_color(efficiency):
                    if efficiency >= 20:
                        return '#00AA00'  # Green
                    elif efficiency >= 10:
                        return '#CCAA00'  # Yellow/Gold
                    else:
                        return '#CC0000'  # Red
                
                # Define zone text positions (x, y coordinates)
                zone_positions = {
                    1: (17, 108),    # Behind net left
                    2: (50, 108),    # Behind net center
                    3: (83, 108),    # Behind net right
                    4: (50, 97),     # Crease
                    5: (28, 90),     # High slot left wing
                    6: (72, 90),     # High slot right wing
                    7: (50, 80),     # Prime slot (zone 7 - the hot zone)
                    8: (7, 63),     # Left wing wide
                    9: (30, 55),     # Left circle
                    10: (50, 50),    # Center slot
                    11: (70, 55),    # Right circle
                    12: (92, 63),    # Right wing wide
                    13: (20, 41),    # Left point
                    14: (50, 38),    # Center point
                    15: (80, 41),    # Right point
                    16: (50, 12)     # Neutral zone
                }
                
                # Add text for each zone
                for zone_num, (x, y) in zone_positions.items():
                    goals = player_shot_data[f'goals_zone_{zone_num}']
                    shots = player_shot_data[f'shots_zone_{zone_num}']
                    
                    if shots > 0:
                        efficiency = (goals / shots) * 100
                    else:
                        efficiency = 0
                    
                    color = get_text_color(efficiency)
                    
                    # Add text with efficiency percentage and goals/shots
                    ax.text(x, y, f"{efficiency:.1f}%\n{int(goals)}/{int(shots)}", 
                        ha='center', va='center', 
                        fontsize=11, 
                        weight='bold',
                        color=color,
                        bbox=dict(boxstyle='round,pad=0.5', 
                                    facecolor='white', 
                                    edgecolor='black',
                                    linewidth=1.5,
                                    alpha=0.9))
                
                plt.tight_layout()
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
                
                # Legend
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.markdown("🟢 **Green:** >20% (Excellent)")
                with col_b:
                    st.markdown("🟡 **Yellow:** 10-20% (Average)")
                with col_c:
                    st.markdown("🔴 **Red:** <10% (Poor)")
            else:
                st.warning("Please add the rink layout image to display zone efficiency")
    
    with tab2:
        
        title_col1, title_col2 = st.columns([0.9, 1.0])
        with title_col1:
            st.subheader(f"{selected_heatmap_player} - Career Shot Analysis")

        with title_col2:
            st.subheader("Shooting Efficiency by Zone")
        
        # Calculate per-game averages
        total_shots_pg = total_shots / games_played
        total_goals_pg = total_goals / games_played
        
        high_shots_pg = high_shots / games_played
        mid_shots_pg = mid_shots / games_played
        low_shots_pg = low_shots / games_played
        
        high_goals_pg = high_goals / games_played
        mid_goals_pg = mid_goals / games_played
        low_goals_pg = low_goals / games_played
        
        col1, col2 = st.columns([.9, 1.0])
        
        with col1:
            # Left side - Danger level breakdown (per game)
            subcol1, subcol2, subcol3, subcol4 = st.columns([1.5, 1, 0.6, 1])
            
            with subcol1:
                st.markdown(f"""
                <div style='border: 2px solid #444; padding: 20px; margin: 5px; border-radius: 5px;'>
                    <div style='font-weight: bold; font-size: 18px; margin-bottom: 10px;'>CHANCES</div>
                    <div style='text-align: center; font-size: 72px; margin-top: -10px;'>{total_shots_pg:.1f}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='border: 2px solid #444; padding: 20px; margin: 5px; border-radius: 5px; margin-top: 20px;'>
                    <div style='font-weight: bold; font-size: 18px; margin-bottom: 10px;'>GOALS SCORED</div>
                    <div style='text-align: center; font-size: 48px; color: #8B0000; margin-top: -10px;'>{total_goals_pg:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with subcol2:
                st.markdown(f"""
                <div style='background-color: #2d5016; padding: 15px 10px; margin: 5px; border-radius: 5px;'>
                    <div style='color: white; font-weight: bold; margin-bottom: 5px;'>HIGH %</div>
                    <div style='color: white; font-size: 32px; margin-bottom: 8px;'>{high_shots_pg:.1f}</div>
                    <div style='color: #ccc; font-size: 11px;'>CONV %</div>
                    <div style='color: white; font-size: 16px;'>{(high_goals/high_shots*100) if high_shots > 0 else 0:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='background-color: #5a5a2d; padding: 15px 10px; margin: 5px; border-radius: 5px;'>
                    <div style='color: white; font-weight: bold; margin-bottom: 5px;'>MID %</div>
                    <div style='color: white; font-size: 32px; margin-bottom: 8px;'>{mid_shots_pg:.1f}</div>
                    <div style='color: #ccc; font-size: 11px;'>CONV %</div>
                    <div style='color: white; font-size: 16px;'>{(mid_goals/mid_shots*100) if mid_shots > 0 else 0:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='background-color: #5a1616; padding: 15px 10px; margin: 5px; border-radius: 5px;'>
                    <div style='color: white; font-weight: bold; margin-bottom: 5px;'>LOW %</div>
                    <div style='color: white; font-size: 32px; margin-bottom: 8px;'>{low_shots_pg:.1f}</div>
                    <div style='color: #ccc; font-size: 11px;'>CONV %</div>
                    <div style='color: white; font-size: 16px;'>{(low_goals/low_shots*100) if low_shots > 0 else 0:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with subcol3:
                st.markdown(f"""
                <div style='height: 140px; display: flex; align-items: center; justify-content: center; margin: 5px;'>
                    <div style='background-color: #1a1a1a; padding: 10px; border-radius: 5px;'>
                        <div style='color: white; font-weight: bold;'>GOALS</div>
                        <div style='color: white; font-size: 32px;'>{high_goals_pg:.2f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='height: 170px; display: flex; align-items: center; justify-content: center; margin: 5px;'>
                    <div style='background-color: #1a1a1a; padding: 10px; border-radius: 5px;'>
                        <div style='color: white; font-weight: bold;'>GOALS</div>
                        <div style='color: white; font-size: 32px;'>{mid_goals_pg:.2f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='height: 180px; display: flex; align-items: center; justify-content: center; margin: 5px;'>
                    <div style='background-color: #1a1a1a; padding: 10px; border-radius: 5px;'>
                        <div style='color: white; font-weight: bold;'>GOALS</div>
                        <div style='color: white; font-size: 32px;'>{low_goals_pg:.2f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                        
            with subcol4:
                # Pie chart (same distribution, just different scale)
                fig_pie_pg = go.Figure(data=[go.Pie(
                    labels=['High Danger', 'Mid Danger', 'Low Danger'],
                    values=[high_shots, mid_shots, low_shots],
                    marker=dict(colors=['#00ff00', '#ffff00', '#ff0000']),
                    hole=0,
                    textinfo='none',
                    showlegend=False
                )])
                fig_pie_pg.update_layout(
                    height=300,
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig_pie_pg, use_container_width=True, key='pie_pergame')
        
        with col2:
            # Right side - Rink layout with colored text overlay            
            # Load the rink image
            try:
                rink_img = Image.open('data/assets/rink_layout.png')
            except:
                st.error("Rink layout image not found. Please add rink_layout.png to data/assets/")
                rink_img = None
            
            if rink_img is not None:
                # Create figure
                fig, ax = plt.subplots(1, 1, figsize=(7, 8))
                ax.imshow(rink_img, extent=[0, 100, 0, 120], aspect='auto')
                ax.set_xlim(0, 100)
                ax.set_ylim(0, 120)
                ax.axis('off')
                
                # Function to get text color based on efficiency
                def get_text_color(efficiency):
                    if efficiency >= 20:
                        return '#00AA00'  # Green
                    elif efficiency >= 10:
                        return '#CCAA00'  # Yellow/Gold
                    else:
                        return '#CC0000'  # Red
                
                # Define zone text positions (x, y coordinates
                zone_positions = {
                    1: (17, 108),    # Behind net left
                    2: (50, 108),    # Behind net center
                    3: (83, 108),    # Behind net right
                    4: (50, 97),     # Crease
                    5: (28, 90),     # High slot left wing
                    6: (72, 90),     # High slot right wing
                    7: (50, 80),     # Prime slot (zone 7 - the hot zone)
                    8: (7, 63),     # Left wing wide
                    9: (30, 55),     # Left circle
                    10: (50, 50),    # Center slot
                    11: (70, 55),    # Right circle
                    12: (92, 63),    # Right wing wide
                    13: (20, 41),    # Left point
                    14: (50, 38),    # Center point
                    15: (80, 41),    # Right point
                    16: (50, 12)     # Neutral zone
                }
                
                # Add text for each zone
                for zone_num, (x, y) in zone_positions.items():
                    goals = player_shot_data[f'goals_zone_{zone_num}']
                    shots = player_shot_data[f'shots_zone_{zone_num}']

                    # Calculate per-game values
                    goals_pg = goals / games_played
                    shots_pg = shots / games_played
                    
                    if shots > 0:
                        efficiency = (goals / shots) * 100
                    else:
                        efficiency = 0
                    
                    color = get_text_color(efficiency)
                    
                    # Add text with efficiency percentage and goals/shots
                    ax.text(x, y, f"{efficiency:.1f}%\n{goals_pg:.2f}/{shots_pg:.1f}", 
                        ha='center', va='center', 
                        fontsize=11, 
                        weight='bold',
                        color=color,
                        bbox=dict(boxstyle='round,pad=0.5', 
                                    facecolor='white', 
                                    edgecolor='black',
                                    linewidth=1.5,
                                    alpha=0.9))
                
                plt.tight_layout()
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
                
                # Legend
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.markdown("🟢 **Green:** >20% (Excellent)")
                with col_b:
                    st.markdown("🟡 **Yellow:** 10-20% (Average)")
                with col_c:
                    st.markdown("🔴 **Red:** <10% (Poor)")
            else:
                st.warning("Please add the rink layout image to display zone efficiency")

else:
    st.info("⚠️ Run the pipeline to generate shot location data: `python scrapers/heatmap_scraper.py`")

st.markdown("---")
st.caption("Data scraped from ChelStats | Advanced stats calculated by ChelStats analytics engine")