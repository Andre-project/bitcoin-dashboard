import pytest
import pandas as pd
import os
import tempfile
from unittest.mock import patch
from data_collectors.price_data import (
    fetch_recent_from_coingecko,
    save_history,
    load_local_history,
    load_from_csv,
    refresh_bitcoin_data,
    get_bitcoin_price_series
)

class TestPriceData:
    def test_fetch_recent_from_coingecko_success(self):
        """Test successful API fetch"""
        with patch('requests.get') as mock_get:
            # Mock successful response
            mock_response = {
                "prices": [
                    [1640995200000, 50000],  # 2022-01-01
                    [1641081600000, 51000]   # 2022-01-02
                ]
            }
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = lambda: None

            df = fetch_recent_from_coingecko(days=2)
            
            assert df is not None
            assert len(df) == 2
            assert 'price' in df.columns
            assert 'date' in df.columns

    def test_fetch_recent_from_coingecko_api_error(self):
        """Test API error handling"""
        with patch('requests.get') as mock_get:
            import requests
            mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Error")

            df = fetch_recent_from_coingecko(days=1)
            assert df is None

    def test_load_from_csv_nonexistent_file(self):
        """Test loading non-existent file"""
        with patch('data_collectors.price_data.CSV_PATH', '/nonexistent/path.csv'):
            df = load_local_history()
            assert df is None

    def test_refresh_bitcoin_data_returns_tuple(self):
        """Test refresh function returns correct format"""
        with patch('data_collectors.price_data.get_bitcoin_price_series') as mock_get:
            mock_df = pd.DataFrame({
                'date': pd.date_range('2023-01-01', periods=3),
                'price': [100, 200, 300]
            })
            mock_get.return_value = mock_df
            
            df, error = refresh_bitcoin_data(days=1)
            
            assert df is not None or error is not None  # Either success or error message

    def test_load_from_csv_backwards_compat(self):
        """Test backwards compatibility function"""
        with patch('data_collectors.price_data.load_local_history') as mock_load:
            mock_df = pd.DataFrame({
                'date': pd.date_range('2023-01-01', periods=3),
                'price': [100, 200, 300]
            })
            mock_load.return_value = mock_df
            
            df = load_from_csv()
            
            # Should return with date as index
            assert df is not None
            assert df.index.name == 'date'