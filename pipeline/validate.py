"""
Data validation and quality checks
"""
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.config import DB_MERGED_STATS
from utils.helpers import setup_logging

logger = setup_logging(__name__)


def validate_data():
    """Run data quality checks"""
    logger.info("Running data validation...")
    
    if not DB_MERGED_STATS.exists():
        logger.error(f"Merged stats file not found: {DB_MERGED_STATS}")
        return False
    
    df = pd.read_csv(DB_MERGED_STATS)
    
    issues = []
    
    # Check for duplicates
    duplicates = df.duplicated(subset=['match_id', 'player_name'], keep=False)
    if duplicates.any():
        dup_count = duplicates.sum()
        issues.append(f"Found {dup_count} duplicate records")
        logger.warning(f"Found {dup_count} duplicate records")
    
    # Check for missing critical fields
    critical_fields = ['match_id', 'player_name', 'goals', 'assists', 'points']
    for field in critical_fields:
        missing = df[field].isna().sum()
        if missing > 0:
            issues.append(f"{field} has {missing} missing values")
            logger.warning(f"{field} has {missing} missing values")
    
    # Check for advanced stats coverage
    war_coverage = df['war'].notna().sum() / len(df) * 100
    if war_coverage < 90:
        issues.append(f"Advanced stats coverage only {war_coverage:.1f}%")
        logger.warning(f"Advanced stats coverage only {war_coverage:.1f}%")
    
    # Check for negative stats that shouldn't be negative
    if (df['goals'] < 0).any():
        issues.append("Found negative goal values")
        logger.error("Found negative goal values")
    
    if issues:
        logger.warning(f"Validation found {len(issues)} issues")
        for issue in issues:
            logger.warning(f"  - {issue}")
        return False
    else:
        logger.info("Data validation passed")
        return True


if __name__ == "__main__":
    validate_data()