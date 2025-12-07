"""
Mempool.space API Data Collectors

Fetches Bitcoin on-chain metrics from Mempool.space API.
No authentication required, unlimited rate.

Interface Contract:
    All functions return pd.DataFrame with DatetimeIndex (UTC)
    Returns empty DataFrame on error
"""

import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration
MEMPOOL_BASE_URL = "https://mempool.space/api/v1"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "on_chain")
CACHE_VALIDITY_HOURS = 24
REQUEST_TIMEOUT = 15


def _get_cache_path(metric_name: str) -> str:
    """Get cache file path for a metric."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{metric_name}_cache.csv")


def _is_cache_valid(cache_path: str) -> bool:
    """Check if cache exists and is less than 24h old."""
    if not os.path.exists(cache_path):
        return False
    try:
        file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        age = datetime.now() - file_mtime
        return age < timedelta(hours=CACHE_VALIDITY_HOURS)
    except Exception as e:
        logger.warning(f"Error checking cache validity: {e}")
        return False


def _load_from_cache(cache_path: str) -> Optional[pd.DataFrame]:
    """Load DataFrame from cache file."""
    try:
        df = pd.read_csv(cache_path, parse_dates=['date'])
        df['date'] = pd.to_datetime(df['date'], utc=True)
        df = df.sort_values('date')
        logger.info(f"Loaded {len(df)} records from cache: {cache_path}")
        return df
    except Exception as e:
        logger.warning(f"Error loading cache: {e}")
        return None


def _save_to_cache(df: pd.DataFrame, cache_path: str) -> bool:
    """Save DataFrame to cache file."""
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        df.to_csv(cache_path, index=False)
        logger.info(f"Saved {len(df)} records to cache: {cache_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to cache: {e}")
        return False


def _filter_by_date(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """Filter DataFrame by date range."""
    try:
        start = pd.to_datetime(start_date, utc=True)
        end = pd.to_datetime(end_date, utc=True) + timedelta(days=1)
        return df[(df['date'] >= start) & (df['date'] < end)].copy()
    except Exception as e:
        logger.warning(f"Error filtering by date: {e}")
        return df


def fetch_hash_rate(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch Bitcoin network hash rate from Mempool.space with 24h caching.
    
    Args:
        start_date: Format 'YYYY-MM-DD'
        end_date: Format 'YYYY-MM-DD'
    
    Returns:
        pd.DataFrame: Columns ['date', 'hash_rate_eh'], index DatetimeIndex (UTC)
                     Values in Exahash/s (EH/s)
    """
    cache_path = _get_cache_path("hash_rate")
    
    # Check cache first
    if _is_cache_valid(cache_path):
        cached_df = _load_from_cache(cache_path)
        if cached_df is not None and not cached_df.empty:
            return _filter_by_date(cached_df, start_date, end_date)
    
    # Fetch from API
    url = f"{MEMPOOL_BASE_URL}/mining/hashrate/1y"
    logger.info(f"Fetching hash rate from Mempool.space...")
    
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if not data or 'hashrates' not in data:
            logger.warning("Empty or invalid response from Mempool.space for hash rate")
            return pd.DataFrame()
        
        # Parse response
        records = []
        for item in data['hashrates']:
            timestamp = item.get('timestamp')
            avg_hashrate = item.get('avgHashrate', 0)
            if timestamp:
                records.append({
                    'date': pd.to_datetime(timestamp, unit='s', utc=True),
                    'hash_rate_eh': avg_hashrate / 1e18  # Convert to EH/s
                })
        
        if not records:
            logger.warning("No hash rate data parsed")
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df = df.sort_values('date').drop_duplicates(subset=['date'], keep='last')
        
        logger.info(f"Fetched {len(df)} hash rate records")
        
        # Save to cache
        _save_to_cache(df, cache_path)
        
        return _filter_by_date(df, start_date, end_date)
        
    except requests.exceptions.Timeout:
        logger.error("Timeout fetching hash rate from Mempool.space")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching hash rate: {e}")
        return pd.DataFrame()
    except ValueError as e:
        logger.error(f"JSON parsing error for hash rate: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error fetching hash rate: {e}")
        return pd.DataFrame()


def fetch_difficulty(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch Bitcoin mining difficulty adjustments from Mempool.space with 24h caching.
    
    Args:
        start_date: Format 'YYYY-MM-DD'
        end_date: Format 'YYYY-MM-DD'
    
    Returns:
        pd.DataFrame: Columns ['date', 'difficulty', 'adjustment_pct']
                     index DatetimeIndex (UTC)
    """
    cache_path = _get_cache_path("difficulty")
    
    # Check cache first
    if _is_cache_valid(cache_path):
        cached_df = _load_from_cache(cache_path)
        if cached_df is not None and not cached_df.empty:
            return _filter_by_date(cached_df, start_date, end_date)
    
    # Fetch from API
    url = f"{MEMPOOL_BASE_URL}/mining/difficulty-adjustments/1y"
    logger.info(f"Fetching difficulty from Mempool.space...")
    
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            logger.warning("Empty response from Mempool.space for difficulty")
            return pd.DataFrame()
        
        # Parse response - format: [[timestamp, height, difficulty, adjustment], ...]
        records = []
        for item in data:
            if len(item) >= 4:
                timestamp, height, difficulty, adjustment = item[0], item[1], item[2], item[3]
                records.append({
                    'date': pd.to_datetime(timestamp, unit='s', utc=True),
                    'difficulty': float(difficulty),
                    'adjustment_pct': float(adjustment)
                })
        
        if not records:
            logger.warning("No difficulty data parsed")
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df = df.sort_values('date').drop_duplicates(subset=['date'], keep='last')
        
        logger.info(f"Fetched {len(df)} difficulty records")
        
        # Save to cache
        _save_to_cache(df, cache_path)
        
        return _filter_by_date(df, start_date, end_date)
        
    except requests.exceptions.Timeout:
        logger.error("Timeout fetching difficulty from Mempool.space")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching difficulty: {e}")
        return pd.DataFrame()
    except ValueError as e:
        logger.error(f"JSON parsing error for difficulty: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error fetching difficulty: {e}")
        return pd.DataFrame()
