"""
Bitcoin Price Data Management Module - Data Architect Edition

Features:
- Automatic gap detection and filling
- Multi-source data fetching (CryptoDataDownload, CoinGecko, Yahoo, Binance)
- Intelligent incremental updates
- Live price integration

Data Flow:
1. Load local CSV history
2. Detect any gaps in date sequence
3. Fill gaps from CoinGecko/Yahoo
4. Update today with live Binance price
5. Save merged dataset
"""

import os
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)

# Portable path configuration
BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "bitcoin_price_history.csv")

# Gap detection threshold (days)
GAP_THRESHOLD = 2  # More than 1 day between records = gap


# =============================================================================
# CORE DATA FUNCTIONS
# =============================================================================

def load_local_history() -> Optional[pd.DataFrame]:
    """
    Load Bitcoin price history from local CSV file.
    
    Returns:
        pd.DataFrame: Historical price data, or None if file doesn't exist/is empty.
    """
    try:
        if not os.path.exists(CSV_PATH):
            logger.warning(f"Local history file not found: {CSV_PATH}")
            return None
        
        df = pd.read_csv(CSV_PATH)
        
        if df.empty:
            logger.warning("Local history file is empty")
            return None
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df = df.drop_duplicates(subset=['date'], keep='last')
        
        logger.info(f"Loaded {len(df)} records from local history ({df['date'].min().date()} to {df['date'].max().date()})")
        return df
        
    except Exception as e:
        logger.error(f"Error loading local history: {e}")
        return None


def save_history(df: pd.DataFrame) -> bool:
    """
    Save Bitcoin price history to local CSV file.
    
    Returns:
        bool: True if save successful, False otherwise.
    """
    try:
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        
        # Clean before saving
        df = df.sort_values('date')
        df = df.drop_duplicates(subset=['date'], keep='last')
        df = df.reset_index(drop=True)
        
        df.to_csv(CSV_PATH, index=False)
        logger.info(f"Saved {len(df)} records to {CSV_PATH}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving history: {e}")
        return False


# =============================================================================
# GAP DETECTION
# =============================================================================

def detect_gaps(df: pd.DataFrame, max_gap_days: int = GAP_THRESHOLD) -> List[Tuple[datetime, datetime]]:
    """
    Detect gaps in date sequence.
    
    Args:
        df: DataFrame with 'date' column
        max_gap_days: Maximum allowed gap (default 2 = 1 missing day is OK)
    
    Returns:
        List of (start_date, end_date) tuples representing gaps
    """
    if df is None or df.empty or len(df) < 2:
        return []
    
    df = df.sort_values('date')
    gaps = []
    
    for i in range(1, len(df)):
        prev_date = df['date'].iloc[i-1]
        curr_date = df['date'].iloc[i]
        diff_days = (curr_date - prev_date).days
        
        if diff_days > max_gap_days:
            gap_start = prev_date + timedelta(days=1)
            gap_end = curr_date - timedelta(days=1)
            gaps.append((gap_start, gap_end))
            logger.warning(f"Gap detected: {gap_start.date()} to {gap_end.date()} ({diff_days - 1} days missing)")
    
    # Check if we're missing recent days (up to yesterday)
    yesterday = pd.Timestamp.now().normalize() - timedelta(days=1)
    last_date = df['date'].max()
    
    if (yesterday - last_date).days >= max_gap_days:
        gap_start = last_date + timedelta(days=1)
        gap_end = yesterday
        gaps.append((gap_start, gap_end))
        logger.warning(f"Recent gap detected: {gap_start.date()} to {gap_end.date()} ({(gap_end - gap_start).days + 1} days missing)")
    
    return gaps


# =============================================================================
# DATA FETCHERS
# =============================================================================

def fetch_from_coingecko(start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
    """
    Fetch Bitcoin price data from CoinGecko API for a specific date range.
    
    Args:
        start_date: Start of range
        end_date: End of range
    
    Returns:
        DataFrame with 'date' and 'price' columns, or None if fetch fails.
    """
    try:
        # Calculate days needed
        days = (end_date - start_date).days + 2  # +2 for buffer
        days = min(days, 365)  # CoinGecko max for daily data
        
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }
        
        logger.info(f"Fetching {days} days from CoinGecko...")
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'prices' not in data or not data['prices']:
            logger.error("CoinGecko response missing 'prices' field")
            return None
        
        df = pd.DataFrame(data['prices'], columns=['timestamp_ms', 'price'])
        df['date'] = pd.to_datetime(df['timestamp_ms'], unit='ms').dt.normalize()
        df = df[['date', 'price']].copy()
        df = df.sort_values('date')
        df = df.drop_duplicates(subset=['date'], keep='last')
        
        # Filter to requested range
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        logger.info(f"Fetched {len(df)} records from CoinGecko ({df['date'].min().date()} to {df['date'].max().date()})")
        return df
        
    except requests.exceptions.Timeout:
        logger.error("CoinGecko API timeout")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"CoinGecko API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching from CoinGecko: {e}")
        return None


def fetch_from_yahoo(start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
    """
    Fetch Bitcoin price data from Yahoo Finance for a specific date range.
    
    Args:
        start_date: Start of range
        end_date: End of range
    
    Returns:
        DataFrame with 'date' and 'price' columns, or None if fetch fails.
    """
    try:
        logger.info(f"Fetching from Yahoo Finance ({start_date.date()} to {end_date.date()})...")
        
        btc = yf.Ticker("BTC-USD")
        df = btc.history(start=start_date, end=end_date + timedelta(days=1))
        
        if df is None or df.empty:
            logger.warning("Yahoo Finance returned no data")
            return None
        
        df = df.reset_index()
        if 'Date' in df.columns:
            df = df.rename(columns={'Date': 'date'})
        
        df = df[['date', 'Close']].copy()
        df = df.rename(columns={'Close': 'price'})
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None).dt.normalize()
        df = df.sort_values('date')
        df = df.drop_duplicates(subset=['date'], keep='last')
        
        logger.info(f"Fetched {len(df)} records from Yahoo Finance")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching from Yahoo Finance: {e}")
        return None


def fetch_live_binance_data(limit: int = 60) -> Optional[pd.DataFrame]:
    """
    Fetch live 1-minute Bitcoin price data from Binance API.
    
    Args:
        limit: Number of recent 1-minute candles to fetch. Default is 60 (last hour).
    
    Returns:
        DataFrame with 'timestamp' and 'price' columns, or None if fetch fails.
    """
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': 'BTCUSDT',
            'interval': '1m',
            'limit': limit
        }
        
        logger.info(f"Fetching live data from Binance (last {limit} minutes)...")
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            logger.error("Binance returned no data")
            return None
        
        df = pd.DataFrame(data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 
                                         'close_time', 'quote_volume', 'trades', 'taker_buy_base', 
                                         'taker_buy_quote', 'ignore'])
        
        df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
        df['price'] = df['close'].astype(float)
        df = df[['timestamp', 'price']].copy()
        
        logger.info(f"Fetched {len(df)} minute candles from Binance (latest: ${df['price'].iloc[-1]:,.2f})")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching from Binance: {e}")
        return None


def download_full_bitcoin_history(start_date: str = "2014-09-17") -> Optional[pd.DataFrame]:
    """
    Download full Bitcoin price history from CryptoDataDownload (Bitstamp data).
    Falls back to Yahoo Finance if CDD fails.
    
    Returns:
        DataFrame: Historical price data, or None if download fails.
    """
    try:
        url = "https://www.cryptodatadownload.com/cdd/Bitstamp_BTCUSD_d.csv"
        
        logger.info("Downloading full Bitcoin history from CryptoDataDownload...")
        
        df = pd.read_csv(url, skiprows=1)
        
        if df is None or df.empty:
            raise ValueError("CryptoDataDownload returned no data")
        
        logger.info(f"Downloaded {len(df)} records from CryptoDataDownload")
        
        df.columns = df.columns.str.strip()
        
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'date' in col_lower and 'date' not in column_mapping:
                column_mapping[col] = 'date'
            elif 'close' in col_lower and 'price' not in column_mapping:
                column_mapping[col] = 'price'
        
        if 'date' not in column_mapping.values() or 'price' not in column_mapping.values():
            raise ValueError(f"Could not find date/close columns. Available: {df.columns.tolist()}")
        
        df = df.rename(columns=column_mapping)
        df = df[['date', 'price']].copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.dropna(subset=['price'])
        df = df.sort_values('date', ascending=True)
        df = df.drop_duplicates(subset=['date'], keep='last')
        
        logger.info(f"Cleaned data: {len(df)} records ({df['date'].min().date()} to {df['date'].max().date()})")
        
        save_history(df)
        return df
        
    except Exception as e:
        logger.warning(f"CryptoDataDownload failed: {e}. Trying Yahoo Finance...")
        
        try:
            btc = yf.Ticker("BTC-USD")
            df = btc.history(period='max')
            
            if df is None or df.empty:
                logger.error("Yahoo Finance fallback also failed")
                return None
            
            df = df.reset_index()
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'date'})
            df = df[['date', 'Close']].copy()
            df = df.rename(columns={'Close': 'price'})
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None).dt.normalize()
            df = df.sort_values('date')
            
            logger.info(f"Yahoo Finance fallback: {len(df)} records ({df['date'].min().date()} to {df['date'].max().date()})")
            
            save_history(df)
            return df
            
        except Exception as fallback_err:
            logger.error(f"Yahoo Finance fallback error: {fallback_err}")
            return None


# =============================================================================
# GAP FILLING
# =============================================================================

def fill_gaps(df: pd.DataFrame, gaps: List[Tuple[datetime, datetime]]) -> pd.DataFrame:
    """
    Fill detected gaps in the dataset using multiple data sources.
    
    Args:
        df: Existing DataFrame
        gaps: List of (start_date, end_date) tuples
    
    Returns:
        DataFrame with gaps filled
    """
    if not gaps:
        logger.info("No gaps to fill")
        return df
    
    logger.info(f"Attempting to fill {len(gaps)} gap(s)...")
    
    filled_data = []
    
    for gap_start, gap_end in gaps:
        logger.info(f"Filling gap: {gap_start.date()} to {gap_end.date()}")
        
        # Try CoinGecko first
        gap_df = fetch_from_coingecko(gap_start, gap_end)
        
        if gap_df is None or gap_df.empty:
            # Fallback to Yahoo Finance
            gap_df = fetch_from_yahoo(gap_start, gap_end)
        
        if gap_df is not None and not gap_df.empty:
            filled_data.append(gap_df)
            logger.info(f"Filled {len(gap_df)} records for gap")
        else:
            logger.warning(f"Could not fill gap: {gap_start.date()} to {gap_end.date()}")
    
    if filled_data:
        # Merge all filled data with original
        all_data = [df] + filled_data
        merged = pd.concat(all_data, ignore_index=True)
        merged = merged.sort_values('date')
        merged = merged.drop_duplicates(subset=['date'], keep='last')
        merged = merged.reset_index(drop=True)
        
        logger.info(f"Merged dataset: {len(merged)} records (was {len(df)})")
        return merged
    
    return df


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def get_bitcoin_price_series(include_live: bool = True, auto_fill_gaps: bool = True) -> Optional[pd.DataFrame]:
    """
    Get complete Bitcoin price series with automatic gap detection and filling.
    
    This is the main function for getting price data. It will:
    1. Load existing local history
    2. Detect any gaps in date sequence
    3. Fill gaps from CoinGecko/Yahoo (if auto_fill_gaps=True)
    4. Update today with live Binance price (if include_live=True)
    5. Save merged dataset
    
    Args:
        include_live: Whether to include live Binance data. Default is True.
        auto_fill_gaps: Whether to automatically fill detected gaps. Default is True.
    
    Returns:
        DataFrame with 'date' and 'price' columns, or None if all sources fail.
    """
    try:
        # 1. Load local history
        local_df = load_local_history()
        
        if local_df is None or local_df.empty:
            logger.warning("No local history available, downloading full history...")
            local_df = download_full_bitcoin_history()
            if local_df is None or local_df.empty:
                logger.error("Cannot load or download historical data")
                return None
        
        # 2. Detect gaps
        gaps = detect_gaps(local_df)
        
        # 3. Fill gaps if requested
        if auto_fill_gaps and gaps:
            logger.info(f"Detected {len(gaps)} gap(s) in data, filling automatically...")
            local_df = fill_gaps(local_df, gaps)
        
        # 4. Fetch live data from Binance
        if include_live:
            live_df = fetch_live_binance_data(limit=60)
            
            if live_df is not None and not live_df.empty:
                latest_live_price = live_df['price'].iloc[-1]
                latest_live_time = live_df['timestamp'].iloc[-1]
                
                logger.info(f"Live price: ${latest_live_price:,.2f} at {latest_live_time}")
                
                # Update today's price
                today = pd.Timestamp.now().normalize()
                
                if today in local_df['date'].values:
                    local_df.loc[local_df['date'] == today, 'price'] = latest_live_price
                    logger.info(f"Updated today's price with live data")
                else:
                    new_row = pd.DataFrame({'date': [today], 'price': [latest_live_price]})
                    local_df = pd.concat([local_df, new_row], ignore_index=True)
                    local_df = local_df.sort_values('date')
                    logger.info(f"Added today's price with live data")
        
        # 5. Save updated history
        save_history(local_df)
        
        logger.info(f"Complete series: {len(local_df)} records ({local_df['date'].min().date()} to {local_df['date'].max().date()})")
        return local_df
        
    except Exception as e:
        logger.error(f"Error in get_bitcoin_price_series: {e}")
        import traceback
        traceback.print_exc()
        return None


# =============================================================================
# BACKWARDS COMPATIBILITY
# =============================================================================

def load_from_csv(filename: str = "data/bitcoin_price.csv") -> Optional[pd.DataFrame]:
    """Legacy function for backwards compatibility."""
    df = load_local_history()
    if df is not None:
        df = df.set_index('date')
    return df


def refresh_bitcoin_data(days: int = 365) -> tuple:
    """Legacy function for backwards compatibility."""
    df = get_bitcoin_price_series()
    
    if df is None:
        return None, "Failed to fetch Bitcoin price data"
    
    df_indexed = df.set_index('date')
    return df_indexed, None


def fetch_recent_from_coingecko(days: int = 7) -> Optional[pd.DataFrame]:
    """Legacy function for backwards compatibility."""
    end_date = pd.Timestamp.now().normalize()
    start_date = end_date - timedelta(days=days)
    return fetch_from_coingecko(start_date, end_date)
