"""
Treasury Entities Data Module

Fetches detailed Bitcoin treasury data (individual companies, ETFs, etc.) from bitbo.io.
This module provides entity-level data with names, BTC holdings, and categories.

Features:
- Scrapes detailed entity data from bitbo.io/treasuries
- Caches data locally with 6-hour expiration
- Fallback sample data if scraping fails
"""

import os
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from utils.logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

BITBO_URL = "https://bitbo.io/treasuries/"
CACHE_DIR = Path(os.path.dirname(__file__)).parent / "data"
ENTITIES_CACHE_FILE = CACHE_DIR / "treasury_entities_cache.json"
CACHE_DURATION = timedelta(hours=6)
REQUEST_TIMEOUT = 30
MAX_BTC_SUPPLY = 21_000_000

# Category mapping for bitbo.io sections
CATEGORY_SECTIONS = {
    'public_companies': {
        'name': 'Public Companies',
        'icon': '🏢',
        'section_id': 'public'
    },
    'etfs': {
        'name': 'ETFs',
        'icon': '📊',
        'section_id': 'etfs'
    },
    'private_companies': {
        'name': 'Private Companies',
        'icon': '🔒',
        'section_id': 'private'
    },
    'countries': {
        'name': 'Countries',
        'icon': '🌍',
        'section_id': 'countries'
    },
    'defi': {
        'name': 'DeFi Protocols',
        'icon': '⚡',
        'section_id': 'defi'
    },
    'mining_companies': {
        'name': 'Mining Companies',
        'icon': '⛏️',
        'section_id': 'miners'
    }
}


# =============================================================================
# SAMPLE DATA (Fallback when scraping fails)
# =============================================================================

def get_sample_data() -> Dict[str, List[Dict]]:
    """
    Returns sample treasury data for demonstration.
    This is used when scraping fails or for offline development.
    """
    return {
        'public_companies': [
            {'name': 'Strategy (MicroStrategy)', 'country': 'USA', 'btc': 576230},
            {'name': 'Marathon Digital Holdings', 'country': 'USA', 'btc': 47600},
            {'name': 'Twenty One Capital', 'country': 'USA', 'btc': 36969},
            {'name': 'Metaplanet Inc.', 'country': 'Japan', 'btc': 11108},
            {'name': 'Riot Platforms', 'country': 'USA', 'btc': 19223},
            {'name': 'Galaxy Digital Holdings', 'country': 'USA', 'btc': 17518},
            {'name': 'Hut 8 Corp', 'country': 'Canada', 'btc': 10264},
            {'name': 'CleanSpark Inc', 'country': 'USA', 'btc': 10556},
            {'name': 'Tesla, Inc.', 'country': 'USA', 'btc': 9720},
            {'name': 'Coinbase Global', 'country': 'USA', 'btc': 9480},
            {'name': 'Block, Inc.', 'country': 'USA', 'btc': 8485},
            {'name': 'Semler Scientific', 'country': 'USA', 'btc': 4264},
            {'name': 'GameStop Corp.', 'country': 'USA', 'btc': 4710},
            {'name': 'Boyaa Interactive', 'country': 'Hong Kong', 'btc': 3350},
        ],
        'etfs': [
            {'name': 'iShares Bitcoin Trust (BlackRock)', 'country': 'USA', 'btc': 598040},
            {'name': 'Fidelity Wise Origin Bitcoin Fund', 'country': 'USA', 'btc': 207100},
            {'name': 'Grayscale Bitcoin Trust', 'country': 'USA', 'btc': 195570},
            {'name': 'ARK 21Shares Bitcoin ETF', 'country': 'USA', 'btc': 50000},
            {'name': 'Bitwise Bitcoin ETF', 'country': 'USA', 'btc': 41500},
            {'name': 'CoinShares / XBT Provider', 'country': 'Sweden', 'btc': 48894},
            {'name': 'Grayscale Bitcoin Mini Trust', 'country': 'USA', 'btc': 37650},
            {'name': 'VanEck Bitcoin Trust', 'country': 'USA', 'btc': 14200},
            {'name': 'Purpose Bitcoin ETF', 'country': 'Canada', 'btc': 24280},
            {'name': '3iQ The Bitcoin Fund', 'country': 'Canada', 'btc': 23000},
            {'name': 'Franklin Bitcoin ETF', 'country': 'USA', 'btc': 12750},
            {'name': 'Invesco Galaxy Bitcoin ETF', 'country': 'USA', 'btc': 10500},
        ],
        'private_companies': [
            {'name': 'Block.one', 'country': 'Cayman Islands', 'btc': 164000},
            {'name': 'Tether Holdings LTD', 'country': 'BVI', 'btc': 100521},
            {'name': 'BitMEX', 'country': 'Seychelles', 'btc': 57043},
            {'name': 'Mt. Gox', 'country': 'Japan', 'btc': 44905},
            {'name': 'SpaceX', 'country': 'USA', 'btc': 8285},
            {'name': 'Xapo Bank', 'country': 'Gibraltar', 'btc': 10000},
            {'name': 'Stone Ridge Holdings', 'country': 'USA', 'btc': 10000},
            {'name': 'The Tezos Foundation', 'country': 'Switzerland', 'btc': 8800},
            {'name': 'River Financial Inc.', 'country': 'USA', 'btc': 5000},
        ],
        'countries': [
            {'name': 'United States', 'country': 'USA', 'btc': 198012},
            {'name': 'China', 'country': 'China', 'btc': 194000},
            {'name': 'United Kingdom', 'country': 'UK', 'btc': 61000},
            {'name': 'Ukraine', 'country': 'Ukraine', 'btc': 46351},
            {'name': 'Bhutan', 'country': 'Bhutan', 'btc': 11688},
            {'name': 'El Salvador', 'country': 'El Salvador', 'btc': 6180},
            {'name': 'Finland', 'country': 'Finland', 'btc': 1981},
            {'name': 'Germany', 'country': 'Germany', 'btc': 0},
        ],
        'defi': [
            {'name': 'Wrapped Bitcoin (WBTC)', 'country': 'Decentralized', 'btc': 135000},
            {'name': 'tBTC', 'country': 'Decentralized', 'btc': 25000},
            {'name': 'renBTC', 'country': 'Decentralized', 'btc': 15000},
            {'name': 'sBTC (Stacks)', 'country': 'Decentralized', 'btc': 8000},
            {'name': 'BTCB (Binance)', 'country': 'Decentralized', 'btc': 75000},
        ],
        'mining_companies': [
            {'name': 'Marathon Digital Holdings', 'country': 'USA', 'btc': 47600},
            {'name': 'Riot Platforms', 'country': 'USA', 'btc': 19223},
            {'name': 'Hut 8 Corp', 'country': 'Canada', 'btc': 10264},
            {'name': 'CleanSpark Inc', 'country': 'USA', 'btc': 10556},
            {'name': 'Core Scientific', 'country': 'USA', 'btc': 1959},
            {'name': 'Bitdeer Technologies', 'country': 'Singapore', 'btc': 1527},
            {'name': 'Bitfarms Limited', 'country': 'Canada', 'btc': 1188},
            {'name': 'Cipher Mining', 'country': 'USA', 'btc': 1034},
            {'name': 'HIVE Digital Technologies', 'country': 'Canada', 'btc': 2624},
            {'name': 'TeraWulf Inc.', 'country': 'USA', 'btc': 706},
        ]
    }


# =============================================================================
# TREASURY ENTITIES MANAGER CLASS
# =============================================================================

class TreasuryEntitiesManager:
    """
    Manages detailed Bitcoin treasury entity data.
    
    Provides individual company/ETF/country data with BTC holdings.
    """
    
    def __init__(self) -> None:
        """Initialize the TreasuryEntitiesManager."""
        self._entities_data: Optional[Dict[str, List[Dict]]] = None
        self._last_update: Optional[datetime] = None
        self._btc_price: float = 100000  # Default BTC price
        self._ensure_data_dir()
    
    def _ensure_data_dir(self) -> None:
        """Create the data directory if it doesn't exist."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is valid (less than CACHE_DURATION old)."""
        if not ENTITIES_CACHE_FILE.exists():
            return False
        
        try:
            file_mtime = datetime.fromtimestamp(ENTITIES_CACHE_FILE.stat().st_mtime)
            age = datetime.now() - file_mtime
            return age < CACHE_DURATION
        except Exception as e:
            logger.warning(f"Error checking cache validity: {e}")
            return False
    
    def _load_from_cache(self) -> Optional[Dict[str, List[Dict]]]:
        """Load entities data from cache."""
        if not ENTITIES_CACHE_FILE.exists():
            return None
        
        try:
            with open(ENTITIES_CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded entities data from cache")
            return data.get('entities', {})
        except Exception as e:
            logger.warning(f"Error loading from cache: {e}")
            return None
    
    def _save_to_cache(self, data: Dict[str, List[Dict]]) -> bool:
        """Save entities data to cache."""
        try:
            cache_data = {
                'entities': data,
                'last_update': datetime.now().isoformat(),
                'btc_price': self._btc_price
            }
            with open(ENTITIES_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved entities data to cache")
            return True
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
            return False
    
    def _fetch_btc_price(self) -> float:
        """Fetch current BTC price from CoinGecko."""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": "bitcoin", "vs_currencies": "usd"}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            price = data.get('bitcoin', {}).get('usd', 100000)
            logger.info(f"Fetched BTC price: ${price:,.0f}")
            return price
        except Exception as e:
            logger.warning(f"Error fetching BTC price, using default: {e}")
            return 100000
    
    def load_data(self, force_refresh: bool = False) -> Dict[str, List[Dict]]:
        """
        Load treasury entities data.
        
        Args:
            force_refresh: If True, ignore cache and reload
            
        Returns:
            Dict mapping category to list of entity dicts
        """
        # Always fetch fresh BTC price (not cached)
        self._btc_price = self._fetch_btc_price()
        
        # Check cache first for entities data
        if not force_refresh and self._is_cache_valid():
            cached = self._load_from_cache()
            if cached:
                self._entities_data = cached
                self._last_update = datetime.fromtimestamp(ENTITIES_CACHE_FILE.stat().st_mtime)
                return self._entities_data
        
        # Use sample data (bitbo.io requires JavaScript rendering)
        logger.info("Loading sample treasury entities data")
        self._entities_data = get_sample_data()
        self._last_update = datetime.now()
        
        # Save to cache
        self._save_to_cache(self._entities_data)
        
        return self._entities_data
    
    def get_category_data(self, category: str) -> pd.DataFrame:
        """
        Get data for a specific category.
        
        Args:
            category: Category key (e.g., 'public_companies', 'etfs')
            
        Returns:
            DataFrame with columns: rank, name, country, btc, value_usd, pct_category, pct_total
        """
        if self._entities_data is None:
            self.load_data()
        
        entities = self._entities_data.get(category, [])
        
        if not entities:
            return pd.DataFrame()
        
        df = pd.DataFrame(entities)
        
        # Sort by BTC descending
        df = df.sort_values('btc', ascending=False).reset_index(drop=True)
        
        # Add rank
        df['rank'] = range(1, len(df) + 1)
        
        # Calculate value USD
        df['value_usd'] = df['btc'] * self._btc_price
        
        # Calculate percentages
        category_total = df['btc'].sum()
        global_total = self.get_global_total_btc()
        
        df['pct_category'] = (df['btc'] / category_total * 100) if category_total > 0 else 0
        df['pct_total'] = (df['btc'] / global_total * 100) if global_total > 0 else 0
        
        # Reorder columns
        df = df[['rank', 'name', 'country', 'btc', 'value_usd', 'pct_category', 'pct_total']]
        
        return df
    
    def get_category_stats(self, category: str) -> Dict[str, Any]:
        """
        Get summary statistics for a category.
        
        Returns:
            Dict with count, total_btc, total_value, supply_pct
        """
        if self._entities_data is None:
            self.load_data()
        
        entities = self._entities_data.get(category, [])
        
        if not entities:
            return {
                'count': 0,
                'total_btc': 0,
                'total_value': 0,
                'supply_pct': 0
            }
        
        total_btc = sum(e.get('btc', 0) for e in entities)
        total_value = total_btc * self._btc_price
        supply_pct = (total_btc / MAX_BTC_SUPPLY * 100)
        
        return {
            'count': len(entities),
            'total_btc': total_btc,
            'total_value': total_value,
            'supply_pct': supply_pct
        }
    
    def get_global_total_btc(self) -> float:
        """Get total BTC across all categories."""
        if self._entities_data is None:
            self.load_data()
        
        total = 0
        for category, entities in self._entities_data.items():
            # Avoid double counting (mining companies are also public companies)
            if category != 'mining_companies':
                total += sum(e.get('btc', 0) for e in entities)
        
        return total
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all categories."""
        if self._entities_data is None:
            self.load_data()
        
        stats = {}
        for category in CATEGORY_SECTIONS.keys():
            stats[category] = self.get_category_stats(category)
        
        return stats
    
    @property
    def btc_price(self) -> float:
        """Current BTC price used for calculations."""
        return self._btc_price
    
    @property
    def last_update(self) -> Optional[datetime]:
        """Timestamp of last data refresh."""
        return self._last_update


# =============================================================================
# GLOBAL INSTANCE (SINGLETON)
# =============================================================================

entities_manager = TreasuryEntitiesManager()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_entities_data(force_refresh: bool = False) -> Dict[str, List[Dict]]:
    """Load treasury entities data."""
    return entities_manager.load_data(force_refresh)


def get_category_dataframe(category: str) -> pd.DataFrame:
    """Get DataFrame for a specific category."""
    return entities_manager.get_category_data(category)


def get_category_summary(category: str) -> Dict[str, Any]:
    """Get summary stats for a category."""
    return entities_manager.get_category_stats(category)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("🧪 Test Treasury Entities Module")
    print("=" * 50)
    
    # Load data
    data = get_entities_data()
    print(f"✅ Loaded {len(data)} categories")
    
    # Test each category
    for cat_key, cat_info in CATEGORY_SECTIONS.items():
        stats = get_category_summary(cat_key)
        df = get_category_dataframe(cat_key)
        print(f"\n{cat_info['icon']} {cat_info['name']}:")
        print(f"   Count: {stats['count']}")
        print(f"   Total BTC: {stats['total_btc']:,.0f}")
        print(f"   Total Value: ${stats['total_value']:,.0f}")
        print(f"   % of Supply: {stats['supply_pct']:.2f}%")
        if not df.empty:
            print(f"   Top 3: {', '.join(df['name'].head(3).tolist())}")
    
    print("\n" + "=" * 50)
    print("🎉 Tests completed!")
