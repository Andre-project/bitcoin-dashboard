"""
Blockchain.com API Data Collectors

Fetches Bitcoin on-chain metrics from Blockchain.com Charts API.
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
BLOCKCHAIN_BASE_URL = "https://api.blockchain.info/charts"
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


def _fetch_blockchain_chart(chart_name: str, metric_col: str) -> pd.DataFrame:
    """
    Generic fetcher for Blockchain.com charts API.
    
    Args:
        chart_name: Name of the chart (e.g., 'n-unique-addresses')
        metric_col: Name for the metric column in output
    
    Returns:
        pd.DataFrame with columns ['date', metric_col]
    """
    url = f"{BLOCKCHAIN_BASE_URL}/{chart_name}"
    params = {
        'timespan': '1year',
        'format': 'json'
    }
    
    logger.info(f"Fetching {chart_name} from Blockchain.com...")
    
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if not data or 'values' not in data:
            logger.warning(f"Empty or invalid response for {chart_name}")
            return pd.DataFrame()
        
        # Parse response - format: {"values": [{"x": timestamp, "y": value}, ...]}
        records = []
        for item in data['values']:
            x_val = item.get('x')
            y_val = item.get('y')
            if x_val is not None and y_val is not None:
                records.append({
                    'date': pd.to_datetime(x_val, unit='s', utc=True),
                    metric_col: float(y_val)
                })
        
        if not records:
            logger.warning(f"No data parsed for {chart_name}")
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df = df.sort_values('date').drop_duplicates(subset=['date'], keep='last')
        
        logger.info(f"Fetched {len(df)} records for {chart_name}")
        return df
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {chart_name}")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching {chart_name}: {e}")
        return pd.DataFrame()
    except ValueError as e:
        logger.error(f"JSON parsing error for {chart_name}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error fetching {chart_name}: {e}")
        return pd.DataFrame()


def fetch_active_addresses(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch unique active addresses from Blockchain.com with 24h caching.
    
    Args:
        start_date: Format 'YYYY-MM-DD'
        end_date: Format 'YYYY-MM-DD'
    
    Returns:
        pd.DataFrame: Columns ['date', 'active_addresses']
                     index DatetimeIndex (UTC)
    """
    cache_path = _get_cache_path("active_addresses")
    
    # Check cache first
    if _is_cache_valid(cache_path):
        cached_df = _load_from_cache(cache_path)
        if cached_df is not None and not cached_df.empty:
            return _filter_by_date(cached_df, start_date, end_date)
    
    # Fetch from API
    df = _fetch_blockchain_chart('n-unique-addresses', 'active_addresses')
    
    if not df.empty:
        df['active_addresses'] = df['active_addresses'].astype(int)
        _save_to_cache(df, cache_path)
        return _filter_by_date(df, start_date, end_date)
    
    return pd.DataFrame()


def fetch_transaction_count(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch daily transaction count from Blockchain.com with 24h caching.
    
    Args:
        start_date: Format 'YYYY-MM-DD'
        end_date: Format 'YYYY-MM-DD'
    
    Returns:
        pd.DataFrame: Columns ['date', 'tx_count']
                     index DatetimeIndex (UTC)
    """
    cache_path = _get_cache_path("tx_count")
    
    # Check cache first
    if _is_cache_valid(cache_path):
        cached_df = _load_from_cache(cache_path)
        if cached_df is not None and not cached_df.empty:
            return _filter_by_date(cached_df, start_date, end_date)
    
    # Fetch from API
    df = _fetch_blockchain_chart('n-transactions', 'tx_count')
    
    if not df.empty:
        df['tx_count'] = df['tx_count'].astype(int)
        _save_to_cache(df, cache_path)
        return _filter_by_date(df, start_date, end_date)
    
    return pd.DataFrame()


def fetch_miners_revenue(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch miners revenue (USD) from Blockchain.com with 24h caching.
    
    Args:
        start_date: Format 'YYYY-MM-DD'
        end_date: Format 'YYYY-MM-DD'
    
    Returns:
        pd.DataFrame: Columns ['date', 'revenue_usd']
                     index DatetimeIndex (UTC)
    """
    cache_path = _get_cache_path("miners_revenue")
    
    # Check cache first
    if _is_cache_valid(cache_path):
        cached_df = _load_from_cache(cache_path)
        if cached_df is not None and not cached_df.empty:
            return _filter_by_date(cached_df, start_date, end_date)
    
    # Fetch from API
    df = _fetch_blockchain_chart('miners-revenue', 'revenue_usd')
    
    if not df.empty:
        _save_to_cache(df, cache_path)
        return _filter_by_date(df, start_date, end_date)
    
    return pd.DataFrame()


def fetch_nvt_ratio(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Calculate NVT Ratio (Market Cap / Transaction Volume USD) with 24h caching.
    
    NVT = Network Value to Transactions ratio.
    High NVT: Network overvalued relative to transaction volume.
    Low NVT: Network undervalued relative to transaction volume.
    
    Args:
        start_date: Format 'YYYY-MM-DD'
        end_date: Format 'YYYY-MM-DD'
    
    Returns:
        pd.DataFrame: Columns ['date', 'nvt_ratio']
                     index DatetimeIndex (UTC)
    """
    cache_path = _get_cache_path("nvt_ratio")
    
    # Check cache first
    if _is_cache_valid(cache_path):
        cached_df = _load_from_cache(cache_path)
        if cached_df is not None and not cached_df.empty:
            return _filter_by_date(cached_df, start_date, end_date)
    
    # Fetch market cap
    df_market_cap = _fetch_blockchain_chart('market-cap', 'market_cap')
    if df_market_cap.empty:
        logger.error("Failed to fetch market cap for NVT calculation")
        return pd.DataFrame()
    
    # Fetch transaction volume
    df_tx_volume = _fetch_blockchain_chart('estimated-transaction-volume-usd', 'tx_volume')
    if df_tx_volume.empty:
        logger.error("Failed to fetch transaction volume for NVT calculation")
        return pd.DataFrame()
    
    # Merge on date
    try:
        df_market_cap['date_str'] = df_market_cap['date'].dt.strftime('%Y-%m-%d')
        df_tx_volume['date_str'] = df_tx_volume['date'].dt.strftime('%Y-%m-%d')
        
        df_merged = pd.merge(
            df_market_cap[['date', 'date_str', 'market_cap']],
            df_tx_volume[['date_str', 'tx_volume']],
            on='date_str',
            how='inner'
        )
        
        if df_merged.empty:
            logger.warning("No matching dates between market cap and tx volume")
            return pd.DataFrame()
        
        # Calculate NVT ratio (avoid division by zero)
        df_merged['nvt_ratio'] = df_merged.apply(
            lambda row: row['market_cap'] / row['tx_volume'] if row['tx_volume'] > 0 else None,
            axis=1
        )
        
        # Clean up
        df = df_merged[['date', 'nvt_ratio']].dropna()
        df = df.sort_values('date').drop_duplicates(subset=['date'], keep='last')
        
        logger.info(f"Calculated {len(df)} NVT ratio records")
        
        # Save to cache
        _save_to_cache(df, cache_path)
        
        return _filter_by_date(df, start_date, end_date)
        
    except Exception as e:
        logger.error(f"Error calculating NVT ratio: {e}")
        return pd.DataFrame()
