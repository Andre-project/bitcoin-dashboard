import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_bitcoin_price_coingecko(days=30):
    """
    Télécharge prix Bitcoin via CoinGecko API
    
    Args:
        days (int): Nombre de jours d'historique (max 365 sans API key)
    
    Returns:
        pd.DataFrame: Prix Bitcoin avec colonnes ['date', 'price']
    """
    try:
        # URL CoinGecko (gratuit, pas de clé)
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        
        # Paramètres
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }
        
        print(f"📡 Connexion à CoinGecko API...")
        
        # Requête avec timeout (critique pour éviter freeze)
        response = requests.get(url, params=params, timeout=10)
        
        # Vérifie status code
        if response.status_code != 200:
            print(f"❌ Erreur API : Status {response.status_code}")
            return None
        
        # Parse JSON
        data = response.json()
        
        # Valide structure réponse
        if 'prices' not in data:
            print("❌ Format réponse invalide (pas de 'prices')")
            return None
        
        # Convertit en DataFrame
        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        
        # Convertit timestamp (millisecondes) en date
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Drop timestamp, garde date et price
        df = df[['date', 'price']]
        
        # Set date comme index
        df.set_index('date', inplace=True)
        
        print(f"✅ Données téléchargées : {len(df)} jours")
        
        return df
    
    except requests.exceptions.Timeout:
        print("❌ Timeout : API trop lente (>10s)")
        return None
    
    except requests.exceptions.ConnectionError:
        print("❌ Erreur connexion : Vérifie internet")
        return None
    
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return None


def calculate_average_price(df):
    """Calcule prix moyen"""
    try:
        if df is None or df.empty:
            print("⚠️ DataFrame vide, impossible de calculer")
            return None
        
        average = df['price'].mean()
        return average
    
    except Exception as e:
        print(f"❌ Erreur calcul moyenne : {e}")
        return None

def save_to_csv(df, filename="data/bitcoin_price.csv"):
    """
    Sauvegarde DataFrame en CSV
    
    Args:
        df (pd.DataFrame): Données à sauvegarder
        filename (str): Chemin du fichier
    """
    try:
        # Crée dossier data/ si n'existe pas
        import os
        os.makedirs('data', exist_ok=True)
        
        # Sauvegarde avec index (les dates)
        df.to_csv(filename)
        
        print(f"💾 Données sauvegardées : {filename}")
        return True
    
    except Exception as e:
        print(f"❌ Erreur sauvegarde : {e}")
        return False
def load_from_csv(filename="data/bitcoin_price.csv"):
    """
    Charge données depuis CSV
    
    Args:
        filename (str): Chemin du fichier
    
    Returns:
        pd.DataFrame ou None: Données chargées ou None si erreur
    """
    try:
        import os
        
        # Vérifie si fichier existe
        if not os.path.exists(filename):
            print(f"⚠️ Fichier {filename} n'existe pas")
            return None
        
        # Charge CSV avec date comme index
        df = pd.read_csv(filename, index_col='date', parse_dates=True)
        
        print(f"📂 Données chargées depuis cache : {len(df)} jours")
        
        return df
    
    except Exception as e:
        print(f"❌ Erreur lecture CSV : {e}")
        return None

# --- MAIN CODE ---
print("=== Bitcoin Price Downloader ===\n")

# Essaie de charger depuis cache d'abord
print("🔍 Recherche cache local...")
btc = load_from_csv()

# Si pas de cache, télécharge
if btc is None:
    print("📡 Pas de cache → Télécharge depuis API...")
    btc = fetch_bitcoin_price_coingecko(days=30)
    
    # Sauvegarde pour la prochaine fois
    if btc is not None and not btc.empty:
        save_to_csv(btc)
else:
    print("✅ Utilisation du cache (pas de téléchargement)")

# Traite les données
if btc is not None and not btc.empty:
    print("\n=== Aperçu des données ===")
    print(btc.tail())  # 5 derniers jours
    
    print(f"\n📅 Premier jour : {btc.index[0].strftime('%Y-%m-%d')}")
    print(f"📅 Dernier jour : {btc.index[-1].strftime('%Y-%m-%d')}")
    
    avg_price = calculate_average_price(btc)
    current_price = btc['price'].iloc[-1]
    
    if avg_price is not None:
        print(f"\n💰 Prix moyen (30j) : ${avg_price:,.2f}")
        print(f"💰 Prix actuel : ${current_price:,.2f}")
        
        # Calcule variation
        variation = ((current_price - avg_price) / avg_price) * 100
        emoji = "📈" if variation > 0 else "📉"
        print(f"{emoji} Variation vs moyenne : {variation:+.2f}%")
        
else:
    print("\n❌ Échec téléchargement")
