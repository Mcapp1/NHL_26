"""
Shared utility functions
"""
import logging
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.config import (
    DB_BASIC_STATS, DB_ADVANCED_STATS,
    LOG_FILE, LOG_LEVEL
)


def setup_logging(name):
    """Setup logging configuration"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_existing_match_ids():
    """Get set of match IDs already in database"""
    match_ids = set()
    
    if DB_BASIC_STATS.exists():
        df = pd.read_csv(DB_BASIC_STATS)
        match_ids.update(df['match_id'].unique())
    
    if DB_ADVANCED_STATS.exists():
        df = pd.read_csv(DB_ADVANCED_STATS)
        match_ids.update(df['match_id'].astype(str).unique())
    
    return match_ids