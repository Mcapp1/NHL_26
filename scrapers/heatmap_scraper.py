# scrapers/heatmap_scraper.py
import json
import pandas as pd
import logging
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.helpers import setup_logging

logger = setup_logging(__name__)

def scrape_career_shot_data():
    """Load shot location data from captured Pro Clubs JSON"""
    logger.info("Loading shot location data from proclubs_members_stats.json...")
    
    try:
        json_path = Path("data/raw/proclubs_members_stats.json")
        
        if not json_path.exists():
            logger.error("proclubs_members_stats.json not found - run ea_proclubs_scraper first")
            return pd.DataFrame()
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        members = data.get('members', [])
        logger.info(f"Found shot location data for {len(members)} players")

        if len(members) == 0:
            logger.warning("No members found in JSON file")
            return pd.DataFrame()

        shot_data = []
        for member in members:
            player_name = member.get('name')
            games_played = int(member.get('gp', 0))
            
            logger.info(f"Processing {player_name}: {games_played} games")
            
            if games_played == 0:
                logger.warning(f"Skipping {player_name} - 0 games played")
                continue
            
            player_shots = {
                'player_name': player_name,
                'games_played': games_played,
                'favorite_position': member.get('favoritePosition', ''),
            }
            
            # Goals and Shots by zone
            for i in range(1, 17):
                goals_key = f'GoalsLocationOnIce{i}'
                shots_key = f'ShotsLocationOnIce{i}'
                goals = int(member.get(goals_key, 0))
                shots = int(member.get(shots_key, 0))
                
                player_shots[f'goals_zone_{i}'] = goals
                player_shots[f'goals_zone_{i}_per_game'] = round(goals / games_played, 2)
                
                player_shots[f'shots_zone_{i}'] = shots
                player_shots[f'shots_zone_{i}_per_game'] = round(shots / games_played, 2)
                
                player_shots[f'efficiency_zone_{i}'] = round((goals / shots * 100) if shots > 0 else 0, 1)

            # Goals and Shots by net location
            for i in range(1, 6):
                goals_key = f'GoalsLocationOnNet{i}'
                shots_key = f'ShotsLocationOnNet{i}'
                goals = int(member.get(goals_key, 0))
                shots = int(member.get(shots_key, 0))
                
                player_shots[f'goals_net_{i}'] = goals
                player_shots[f'goals_net_{i}_per_game'] = round(goals / games_played, 2)
                
                player_shots[f'shots_net_{i}'] = shots
                player_shots[f'shots_net_{i}_per_game'] = round(shots / games_played, 2)

            shot_data.append(player_shots)

        df = pd.DataFrame(shot_data)
        df[['goals_zone_5', 'goals_zone_6']] = df[['goals_zone_6', 'goals_zone_5']]
        output_path = 'data/processed/shot_locations.csv'
        df.to_csv(output_path, index=False)
        logger.info(f"Saved shot location data to {output_path}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading shot location data: {e}", exc_info=True)
        return pd.DataFrame()

if __name__ == "__main__":
    logger.info("Starting shot location data processing...")
    df = scrape_career_shot_data()
    
    if not df.empty:
        logger.info(f"✅ Successfully processed data for {len(df)} players")
        logger.info(f"Players: {', '.join(df['player_name'].tolist())}")
    else:
        logger.warning("⚠️ No shot location data processed")