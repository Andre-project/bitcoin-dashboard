"""
Treasury Data Management Module

Fetches and manages Bitcoin treasury data from BTC-Treasury GitHub repository.
Tracks BTC holdings by category: mining companies, countries, DeFi, ETFs,
private companies, and public companies.

Features:
- Intelligent caching with 6-hour expiration
- Fallback to expired cache on network errors
- GitHub API integration for update checking
- Robust error handling

Interface Contract:
    All data functions return pd.DataFrame
    Returns empty DataFrame on unrecoverable error
    Cache stored in data/treasury_cache.csv
"""

import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# GitHub raw CSV URL
TREASURY_CSV_URL = "https://raw.githubusercontent.com/Andre-project/BTC-Treasury/main/category_btc-treasuries.csv"

# GitHub API for checking updates
GITHUB_API_URL = "https://api.github.com/repos/Andre-project/BTC-Treasury/commits"

# Cache configuration
CACHE_DIR = Path(os.path.dirname(__file__)).parent / "data"
CACHE_FILE = CACHE_DIR / "treasury_cache.csv"
CACHE_DURATION = timedelta(hours=6)

# Request configuration
REQUEST_TIMEOUT = 15

# Category column mapping (raw CSV name -> normalized name)
CATEGORY_COLUMNS = {
    "btc_mining_companies": "mining_companies",
    "countries": "countries",
    "defi": "defi",
    "etfs": "etfs",
    "private_companies": "private_companies",
    "public_companies": "public_companies"
}


# =============================================================================
# TREASURY DATA MANAGER CLASS
# =============================================================================

class TreasuryDataManager:
    """
    Manages Bitcoin treasury data with intelligent caching.
    
    This class handles loading, caching, and querying treasury data
    from the BTC-Treasury GitHub repository. The data tracks BTC
    holdings by category over time.
    
    Attributes:
        df: DataFrame containing treasury data
        last_update: Timestamp of last data refresh
    """
    
    def __init__(self) -> None:
        """Initialize the TreasuryDataManager."""
        self.df: Optional[pd.DataFrame] = None
        self.last_update: Optional[datetime] = None
        self._ensure_data_dir()
    
    def _ensure_data_dir(self) -> None:
        """Create the data directory if it doesn't exist."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Data directory ensured: {CACHE_DIR}")
    
    def _is_cache_valid(self) -> bool:
        """
        Check if the cache file exists and is less than CACHE_DURATION old.
        
        Returns:
            bool: True if cache is valid, False otherwise
        """
        if not CACHE_FILE.exists():
            logger.debug("Cache file does not exist")
            return False
        
        try:
            file_mtime = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
            age = datetime.now() - file_mtime
            is_valid = age < CACHE_DURATION
            logger.debug(f"Cache age: {age}, valid: {is_valid}")
            return is_valid
        except Exception as e:
            logger.warning(f"Error checking cache validity: {e}")
            return False
    
    def _get_cache_age_hours(self) -> float:
        """
        Get the age of the cache in hours.
        
        Returns:
            float: Age in hours, or -1 if cache doesn't exist
        """
        if not CACHE_FILE.exists():
            return -1.0
        
        try:
            file_mtime = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
            age = datetime.now() - file_mtime
            return age.total_seconds() / 3600
        except Exception:
            return -1.0
    
    def _load_from_cache(self) -> Optional[pd.DataFrame]:
        """
        Load data from the cache file.
        
        Returns:
            pd.DataFrame or None if load fails
        """
        if not CACHE_FILE.exists():
            return None
        
        try:
            df = pd.read_csv(CACHE_FILE, parse_dates=["timestamp"])
            df = df.sort_values("timestamp", ascending=True)
            logger.info(f"Loaded {len(df)} records from cache")
            return df
        except Exception as e:
            logger.warning(f"Error loading from cache: {e}")
            return None
    
    def _save_to_cache(self, df: pd.DataFrame) -> bool:
        """
        Save DataFrame to the cache file.
        
        Args:
            df: DataFrame to save
            
        Returns:
            bool: True if save successful
        """
        try:
            df.to_csv(CACHE_FILE, index=False)
            logger.info(f"Saved {len(df)} records to cache: {CACHE_FILE}")
            return True
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
            return False
    
    def _download_from_github(self) -> Optional[pd.DataFrame]:
        """
        Download the CSV file from GitHub.
        
        Returns:
            pd.DataFrame or None if download fails
        """
        logger.info(f"Downloading treasury data from GitHub...")
        
        try:
            response = requests.get(TREASURY_CSV_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Parse CSV from response text
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            if df.empty:
                logger.warning("Empty CSV received from GitHub")
                return None
            
            logger.info(f"Downloaded {len(df)} records from GitHub")
            return df
            
        except requests.exceptions.Timeout:
            logger.error("Timeout downloading treasury data from GitHub")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error downloading treasury data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing treasury CSV: {e}")
            return None
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize the treasury data.
        
        Args:
            df: Raw DataFrame from CSV
            
        Returns:
            pd.DataFrame: Cleaned and normalized data
        """
        try:
            # Create a copy to avoid modifying original
            df = df.copy()
            
            # Normalize column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Parse timestamp
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            # Rename category columns if they exist
            rename_map = {}
            for raw_name, norm_name in CATEGORY_COLUMNS.items():
                if raw_name in df.columns:
                    rename_map[raw_name] = norm_name
            
            if rename_map:
                df = df.rename(columns=rename_map)
            
            # Ensure numeric columns are numeric
            for col in df.columns:
                if col != "timestamp":
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # Drop rows with all NaN values (except timestamp)
            value_cols = [c for c in df.columns if c != "timestamp"]
            df = df.dropna(subset=value_cols, how="all")
            
            # Sort by timestamp descending (most recent first)
            df = df.sort_values("timestamp", ascending=False)
            
            # Remove duplicate timestamps, keep latest
            df = df.drop_duplicates(subset=["timestamp"], keep="first")
            
            logger.info(f"Cleaned data: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            return pd.DataFrame()
    
    def load_data(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Load treasury data with intelligent caching.
        
        This method will:
        1. Return cached data if valid (< 6 hours old)
        2. Download fresh data from GitHub if cache is expired
        3. Fall back to expired cache if download fails
        4. Return empty DataFrame only if all sources fail
        
        Args:
            force_refresh: If True, ignore cache and download fresh data
            
        Returns:
            pd.DataFrame: Treasury data, or empty DataFrame on failure
        """
        # Check cache first (unless force refresh)
        if not force_refresh and self._is_cache_valid():
            cached_df = self._load_from_cache()
            if cached_df is not None and not cached_df.empty:
                self.df = cached_df
                self.last_update = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
                return self.df
        
        # Download fresh data
        raw_df = self._download_from_github()
        
        if raw_df is not None and not raw_df.empty:
            # Clean and save
            self.df = self._clean_data(raw_df)
            if not self.df.empty:
                self._save_to_cache(self.df)
                self.last_update = datetime.now()
                return self.df
        
        # Fallback to expired cache
        logger.warning("Download failed, attempting fallback to expired cache")
        cached_df = self._load_from_cache()
        if cached_df is not None and not cached_df.empty:
            self.df = cached_df
            self.last_update = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
            logger.warning(f"Using expired cache from {self.last_update}")
            return self.df
        
        # Complete failure
        logger.error("Failed to load treasury data from any source")
        self.df = pd.DataFrame()
        return self.df
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for treasury data.
        
        Returns:
            dict: Statistics including totals and metadata
                - total_categories: Number of categories tracked
                - total_btc: Total BTC across all categories (latest)
                - categories: Dict of category-wise BTC totals
                - last_update: Timestamp of last data refresh
                - cache_age_hours: Age of cache in hours
                - records_count: Number of records in dataset
        """
        if self.df is None or self.df.empty:
            self.load_data()
        
        if self.df is None or self.df.empty:
            return {
                "total_categories": 0,
                "total_btc": 0,
                "categories": {},
                "last_update": None,
                "cache_age_hours": -1,
                "records_count": 0
            }
        
        # Get latest row (most recent data)
        latest = self.df.iloc[0] if len(self.df) > 0 else pd.Series()
        
        # Calculate category totals from latest data
        categories = {}
        value_cols = [c for c in self.df.columns if c != "timestamp"]
        total_btc = 0
        
        for col in value_cols:
            if col in latest and pd.notna(latest[col]):
                categories[col] = int(latest[col])
                total_btc += int(latest[col])
        
        return {
            "total_categories": len(categories),
            "total_btc": total_btc,
            "categories": categories,
            "last_update": self.last_update,
            "cache_age_hours": round(self._get_cache_age_hours(), 2),
            "records_count": len(self.df)
        }
    
    def get_latest_holdings(self) -> pd.Series:
        """
        Get the latest BTC holdings for all categories.
        
        Returns:
            pd.Series: Latest holdings by category
        """
        if self.df is None or self.df.empty:
            self.load_data()
        
        if self.df is None or self.df.empty:
            return pd.Series()
        
        # Get most recent row
        latest = self.df.iloc[0]
        value_cols = [c for c in self.df.columns if c != "timestamp"]
        
        return latest[value_cols]
    
    def get_historical_data(self, days: int = 30) -> pd.DataFrame:
        """
        Get historical treasury data for a specified number of days.
        
        Args:
            days: Number of days of history to return
            
        Returns:
            pd.DataFrame: Historical data sorted by timestamp ascending
        """
        if self.df is None or self.df.empty:
            self.load_data()
        
        if self.df is None or self.df.empty:
            return pd.DataFrame()
        
        # Filter by date
        cutoff = datetime.now() - timedelta(days=days)
        df_filtered = self.df[self.df["timestamp"] >= cutoff].copy()
        
        # Sort ascending for time series
        return df_filtered.sort_values("timestamp", ascending=True)
    
    def get_category_trend(self, category: str, days: int = 30) -> pd.DataFrame:
        """
        Get the trend for a specific category over time.
        
        Args:
            category: Category name (e.g., 'etfs', 'public_companies')
            days: Number of days of history
            
        Returns:
            pd.DataFrame: Columns ['timestamp', category]
        """
        if self.df is None or self.df.empty:
            self.load_data()
        
        if self.df is None or self.df.empty or category not in self.df.columns:
            return pd.DataFrame()
        
        # Get historical data
        hist_df = self.get_historical_data(days)
        
        if hist_df.empty:
            return pd.DataFrame()
        
        return hist_df[["timestamp", category]].copy()
    
    def get_top_categories(self, n: int = 6) -> pd.DataFrame:
        """
        Get the top N categories by BTC holdings.
        
        Args:
            n: Number of top categories to return
            
        Returns:
            pd.DataFrame: Categories ranked by BTC holdings
        """
        if self.df is None or self.df.empty:
            self.load_data()
        
        if self.df is None or self.df.empty:
            return pd.DataFrame()
        
        # Get latest holdings
        latest = self.get_latest_holdings()
        
        if latest.empty:
            return pd.DataFrame()
        
        # Create ranking DataFrame
        ranking = pd.DataFrame({
            "category": latest.index,
            "btc_holdings": latest.values
        })
        
        # Sort and limit
        ranking = ranking.sort_values("btc_holdings", ascending=False)
        ranking = ranking.head(n).reset_index(drop=True)
        
        return ranking
    
    def search_category(self, query: str) -> pd.DataFrame:
        """
        Search for categories matching the query.
        
        Args:
            query: Search string (case-insensitive)
            
        Returns:
            pd.DataFrame: Matching categories with their latest holdings
        """
        if self.df is None or self.df.empty:
            self.load_data()
        
        if self.df is None or self.df.empty:
            return pd.DataFrame()
        
        # Get latest holdings
        latest = self.get_latest_holdings()
        
        if latest.empty:
            return pd.DataFrame()
        
        # Filter by search query
        query_lower = query.lower()
        matches = [cat for cat in latest.index if query_lower in cat.lower()]
        
        if not matches:
            return pd.DataFrame()
        
        # Create result DataFrame
        result = pd.DataFrame({
            "category": matches,
            "btc_holdings": [latest[cat] for cat in matches]
        })
        
        return result.sort_values("btc_holdings", ascending=False)
    
    def check_github_updates(self) -> Tuple[bool, Optional[datetime]]:
        """
        Check if there are new updates on GitHub.
        
        Uses the GitHub API to check the last commit date for the CSV file.
        
        Returns:
            Tuple of (has_update, last_commit_date):
                - has_update: True if GitHub has newer data than cache
                - last_commit_date: Datetime of last commit, or None on error
        """
        try:
            params = {
                "path": "category_btc-treasuries.csv",
                "per_page": 1
            }
            
            response = requests.get(
                GITHUB_API_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            commits = response.json()
            
            if not commits or len(commits) == 0:
                logger.warning("No commits found for CSV file")
                return False, None
            
            # Parse commit date
            commit_date_str = commits[0]["commit"]["committer"]["date"]
            commit_date = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))
            commit_date = commit_date.replace(tzinfo=None)  # Make naive for comparison
            
            # Check if newer than cache
            if CACHE_FILE.exists():
                cache_mtime = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
                has_update = commit_date > cache_mtime
            else:
                has_update = True
            
            logger.info(f"GitHub last commit: {commit_date}, has_update: {has_update}")
            return has_update, commit_date
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking GitHub updates: {e}")
            return False, None
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing GitHub response: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error checking updates: {e}")
            return False, None


# =============================================================================
# GLOBAL INSTANCE (SINGLETON)
# =============================================================================

treasury_manager = TreasuryDataManager()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_treasury_data(force_refresh: bool = False) -> pd.DataFrame:
    """
    Helper function to load treasury data.
    
    This is the recommended entry point for loading treasury data.
    
    Args:
        force_refresh: If True, ignore cache and download fresh data
        
    Returns:
        pd.DataFrame: Treasury data
    """
    return treasury_manager.load_data(force_refresh)


def get_treasury_stats() -> Dict[str, Any]:
    """
    Helper function to get treasury statistics.
    
    Returns:
        dict: Treasury statistics
    """
    return treasury_manager.get_stats()


# =============================================================================
# TEST / DEMO
# =============================================================================

if __name__ == "__main__":
    print("🧪 Test du module Treasury Data")
    print("=" * 50)
    
    # Test 1: Chargement
    print("\n📥 Test 1: Chargement des données...")
    df = get_treasury_data()
    if not df.empty:
        print(f"✅ {len(df)} enregistrements chargés")
        print(f"   Colonnes: {list(df.columns)}")
    else:
        print("❌ Échec du chargement")
    
    # Test 2: Stats
    print("\n📊 Test 2: Statistiques...")
    stats = treasury_manager.get_stats()
    print(f"✅ Stats:")
    print(f"   - Total BTC: {stats['total_btc']:,}")
    print(f"   - Catégories: {stats['total_categories']}")
    print(f"   - Âge du cache: {stats['cache_age_hours']} heures")
    print(f"   - Dernière MAJ: {stats['last_update']}")
    
    # Test 3: Holdings par catégorie
    print("\n🏆 Test 3: Holdings par catégorie...")
    top_cats = treasury_manager.get_top_categories()
    if not top_cats.empty:
        print("✅ Top catégories:")
        for _, row in top_cats.iterrows():
            print(f"   - {row['category']}: {row['btc_holdings']:,} BTC")
    else:
        print("❌ Pas de données de catégories")
    
    # Test 4: Données historiques
    print("\n📈 Test 4: Données historiques (30 jours)...")
    hist = treasury_manager.get_historical_data(days=30)
    if not hist.empty:
        print(f"✅ {len(hist)} enregistrements sur les 30 derniers jours")
    else:
        print("❌ Pas de données historiques")
    
    # Test 5: Check updates
    print("\n🔄 Test 5: Vérification des mises à jour GitHub...")
    has_update, commit_date = treasury_manager.check_github_updates()
    print(f"✅ Updates disponibles: {has_update}")
    print(f"   Dernier commit: {commit_date}")
    
    # Test 6: Trend ETFs
    print("\n📉 Test 6: Trend ETFs (30 jours)...")
    etf_trend = treasury_manager.get_category_trend("etfs", days=30)
    if not etf_trend.empty:
        print(f"✅ {len(etf_trend)} points de données pour ETFs")
        print(f"   Min: {etf_trend['etfs'].min():,} BTC")
        print(f"   Max: {etf_trend['etfs'].max():,} BTC")
    else:
        print("❌ Pas de données de trend ETFs")
    
    print("\n" + "=" * 50)
    print("🎉 Tests terminés!")
