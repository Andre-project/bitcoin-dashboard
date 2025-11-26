import pytest
import pandas as pd
import os
import tempfile
from unittest.mock import patch
from data_collectors.price_data import fetch_bitcoin_price_coingecko, save_to_csv, load_from_csv, refresh_bitcoin_data

class TestPriceData:
    def test_fetch_bitcoin_price_coingecko_success(self):
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

            df = fetch_bitcoin_price_coingecko(days=2)
            
            assert df is not None
            assert len(df) == 2
            assert 'price' in df.columns
            assert df.index.name == 'date'

    def test_fetch_bitcoin_price_coingecko_api_error(self):
        """Test API error handling"""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 500

            df = fetch_bitcoin_price_coingecko(days=1)
            assert df is None

    def test_save_and_load_csv(self):
        """Test CSV save and load roundtrip"""
        # Create test data
        dates = pd.date_range('2023-01-01', periods=3)
        df = pd.DataFrame({'price': [100, 200, 300]}, index=dates)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.join(temp_dir, 'test.csv')
            
            # Test save
            result = save_to_csv(df, filename)
            assert result is True
            assert os.path.exists(filename)
            
            # Test load
            loaded_df = load_from_csv(filename)
            assert loaded_df is not None
            assert len(loaded_df) == 3
            pd.testing.assert_frame_equal(df, loaded_df)

    def test_load_csv_nonexistent_file(self):
        """Test loading non-existent file"""
        df = load_from_csv('nonexistent.csv')
        assert df is None

    def test_refresh_bitcoin_data_success(self):
        """Test refresh function success"""
        with patch('data_collectors.price_data.fetch_bitcoin_price_coingecko') as mock_fetch, \
             patch('data_collectors.price_data.save_to_csv') as mock_save:
            
            mock_df = pd.DataFrame({'price': [100]}, index=pd.date_range('2023-01-01', periods=1))
            mock_fetch.return_value = mock_df
            mock_save.return_value = True
            
            df, error = refresh_bitcoin_data(days=1)
            
            assert df is not None
            assert error is None
            mock_fetch.assert_called_once_with(365)  # Default days
            mock_save.assert_called_once()

    def test_refresh_bitcoin_data_fetch_failure(self):
        """Test refresh when fetch fails"""
        with patch('data_collectors.price_data.fetch_bitcoin_price_coingecko') as mock_fetch:
            mock_fetch.return_value = None
            
            df, error = refresh_bitcoin_data(days=1)
            
            assert df is None
            assert error == "Échec du téléchargement"