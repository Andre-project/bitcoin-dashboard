"""
Proof Score Data Collector

Loads Bitcoin-maxi Proof of Reserve scoring data from CSV.
Provides confidence scores and metadata for treasury entities.
"""

import os
import pandas as pd
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# CSV file path
CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', 'data', 'BITCOIN_MAXI_POR_COMPLETE.csv'
)

# Cache
_proof_scores_df: Optional[pd.DataFrame] = None


def load_proof_scores(force_reload: bool = False) -> pd.DataFrame:
    """
    Load proof-of-reserve scoring data from CSV.
    
    Returns:
        DataFrame with columns:
        - Name
        - Category
        - Country
        - Claimed BTC
        - Verified BTC
        - Confidence Score
        - Max Possible
        - Tier
        - Public Addresses
        - Concerns
    """
    global _proof_scores_df
    
    if _proof_scores_df is not None and not force_reload:
        return _proof_scores_df
    
    try:
        df = pd.read_csv(CSV_PATH)
        
        # Normalize column names for easier access
        df.columns = df.columns.str.strip()
        
        # Create lowercase name for matching
        df['name_lower'] = df['Name'].str.lower().str.strip()
        
        # Ensure numeric columns
        df['Confidence Score'] = pd.to_numeric(df['Confidence Score'], errors='coerce').fillna(0)
        df['Max Possible'] = pd.to_numeric(df['Max Possible'], errors='coerce').fillna(100)
        
        # Fill string columns
        df['Tier'] = df['Tier'].fillna('Unknown')
        df['Public Addresses'] = df['Public Addresses'].fillna('Unknown')
        df['Concerns'] = df['Concerns'].fillna('')
        
        _proof_scores_df = df
        logger.info(f"Loaded {len(df)} rows from BITCOIN_MAXI_POR_COMPLETE.csv")
        return df
        
    except FileNotFoundError:
        logger.error(f"Proof score CSV not found at {CSV_PATH}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading proof score CSV: {e}")
        return pd.DataFrame()


def normalize_name(name: str) -> str:
    """
    Normalize entity name for better matching.
    Removes parenthetical content, common suffixes, and extra whitespace.
    """
    import re
    
    name = name.lower().strip()
    
    # Remove content in parentheses (e.g., "(MARA)", "(BITB)")
    name = re.sub(r'\s*\([^)]*\)', '', name)
    
    # Remove common suffixes
    suffixes = [' inc', ' inc.', ' corp', ' corp.', ' ltd', ' ltd.', 
                ' holdings', ' limited', ' llc', ' lp', ' plc']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    
    # Normalize whitespace
    name = ' '.join(name.split())
    
    return name.strip()


def get_proof_score_for_entity(entity_name: str) -> dict:
    """
    Get proof score data for a specific entity.
    Uses multiple matching strategies for better entity matching.
    
    Args:
        entity_name: Name of the entity (case-insensitive match)
    
    Returns:
        Dict with keys: confidence_score, max_possible, tier, public_addresses, concerns
    """
    df = load_proof_scores()
    
    default_result = {
        'confidence_score': 0,
        'max_possible': 100,
        'tier': 'Unknown',
        'public_addresses': 'Unknown',
        'concerns': 'No data available'
    }
    
    if df.empty:
        return default_result
    
    name_lower = entity_name.lower().strip()
    name_normalized = normalize_name(entity_name)
    
    # Strategy 1: Exact match
    match = df[df['name_lower'] == name_lower]
    
    if match.empty:
        # Strategy 2: Normalized match (CSV name normalized matches entity name normalized)
        df['name_normalized'] = df['Name'].apply(normalize_name)
        match = df[df['name_normalized'] == name_normalized]
    
    if match.empty:
        # Strategy 3: Entity name contains CSV name (normalized)
        for idx, row in df.iterrows():
            csv_normalized = normalize_name(row['Name'])
            if csv_normalized in name_normalized or name_normalized in csv_normalized:
                match = df.iloc[[idx]]
                break
    
    if match.empty:
        # Strategy 4: Partial match - CSV name contains entity name
        match = df[df['name_lower'].str.contains(name_lower, na=False, regex=False)]
    
    if match.empty:
        # Strategy 5: Partial match - entity name contains CSV name
        for idx, row in df.iterrows():
            if row['name_lower'] in name_lower:
                match = df.iloc[[idx]]
                break
    
    if match.empty:
        # Strategy 6: First word match (for common names like "Marathon", "Riot", etc.)
        first_word = name_normalized.split()[0] if name_normalized else ''
        if len(first_word) > 3:  # Only if meaningful word
            for idx, row in df.iterrows():
                csv_first = normalize_name(row['Name']).split()[0] if row['Name'] else ''
                if first_word == csv_first:
                    match = df.iloc[[idx]]
                    break
    
    if match.empty:
        return default_result
    
    row = match.iloc[0]
    return {
        'confidence_score': int(row['Confidence Score']),
        'max_possible': int(row['Max Possible']),
        'tier': str(row['Tier']),
        'public_addresses': str(row['Public Addresses']),
        'concerns': str(row['Concerns'])
    }


def format_proof_score_display(confidence_score: int) -> str:
    """
    Format proof score for display in table.
    
    Args:
        confidence_score: Score from 0-100
    
    Returns:
        Formatted string like "85%"
    """
    return f"{confidence_score}%"


def create_proof_score_tooltip(confidence_score: int, max_possible: int, 
                                tier: str, public_addresses: str, concerns: str) -> str:
    """
    Create tooltip text for proof score cell.
    
    Returns:
        Multi-line tooltip text
    """
    lines = [
        f"Confidence: {confidence_score}% (Max: {max_possible}%)",
        f"Tier: {tier}",
        f"Public addresses: {public_addresses}",
        f"Concerns: {concerns if concerns else 'None noted'}"
    ]
    return "\n".join(lines)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("🧪 Test Proof Score Module")
    print("=" * 50)
    
    # Load data
    df = load_proof_scores()
    print(f"✅ Loaded {len(df)} entities")
    
    # Test specific entities
    test_names = ['Bitwise Bitcoin ETF', 'Strategy (MicroStrategy)', 'El Salvador', 'Unknown Entity']
    
    for name in test_names:
        score = get_proof_score_for_entity(name)
        print(f"\n{name}:")
        print(f"  Score: {score['confidence_score']}%")
        print(f"  Tier: {score['tier']}")
        print(f"  Public Addresses: {score['public_addresses']}")
    
    print("\n" + "=" * 50)
    print("🎉 Tests completed!")
