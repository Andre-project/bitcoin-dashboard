import logging
import os
from datetime import datetime

def setup_logger():
    """Configure le logger global pour l'application"""
    # Crée dossier logs si nécessaire
    os.makedirs('logs', exist_ok=True)

    # Format du log
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Handler pour console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)

    # Handler pour fichier
    log_filename = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)

    # Logger root
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

def get_logger(name: str):
    """Retourne un logger pour un module spécifique"""
    return logging.getLogger(name)

# Setup automatique au import
setup_logger()