"""
Configuration settings for NHL 26 stats pipeline
"""
import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Team configuration
TEAM_NAME = "Dutchess Dairyboys"
TEAM_NAME_ENCODED = "Dutchess%20dairyboys"
CONSOLE = "common-gen5"
CLUB_ID = "58805"

# Player names
PLAYER_NAMES = ['MrBazzzz', 'Mcapp_1', 'TwoInchTommy565', 'NYKings06', 'Slick__AV']

# API endpoints
API_BASE_URL = "https://chelstats.app/api"
CLUB_STATS_URL = f"{API_BASE_URL}/clubs/stats?teamname={TEAM_NAME_ENCODED}&console={CONSOLE}&strict=false"

# Game URLs
def get_game_url(match_id):
    return f"https://chelstats.app/clubs/recent-games?teamname={TEAM_NAME_ENCODED}&console={CONSOLE}&gameType=RegularSeason&matchId={match_id}"

# Database files
DB_BASIC_STATS = RAW_DATA_DIR / "basic_stats.csv"
DB_ADVANCED_STATS = RAW_DATA_DIR / "advanced_stats.csv"
DB_MERGED_STATS = PROCESSED_DATA_DIR / "merged_stats.csv"

# Scraper settings
SCRAPER_TIMEOUT = 30000  # milliseconds
WAIT_AFTER_CLICK = 4000  # milliseconds
HEADLESS_MODE = True  # Set to False for debugging

# Logging
LOG_FILE = LOGS_DIR / "pipeline.log"
LOG_LEVEL = "INFO"