"""
Bitcoin Price Data Management Module
Manages full historical data with local CSV storage and incremental CoinGecko updates.
"""

import os
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import Optional
from utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)

# Portable path configuration
BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "bitcoin_price_history.csv")


def load_local_history() -> Optional[pd.DataFrame]:
    """
    Load Bitcoin price history from local CSV file.
    
    Returns:
        pd.DataFrame: Historical price data with 'date' index, or None if file doesn't exist/is empty.
    """
    try:
        if not os.path.exists(CSV_PATH):
            logger.warning(f"📂 Local history file not found: {CSV_PATH}")
            return None
        
        df = pd.read_csv(CSV_PATH)
        
        if df.empty:
            logger.warning("⚠️ Local history file is empty")
            return None
        
        # Parse date column and set as index
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df = df.drop_duplicates(subset=['date'], keep='last')
        
        logger.info(f"✅ Loaded {len(df)} records from local history ({df['date'].min()} to {df['date'].max()})")
        return df
        
    except Exception as e:
        logger.error(f"❌ Error loading local history: {e}")
        return None


def download_full_bitcoin_history(start_date: str = "2014-09-17") -> Optional[pd.DataFrame]:
    """
    Download full Bitcoin price history from CryptoDataDownload (Bitstamp data).
    
    Args:
        start_date (str): Kept for API compatibility but not used (CDD provides full history).
    
    Returns:
        pd.DataFrame: Historical price data, or None if download fails.
    """
    try:
        # CryptoDataDownload URL for Bitstamp BTC/USD daily data (longest history)
        url = "https://www.cryptodatadownload.com/cdd/Bitstamp_BTCUSD_d.csv"
        
        logger.info(f"📡 Downloading full Bitcoin history from CryptoDataDownload (Bitstamp)...")
        
        # Download CSV, skip first row (header disclaimer)
        df = pd.read_csv(url, skiprows=1)
        
        if df is None or df.empty:
            logger.error("❌ CryptoDataDownload returned no data")
            return None
        
        logger.info(f"✅ Downloaded {len(df)} records from CryptoDataDownload")
        
        # Inspect and clean columns
        # Expected columns: ["unix", "date", "symbol", "open", "high", "low", "close", "Volume BTC", ...]
        # Column names might vary, so we'll be flexible
        
        # Find the date and close columns (case-insensitive)
        df.columns = df.columns.str.strip()  # Remove whitespace
        
        # Map common column names
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'date' in col_lower and 'date' not in column_mapping:
                column_mapping[col] = 'date'
            elif 'close' in col_lower and 'price' not in column_mapping:
                column_mapping[col] = 'price'
        
        if 'date' not in column_mapping.values() or 'price' not in column_mapping.values():
            logger.error(f"❌ Could not find date/close columns. Available: {df.columns.tolist()}")
            return None
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Keep only date and price
        df = df[['date', 'price']].copy()
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Remove any rows with NaN prices
        df = df.dropna(subset=['price'])
        
        # Sort by date ascending (CDD is often descending)
        df = df.sort_values('date', ascending=True)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['date'], keep='last')
        
        logger.info(f"✅ Cleaned data: {len(df)} records ({df['date'].min()} to {df['date'].max()})")
        
        # Save to CSV
        try:
            os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
            df.to_csv(CSV_PATH, index=False)
            logger.info(f"💾 Saved full history to {CSV_PATH}")
        except PermissionError:
            logger.error(f"❌ Permission denied writing to {CSV_PATH}")
        except Exception as save_err:
            logger.error(f"❌ Error saving full history: {save_err}")
        
        return df
        
    except pd.errors.ParserError as e:
        logger.error(f"❌ CSV parsing error from CryptoDataDownload: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error downloading from CryptoDataDownload: {e}")
        # Fallback: try with yfinance as backup
        try:
            logger.info("⚠️ Attempting fallback to yfinance...")
            btc = yf.Ticker("BTC-USD")
            # Use period='max' to get maximum available history
            df = btc.history(period='max')
            
            if df is None or df.empty:
                logger.error("❌ yfinance fallback also failed")
                return None
            
            df = df.reset_index()
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'date'})
            df = df[['date', 'Close']].copy()
            df = df.rename(columns={'Close': 'price'})
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            logger.info(f"✅ Fallback successful: {len(df)} records from yfinance (from {df['date'].min()} to {df['date'].max()})")
            
            # Save to CSV
            try:
                os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
                df.to_csv(CSV_PATH, index=False)
                logger.info(f"💾 Saved full history to {CSV_PATH}")
            except Exception as save_err:
                logger.error(f"❌ Error saving: {save_err}")
            
            return df
        except Exception as fallback_err:
            logger.error(f"❌ yfinance fallback error: {fallback_err}")
            return None


def fetch_recent_from_coingecko(days: int = 7) -> Optional[pd.DataFrame]:
    """
    Fetch recent Bitcoin price data from CoinGecko API.
    
    Args:
        days (int): Number of recent days to fetch. Default is 7.
    
    Returns:
        pd.DataFrame: Recent price data with 'date' and 'price' columns, or None if fetch fails.
    """
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }
        
        logger.info(f"📡 Fetching {days} days from CoinGecko API...")
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'prices' not in data or not data['prices']:
            logger.error("❌ CoinGecko response missing 'prices' field")
            return None
        
        # Build DataFrame from prices list
        df = pd.DataFrame(data['prices'], columns=['timestamp_ms', 'price_usd'])
        
        # Convert timestamp to date
        df['date'] = pd.to_datetime(df['timestamp_ms'], unit='ms').dt.date
        df['date'] = pd.to_datetime(df['date'])
        
        # Keep only date and price, rename for consistency
        df = df[['date', 'price_usd']].copy()
        df = df.rename(columns={'price_usd': 'price'})
        df = df.sort_values('date')
        
        logger.info(f"✅ Fetched {len(df)} records from CoinGecko ({df['date'].min()} to {df['date'].max()})")
        return df
        
    except requests.exceptions.Timeout:
        logger.error("❌ CoinGecko API timeout (>10s)")
        return None
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"❌ CoinGecko API HTTP error: {http_err}")
        return None
    except Exception as e:
        logger.error(f"❌ Error fetching from CoinGecko: {e}")
        return None


def save_history(df: pd.DataFrame) -> None:
    """
    Save Bitcoin price history to local CSV file.
    
    Args:
        df (pd.DataFrame): Price data to save.
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        
        # Save to CSV
        df.to_csv(CSV_PATH, index=False)
        logger.info(f"💾 Saved {len(df)} records to {CSV_PATH}")
        
    except PermissionError:
        logger.error(f"❌ Permission denied writing to {CSV_PATH}")
    except Exception as e:
        logger.error(f"❌ Error saving history: {e}")


def fetch_live_binance_data(limit: int = 60) -> Optional[pd.DataFrame]:
    """
    Fetch live 1-minute Bitcoin price data from Binance API.
    
    Args:
        limit (int): Number of recent 1-minute candles to fetch. Default is 60 (last hour).
    
    Returns:
        pd.DataFrame: Recent minute data with 'timestamp' and 'price' columns, or None if fetch fails.
    """
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': 'BTCUSDT',
            'interval': '1m',
            'limit': limit
        }
        
        logger.info(f"📡 Fetching live data from Binance (last {limit} minutes)...")
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            logger.error("❌ Binance returned no data")
            return None
        
        # Binance klines format: [open_time, open, high, low, close, volume, close_time, ...]
        # We want: timestamp and close price
        df = pd.DataFrame(data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 
                                         'close_time', 'quote_volume', 'trades', 'taker_buy_base', 
                                         'taker_buy_quote', 'ignore'])
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
        
        # Keep only timestamp and close price
        df['price'] = df['close'].astype(float)
        df = df[['timestamp', 'price']].copy()
        
        logger.info(f"✅ Fetched {len(df)} minute candles from Binance (latest: ${df['price'].iloc[-1]:,.2f})")
        return df
        
    except requests.exceptions.Timeout:
        logger.error("❌ Binance API timeout (>10s)")
        return None
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"❌ Binance API HTTP error: {http_err}")
        return None
    except Exception as e:
        logger.error(f"❌ Error fetching from Binance: {e}")
        return None


def get_bitcoin_price_series(include_live: bool = True) -> Optional[pd.DataFrame]:
    """
    Get complete Bitcoin price series by merging local history with live Binance data.
    
    This is the main function to use for getting price data. It will:
    1. Load existing local history (daily data)
    2. Fetch live minute data from Binance (last hour)
    3. Update the last daily candle with the latest live price
    4. Return the merged dataset
    
    Args:
        include_live (bool): Whether to include live Binance data. Default is True.
    
    Returns:
        pd.DataFrame: Complete price series with 'date' and 'price' columns, or None if all sources fail.
    """
    try:
        # Load local history (daily data)
        local_df = load_local_history()
        
        if local_df is None or local_df.empty:
            logger.warning("⚠️ No local history available")
            # Try to download full history first
            local_df = download_full_bitcoin_history()
            if local_df is None or local_df.empty:
                logger.error("❌ Cannot load or download historical data")
                return None
        
        # Fetch live data from Binance if requested
        if include_live:
            live_df = fetch_live_binance_data(limit=60)
            
            if live_df is not None and not live_df.empty:
                # Get the latest live price
                latest_live_price = live_df['price'].iloc[-1]
                latest_live_time = live_df['timestamp'].iloc[-1]
                
                logger.info(f"🔴 Live price: ${latest_live_price:,.2f} at {latest_live_time}")
                
                # Update today's price in the historical data
                today = pd.Timestamp.now().normalize()
                
                # Check if we have today's date in history
                if today in local_df['date'].values:
                    # Update existing row
                    local_df.loc[local_df['date'] == today, 'price'] = latest_live_price
                    logger.info(f"✅ Updated today's price with live data: ${latest_live_price:,.2f}")
                else:
                    # Append new row for today
                    new_row = pd.DataFrame({'date': [today], 'price': [latest_live_price]})
                    local_df = pd.concat([local_df, new_row], ignore_index=True)
                    local_df = local_df.sort_values('date')
                    logger.info(f"✅ Added today's price with live data: ${latest_live_price:,.2f}")
                
                # Save updated history
                save_history(local_df)
            else:
                logger.warning("⚠️ Live data fetch failed, using historical data only")
        
        logger.info(f"✅ Complete series: {len(local_df)} records ({local_df['date'].min()} to {local_df['date'].max()})")
        return local_df
        
    except Exception as e:
        logger.error(f"❌ Error in get_bitcoin_price_series: {e}")
        return None


# Backwards compatibility functions for existing code
def load_from_csv(filename: str = "data/bitcoin_price.csv") -> Optional[pd.DataFrame]:
    """
    Legacy function for backwards compatibility.
    Loads from the new history file and returns with date index.
    
    Args:
        filename (str): Ignored, kept for API compatibility.
    
    Returns:
        pd.DataFrame: Price data with date index, or None.
    """
    df = load_local_history()
    if df is not None:
        df = df.set_index('date')
    return df


def refresh_bitcoin_data(days: int = 365) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Legacy function for backwards compatibility.
    Refreshes data using the new system and returns indexed DataFrame.
    
    Args:
        days (int): Ignored, kept for API compatibility. Always fetches complete history.
    
    Returns:
        tuple: (DataFrame with date index, error message or None)
    """
    df = get_bitcoin_price_series()
    
    if df is None:
        return None, "Failed to fetch Bitcoin price data"
    
    # Return with date index for compatibility
    df_indexed = df.set_index('date')
    return df_indexed, None
