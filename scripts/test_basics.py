import requests
import pandas as pd
from datetime import datetime, timedelta
from data_collectors.price_data import fetch_bitcoin_price_coingecko, save_to_csv, load_from_csv
from utils.logger import get_logger

logger = get_logger(__name__)

# --- MAIN CODE ---
logger.info("=== Bitcoin Price Downloader ===")

# Essaie de charger depuis cache d'abord
logger.info("🔍 Recherche cache local...")
btc = load_from_csv()

# Si pas de cache, télécharge
if btc is None:
    logger.info("📡 Pas de cache → Télécharge depuis API...")
    btc = fetch_bitcoin_price_coingecko(days=30)
    
    # Sauvegarde pour la prochaine fois
    if btc is not None and not btc.empty:
        save_to_csv(btc)
else:
    logger.info("✅ Utilisation du cache (pas de téléchargement)")

# Traite les données
if btc is not None and not btc.empty:
    logger.info("\n=== Aperçu des données ===")
    print(btc.tail())  # 5 derniers jours
    
    print(f"\n📅 Premier jour : {btc.index[0].strftime('%Y-%m-%d')}")
    print(f"📅 Dernier jour : {btc.index[-1].strftime('%Y-%m-%d')}")
    
    avg_price = btc['price'].mean()
    current_price = btc['price'].iloc[-1]
    
    if avg_price is not None:
        print(f"\n💰 Prix moyen (30j) : ${avg_price:,.2f}")
        print(f"💰 Prix actuel : ${current_price:,.2f}")
        
        # Calcule variation
        variation = ((current_price - avg_price) / avg_price) * 100
        emoji = "📈" if variation > 0 else "📉"
        print(f"{emoji} Variation vs moyenne : {variation:+.2f}%")
        
else:
    logger.error("\n❌ Échec téléchargement")
