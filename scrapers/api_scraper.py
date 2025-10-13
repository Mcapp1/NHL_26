"""
API-based scraper for basic NHL 26 stats
"""
import requests
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.config import (
    CLUB_STATS_URL, CLUB_ID, DB_BASIC_STATS
)
from utils.helpers import setup_logging

logger = setup_logging(__name__)


class APIBasicStatsScraper:
    """Scrapes basic game stats from ChelStats API"""
    
    def fetch_club_data(self):
        """Fetch club data from API"""
        try:
            logger.info("Fetching club data from API...")
            response = requests.get(CLUB_STATS_URL, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching API data: {e}")
            return None
    
    def get_match_ids(self, data):
        """Extract match IDs from API response"""
        try:
            games = data.get('recentGames', {}).get('RegularSeason', [])
            match_ids = [game['matchId'] for game in games]
            logger.info(f"Found {len(match_ids)} recent games")
            return match_ids
        except Exception as e:
            logger.error(f"Error extracting match IDs: {e}")
            return []
    
    def extract_player_game_stats(self, game_data, club_id):
        """Extract player stats from a single game"""
        players_data = []
        
        match_id = game_data.get('matchId')
        timestamp = game_data.get('timestamp')
        
        if 'players' not in game_data or club_id not in game_data['players']:
            return players_data
        
        club_players = game_data['players'][club_id]
        
        for player_id, stats in club_players.items():
            player_record = {
                # Identifiers
                'match_id': match_id,
                'timestamp': timestamp,
                'scraped_at': datetime.now().isoformat(),
                'player_name': stats.get('playername'),
                'player_id': player_id,
                'position': stats.get('position'),
                'player_class': stats.get('class'),
                
                # Game info
                'result': stats.get('result'),
                'score': stats.get('score'),
                'opponent_score': stats.get('opponentScore'),
                'opponent_club_id': stats.get('opponentClubId'),
                
                # Time
                'toi_seconds': stats.get('toiseconds'),
                'toi_minutes': round(int(stats.get('toiseconds', 0)) / 60, 2) if stats.get('toiseconds') else None,
                
                # Ratings
                'rating_offense': stats.get('ratingOffense'),
                'rating_defense': stats.get('ratingDefense'),
                'rating_teamplay': stats.get('ratingTeamplay'),
                
                # Scoring
                'goals': stats.get('skgoals'),
                'assists': stats.get('skassists'),
                'points': int(stats.get('skgoals', 0)) + int(stats.get('skassists', 0)),
                'gwg': stats.get('skgwg'),
                'ppg': stats.get('skppg'),
                'shg': stats.get('skshg'),
                'plus_minus': stats.get('skplusmin'),
                
                # Shooting
                'shots': stats.get('skshots'),
                'shot_attempts': stats.get('skshotattempts'),
                'shot_pct': stats.get('skshotpct'),
                'shot_on_net_pct': stats.get('skshotonnetpct'),
                'deflections': stats.get('skdeflections'),
                
                # Passing
                'passes': stats.get('skpasses'),
                'pass_attempts': stats.get('skpassattempts'),
                'pass_pct': stats.get('skpasspct'),
                'saucer_passes': stats.get('sksaucerpasses'),
                
                # Possession
                'possession_seconds': stats.get('skpossession'),
                'possession_minutes': round(int(stats.get('skpossession', 0)) / 60, 2) if stats.get('skpossession') else None,
                
                # Faceoffs
                'faceoff_wins': stats.get('skfow'),
                'faceoff_losses': stats.get('skfol'),
                'faceoff_pct': stats.get('skfopct'),
                
                # Defense
                'hits': stats.get('skhits'),
                'blocked_shots': stats.get('skbs'),
                'interceptions': stats.get('skinterceptions'),
                'takeaways': stats.get('sktakeaways'),
                'giveaways': stats.get('skgiveaways'),
                'pk_clear_zone': stats.get('skpkclearzone'),
                
                # Penalties
                'pim': stats.get('skpim'),
                'penalties_drawn': stats.get('skpenaltiesdrawn'),
                
                # Goalie stats
                'goalie_saves': stats.get('glsaves'),
                'goalie_shots_against': stats.get('glshots'),
                'goalie_goals_against': stats.get('glga'),
                'goalie_save_pct': stats.get('glsavepct'),
                'goalie_gaa': stats.get('glgaa'),
                'goalie_shutout_periods': stats.get('glsoperiods'),
            }
            
            players_data.append(player_record)
        
        return players_data
    
    def scrape(self):
        """Main scraping function"""
        logger.info("Starting basic stats scraper...")
        
        # Fetch data
        data = self.fetch_club_data()
        if not data:
            logger.error("Failed to fetch club data")
            return []
        
        # Get games
        recent_games = data.get('recentGames', {}).get('RegularSeason', [])
        
        # Extract stats
        all_player_stats = []
        for game in recent_games:
            match_id = game.get('matchId')
            logger.info(f"Processing game {match_id}")
            
            player_stats = self.extract_player_game_stats(game, CLUB_ID)
            all_player_stats.extend(player_stats)
            logger.info(f"  Extracted stats for {len(player_stats)} players")
        
        return all_player_stats
    
    def save(self, data):
        """Save to database with duplicate checking"""
        if not data:
            logger.warning("No data to save")
            return 0
        
        df_new = pd.DataFrame(data)
        
        if DB_BASIC_STATS.exists():
            df_existing = pd.read_csv(DB_BASIC_STATS)
            
            # Check for duplicates
            df_existing['key'] = df_existing['match_id'].astype(str) + '_' + df_existing['player_id'].astype(str)
            df_new['key'] = df_new['match_id'].astype(str) + '_' + df_new['player_id'].astype(str)
            
            df_new_only = df_new[~df_new['key'].isin(df_existing['key'])].drop('key', axis=1)
            df_existing = df_existing.drop('key', axis=1)
            
            if len(df_new_only) > 0:
                df_combined = pd.concat([df_existing, df_new_only], ignore_index=True)
            else:
                logger.info("No new records (all duplicates)")
                return 0
        else:
            df_combined = df_new
        
        df_combined.to_csv(DB_BASIC_STATS, index=False)
        logger.info(f"Saved {len(df_new)} new records to {DB_BASIC_STATS}")
        
        return len(df_new)


if __name__ == "__main__":
    scraper = APIBasicStatsScraper()
    data = scraper.scrape()
    scraper.save(data)