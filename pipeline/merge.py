"""
Merge basic and advanced stats into unified dataset
"""
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.config import DB_BASIC_STATS, DB_ADVANCED_STATS, DB_MERGED_STATS
from utils.helpers import setup_logging

logger = setup_logging(__name__)


def merge_stats():
    """Merge basic and advanced stats on match_id + player_name"""
    logger.info("Starting merge process...")
    
    # Check if files exist
    if not DB_BASIC_STATS.exists():
        logger.error(f"Basic stats file not found: {DB_BASIC_STATS}")
        return False
    
    if not DB_ADVANCED_STATS.exists():
        logger.error(f"Advanced stats file not found: {DB_ADVANCED_STATS}")
        return False
    
    # Load data
    df_basic = pd.read_csv(DB_BASIC_STATS)
    df_advanced = pd.read_csv(DB_ADVANCED_STATS)
    
    logger.info(f"Loaded {len(df_basic)} basic stat records")
    logger.info(f"Loaded {len(df_advanced)} advanced stat records")
    
    # Merge on match_id and player_name
    df_merged = pd.merge(
        df_basic,
        df_advanced,
        on=['match_id', 'player_name'],
        how='left',
        suffixes=('', '_adv')
    )
    
    df_merged = df_merged[df_merged['player_name'].isin(['Mcapp_1', 'TwoInchTommy565', 'NYKings06', 'MrBazzzz', 'Slick__AV'])]
    
    # Drop duplicate scraped_at column
    if 'scraped_at_adv' in df_merged.columns:
        df_merged = df_merged.drop('scraped_at_adv', axis=1)
    
    # Save merged data
    df_merged.to_csv(DB_MERGED_STATS, index=False)
    
    logger.info(f"Merged {len(df_merged)} records to {DB_MERGED_STATS}")
    logger.info(f"Advanced stats coverage: {df_merged['war'].notna().sum()}/{len(df_merged)} records")
    
    return True


if __name__ == "__main__":
    merge_stats()