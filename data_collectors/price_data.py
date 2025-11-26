import requests
import pandas as pd
from datetime import datetime
import os
from typing import Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

def fetch_bitcoin_price_coingecko(days: int = 30) -> Optional[pd.DataFrame]:
    """
    Télécharge prix Bitcoin via CoinGecko API

    Args:
        days (int): Nombre de jours d'historique (max 365 pour free tier)

    Returns:
        pd.DataFrame: Prix Bitcoin avec colonnes ['date', 'price'] indexé par date, ou None si erreur
    """
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }

        logger.info(f"📡 Connexion à CoinGecko API pour {days} jours...")

        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            logger.error(f"❌ Erreur API : Status {response.status_code}")
            return None

        data = response.json()

        if 'prices' not in data:
            logger.error("❌ Format réponse invalide (pas de 'prices')")
            return None

        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[['date', 'price']]
        df.set_index('date', inplace=True)

        logger.info(f"✅ Données téléchargées : {len(df)} jours")
        return df

    except requests.exceptions.Timeout:
        logger.error("❌ Timeout : API trop lente (>10s)")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("❌ Erreur connexion : Vérifie internet")
        return None
    except Exception as e:
        logger.error(f"❌ Erreur inattendue : {e}")
        return None


def save_to_csv(df: pd.DataFrame, filename: str = "data/bitcoin_price.csv") -> bool:
    """
    Sauvegarde DataFrame en CSV

    Args:
        df (pd.DataFrame): Données à sauvegarder
        filename (str): Chemin du fichier

    Returns:
        bool: True si succès, False sinon
    """
    try:
        os.makedirs(os.path.dirname(filename) or 'data', exist_ok=True)
        df.to_csv(filename)
        logger.info(f"💾 Données sauvegardées : {filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde : {e}")
        return False


def load_from_csv(filename: str = "data/bitcoin_price.csv") -> Optional[pd.DataFrame]:
    """
    Charge données depuis CSV

    Args:
        filename (str): Chemin du fichier

    Returns:
        pd.DataFrame ou None: Données chargées ou None si erreur
    """
    try:
        if not os.path.exists(filename):
            logger.warning(f"⚠️ Fichier {filename} n'existe pas")
            return None

        df = pd.read_csv(filename, index_col='date', parse_dates=True)
        logger.info(f"📂 Données chargées depuis cache : {len(df)} jours")
        return df
    except Exception as e:
        logger.error(f"❌ Erreur lecture CSV : {e}")
        return None


def refresh_bitcoin_data(days: int = 365) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Re-télécharge Bitcoin data depuis CoinGecko et sauvegarde

    Args:
        days (int): Nombre de jours (default: 365 = 1 year)

    Returns:
        Tuple[pd.DataFrame, str]: (df, error_message) - df=None si erreur
    """
    df = fetch_bitcoin_price_coingecko(days)
    if df is None:
        error = "Échec du téléchargement"
        logger.error(f"❌ {error}")
        return None, error

    if not save_to_csv(df):
        error = "Échec de la sauvegarde"
        logger.error(f"❌ {error}")
        return None, error

    logger.info("✅ Données rafraîchies et sauvegardées")
    return df, None