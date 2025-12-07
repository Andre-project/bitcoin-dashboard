"""
Glassnode API Data Collector Module

Fetches Bitcoin on-chain metrics from Glassnode API with local caching.
Rate limited to 10 requests/minute (free tier).

Interface Contract:
    All functions return pd.DataFrame with columns ['date', '{metric_name}']
    Date column is pd.DatetimeIndex (UTC timezone)
    Returns empty DataFrame on error
"""

import os
import time
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration
GLASSNODE_BASE_URL = "https://api.glassnode.com/v1/metrics"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "on_chain")
CACHE_VALIDITY_HOURS = 24
REQUEST_TIMEOUT = 15
RATE_LIMIT_SLEEP = 7  # seconds between API calls


def _get_api_key() -> Optional[str]:
    """Get Glassnode API key from environment variable."""
    api_key = os.getenv("GLASSNODE_API_KEY")
    if not api_key:
        logger.error("GLASSNODE_API_KEY environment variable not set")
        return None
    return api_key


def _get_cache_path(metric_name: str) -> str:
    """
    Get the cache file path for a metric.
    
    Args:
        metric_name: Name of the metric (e.g., 'mvrv_ratio')
    
    Returns:
        str: Absolute path to cache file
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{metric_name}_cache.csv")


def _is_cache_valid(cache_path: str, hours: int = CACHE_VALIDITY_HOURS) -> bool:
    """
    Check if cache file exists and is less than specified hours old.
    
    Args:
        cache_path: Path to cache file
        hours: Maximum age in hours for valid cache
    
    Returns:
        bool: True if cache is valid, False otherwise
    """
    if not os.path.exists(cache_path):
        return False
    
    try:
        file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        age = datetime.now() - file_mtime
        return age < timedelta(hours=hours)
    except Exception as e:
        logger.warning(f"Error checking cache validity: {e}")
        return False


def _load_from_cache(cache_path: str, metric_name: str) -> Optional[pd.DataFrame]:
    """
    Load data from cache file.
    
    Args:
        cache_path: Path to cache file
        metric_name: Name of the metric column
    
    Returns:
        pd.DataFrame or None if load fails
    """
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
    """
    Save DataFrame to cache file.
    
    Args:
        df: DataFrame to save
        cache_path: Path to cache file
    
    Returns:
        bool: True if save successful
    """
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        df.to_csv(cache_path, index=False)
        logger.info(f"Saved {len(df)} records to cache: {cache_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to cache: {e}")
        return False


def _fetch_glassnode_metric(
    endpoint: str,
    metric_name: str,
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    Generic fetcher for Glassnode API with caching and rate limiting.
    
    Args:
        endpoint: API endpoint path (e.g., 'market/mvrv')
        metric_name: Name for the metric column (e.g., 'mvrv_ratio')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        pd.DataFrame: Columns ['date', metric_name], DatetimeIndex (UTC)
        Returns empty DataFrame on error
    """
    cache_path = _get_cache_path(metric_name)
    
    # 1. Check cache first
    if _is_cache_valid(cache_path):
        cached_df = _load_from_cache(cache_path, metric_name)
        if cached_df is not None and not cached_df.empty:
            return cached_df
    
    # 2. Get API key
    api_key = _get_api_key()
    if not api_key:
        return pd.DataFrame()
    
    # 3. Convert dates to Unix timestamps
    try:
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        return pd.DataFrame()
    
    # 4. Build API URL
    url = f"{GLASSNODE_BASE_URL}/{endpoint}"
    params = {
        "a": "BTC",
        "s": start_ts,
        "u": end_ts,
        "i": "24h",
        "api_key": api_key
    }
    
    # 5. Rate limiting
    logger.info(f"Fetching {metric_name} from Glassnode API...")
    time.sleep(RATE_LIMIT_SLEEP)
    
    # 6. Make API request
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            logger.warning(f"Empty response from Glassnode for {metric_name}")
            return pd.DataFrame()
        
        # 7. Parse response
        df = pd.DataFrame(data)
        
        if df.empty:
            logger.warning(f"No data returned for {metric_name}")
            return pd.DataFrame()
        
        # Expected format: [{"t": timestamp, "v": value}, ...]
        if 't' in df.columns and 'v' in df.columns:
            df['date'] = pd.to_datetime(df['t'], unit='s', utc=True)
            df[metric_name] = df['v']
            df = df[['date', metric_name]].copy()
        else:
            logger.error(f"Unexpected response format for {metric_name}: {df.columns.tolist()}")
            return pd.DataFrame()
        
        # 8. Clean data
        df = df.dropna()
        df = df.sort_values('date')
        df = df.drop_duplicates(subset=['date'], keep='last')
        
        logger.info(f"Fetched {len(df)} records for {metric_name}")
        
        # 9. Save to cache
        _save_to_cache(df, cache_path)
        
        return df
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {metric_name} from Glassnode")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching {metric_name}: {e}")
        return pd.DataFrame()
    except ValueError as e:
        logger.error(f"JSON parsing error for {metric_name}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error fetching {metric_name}: {e}")
        return pd.DataFrame()


# ============================================================================
# PUBLIC API FUNCTIONS
# ============================================================================

def fetch_mvrv_ratio(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch MVRV Ratio (Market Value to Realized Value) from Glassnode.
    
    MVRV > 1: Market value exceeds realized value (potential overvaluation)
    MVRV < 1: Market value below realized value (potential undervaluation)
    
    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        pd.DataFrame: Columns ['date', 'mvrv_ratio']
    """
    return _fetch_glassnode_metric('market/mvrv', 'mvrv_ratio', start_date, end_date)


def fetch_sopr(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch SOPR (Spent Output Profit Ratio) from Glassnode.
    
    SOPR > 1: Coins moved at profit
    SOPR < 1: Coins moved at loss
    SOPR = 1: Coins moved at break-even
    
    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        pd.DataFrame: Columns ['date', 'sopr']
    """
    return _fetch_glassnode_metric('indicators/sopr', 'sopr', start_date, end_date)


def fetch_active_addresses(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch Active Addresses count from Glassnode.
    
    Number of unique addresses that were active in the network as sender or receiver.
    
    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        pd.DataFrame: Columns ['date', 'active_addresses']
    """
    return _fetch_glassnode_metric('addresses/active_count', 'active_addresses', start_date, end_date)


def fetch_hash_rate(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch Hash Rate (mean) from Glassnode.
    
    Network hash rate in Exahashes per second (EH/s).
    
    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        pd.DataFrame: Columns ['date', 'hash_rate_eh']
    """
    df = _fetch_glassnode_metric('mining/hash_rate_mean', 'hash_rate_eh', start_date, end_date)
    
    # Convert from H/s to EH/s (1 EH = 10^18 H)
    if not df.empty and 'hash_rate_eh' in df.columns:
        df['hash_rate_eh'] = df['hash_rate_eh'] / 1e18
    
    return df


def fetch_lth_supply(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch Long-Term Holder Supply from Glassnode.
    
    Total supply held by long-term holders (coins held > 155 days).
    
    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        pd.DataFrame: Columns ['date', 'lth_supply_btc']
    """
    return _fetch_glassnode_metric('supply/lth_sum', 'lth_supply_btc', start_date, end_date)


def fetch_nvt_ratio(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch NVT Ratio (Network Value to Transactions) from Glassnode.
    
    NVT = Market Cap / Daily Transaction Volume (in USD)
    High NVT: Network is overvalued relative to transaction volume
    Low NVT: Network is undervalued relative to transaction volume
    
    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        pd.DataFrame: Columns ['date', 'nvt_ratio']
    """
    return _fetch_glassnode_metric('indicators/nvt', 'nvt_ratio', start_date, end_date)


def fetch_all_metrics(start_date: str, end_date: str) -> dict[str, pd.DataFrame]:
    """
    Fetch all available on-chain metrics.
    
    Args:
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        dict: {metric_name: pd.DataFrame} for each metric
    """
    logger.info(f"Fetching all on-chain metrics from {start_date} to {end_date}")
    
    return {
        'mvrv_ratio': fetch_mvrv_ratio(start_date, end_date),
        'sopr': fetch_sopr(start_date, end_date),
        'active_addresses': fetch_active_addresses(start_date, end_date),
        'hash_rate': fetch_hash_rate(start_date, end_date),
        'lth_supply': fetch_lth_supply(start_date, end_date),
        'nvt_ratio': fetch_nvt_ratio(start_date, end_date),
    }
