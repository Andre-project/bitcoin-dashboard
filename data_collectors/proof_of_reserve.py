"""
Proof of Reserve Data Collector

Loads and manages proof of reserve data for Bitcoin treasury entities.
Provides verification status (full, partial, unverified) for each entity.
"""

import os
import pandas as pd
from typing import Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

# CSV file path
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'proof_of_reserve.csv')

# Cache
_proof_data: Optional[pd.DataFrame] = None


def load_proof_of_reserve(force_reload: bool = False) -> pd.DataFrame:
    """
    Load proof of reserve data from CSV.
    
    Args:
        force_reload: If True, reload from CSV even if cached
    
    Returns:
        DataFrame with columns: name, category, proof_status, proof_percentage, proof_source, proof_notes
    """
    global _proof_data
    
    if _proof_data is not None and not force_reload:
        return _proof_data
    
    try:
        df = pd.read_csv(CSV_PATH)
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Create lowercase name for matching
        df['name_lower'] = df['name'].str.lower().str.strip()
        
        # Ensure numeric percentage
        df['proof_percentage'] = pd.to_numeric(df['proof_percentage'], errors='coerce').fillna(0).astype(int)
        
        # Fill NA values
        df['proof_status'] = df['proof_status'].fillna('unverified')
        df['proof_source'] = df['proof_source'].fillna('No data')
        df['proof_notes'] = df['proof_notes'].fillna('')
        
        _proof_data = df
        logger.info(f"Loaded proof of reserve data: {len(df)} entities")
        return df
        
    except FileNotFoundError:
        logger.error(f"Proof of reserve CSV not found: {CSV_PATH}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading proof of reserve data: {e}")
        return pd.DataFrame()


def get_proof_data(entity_name: str) -> Dict[str, Any]:
    """
    Get proof of reserve data for a specific entity.
    
    Args:
        entity_name: Name of the entity (case-insensitive match)
    
    Returns:
        Dict with keys: status, percentage, source, notes
        Returns default 'unverified' if entity not found
    """
    df = load_proof_of_reserve()
    
    if df.empty:
        return {
            'status': 'unverified',
            'percentage': 0,
            'source': 'No data',
            'notes': ''
        }
    
    # Case-insensitive match
    name_lower = entity_name.lower().strip()
    match = df[df['name_lower'] == name_lower]
    
    if match.empty:
        # Try partial match
        match = df[df['name_lower'].str.contains(name_lower, na=False)]
    
    if match.empty:
        return {
            'status': 'unverified',
            'percentage': 0,
            'source': 'No data',
            'notes': ''
        }
    
    row = match.iloc[0]
    return {
        'status': row['proof_status'],
        'percentage': int(row['proof_percentage']),
        'source': row['proof_source'],
        'notes': row['proof_notes']
    }


def format_proof_display(status: str, percentage: int) -> str:
    """
    Format proof status for display in table.
    
    Args:
        status: 'full', 'partial', or 'unverified'
        percentage: Verification percentage (0-100)
    
    Returns:
        Formatted string: 'Full', 'Partial', or 'None'
    """
    if status == 'full':
        return 'Full'
    elif status == 'partial':
        return 'Partial'
    else:
        return 'None'


def create_proof_tooltip(status: str, percentage: int, source: str, notes: str) -> str:
    """
    Create tooltip text for proof of reserve.
    
    Args:
        status: 'full', 'partial', or 'unverified'
        percentage: Verification percentage (0-100)
        source: Source of verification
        notes: Additional notes
    
    Returns:
        Formatted tooltip text in English
    """
    if status == 'full':
        icon = "✓"
        confidence = "Public addresses available"
    elif status == 'partial':
        icon = "~"
        confidence = f"{percentage}% confidence"
    else:
        icon = "✗"
        confidence = "No public verification"
    
    tooltip = f"{icon} {confidence}\nSource: {source}"
    if notes:
        tooltip += f"\n{notes}"
    
    return tooltip


def get_proof_for_entities(entity_names: list) -> pd.DataFrame:
    """
    Get proof data for a list of entities.
    
    Args:
        entity_names: List of entity names
    
    Returns:
        DataFrame with proof columns matching entity order
    """
    results = []
    for name in entity_names:
        proof = get_proof_data(name)
        results.append({
            'name': name,
            'proof_status': proof['status'],
            'proof_percentage': proof['percentage'],
            'proof_source': proof['source'],
            'proof_notes': proof['notes'],
            'proof_display': format_proof_display(proof['status'], proof['percentage'])
        })
    
    return pd.DataFrame(results)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("🧪 Test Proof of Reserve Module")
    print("=" * 50)
    
    # Load data
    df = load_proof_of_reserve()
    print(f"✅ Loaded {len(df)} entities")
    
    # Test specific entities
    test_names = ['Strategy (MicroStrategy)', 'El Salvador', 'Block.one', 'Unknown Entity']
    
    for name in test_names:
        proof = get_proof_data(name)
        display = format_proof_display(proof['status'], proof['percentage'])
        print(f"\n{name}:")
        print(f"  Status: {proof['status']}")
        print(f"  Percentage: {proof['percentage']}%")
        print(f"  Display: {display}")
        print(f"  Source: {proof['source']}")
    
    print("\n" + "=" * 50)
    print("🎉 Tests completed!")
