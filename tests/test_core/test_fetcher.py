"""Tests for the weather data fetcher."""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock

from weather_spark_digest.core.fetcher import WeatherDataFetcher


class TestWeatherDataFetcher:
    """Test cases for WeatherDataFetcher."""

    def test_init(self):
        """Test fetcher initialization."""
        fetcher = WeatherDataFetcher()
        assert fetcher.base_url == "https://weatherspark.com"
        assert fetcher.session is not None

        # Test custom base URL
        custom_fetcher = WeatherDataFetcher("https://example.com")
        assert custom_fetcher.base_url == "https://example.com"

    def test_fetch_city_data(self):
        """Test fetching city data."""
        fetcher = WeatherDataFetcher()
        city_data = fetcher.fetch_city_data("New York")

        # Verify data structure
        assert "city" in city_data
        assert "temperature_data" in city_data
        assert "humidity_data" in city_data
        assert "precipitation_data" in city_data
        assert "fetch_timestamp" in city_data

        assert city_data["city"] == "New York"
        assert len(city_data["temperature_data"]) == 12  # 12 months
        assert len(city_data["humidity_data"]) == 12
        assert len(city_data["precipitation_data"]) == 12

    def test_generate_mock_temperature_data(self):
        """Test mock temperature data generation."""
        fetcher = WeatherDataFetcher()
        temp_data = fetcher._generate_mock_temperature_data()

        assert len(temp_data) == 12
        for i, month_data in enumerate(temp_data):
            assert month_data["month"] == i + 1
            assert "avg_high" in month_data
            assert "avg_low" in month_data
            assert "record_high" in month_data
            assert "record_low" in month_data

    def test_generate_mock_humidity_data(self):
        """Test mock humidity data generation."""
        fetcher = WeatherDataFetcher()
        humidity_data = fetcher._generate_mock_humidity_data()

        assert len(humidity_data) == 12
        for i, month_data in enumerate(humidity_data):
            assert month_data["month"] == i + 1
            assert "avg_humidity" in month_data
            assert "morning_humidity" in month_data
            assert "afternoon_humidity" in month_data

    def test_generate_mock_precipitation_data(self):
        """Test mock precipitation data generation."""
        fetcher = WeatherDataFetcher()
        precip_data = fetcher._generate_mock_precipitation_data()

        assert len(precip_data) == 12
        for i, month_data in enumerate(precip_data):
            assert month_data["month"] == i + 1
            assert "total_precipitation" in month_data
            assert "rainy_days" in month_data
            assert "snow_days" in month_data

    def test_flatten_city_data_for_csv(self):
        """Test flattening city data for CSV output."""
        fetcher = WeatherDataFetcher()
        city_data = fetcher.fetch_city_data("Test City")
        flattened_data = fetcher.flatten_city_data_for_csv(city_data)

        assert len(flattened_data) == 12  # 12 months

        # Check first month data
        first_month = flattened_data[0]
        assert first_month["city"] == "Test City"
        assert first_month["month"] == 1
        assert "avg_high_temp" in first_month
        assert "avg_low_temp" in first_month
        assert "record_high_temp" in first_month
        assert "record_low_temp" in first_month
        assert "avg_humidity" in first_month
        assert "morning_humidity" in first_month
        assert "afternoon_humidity" in first_month
        assert "total_precipitation" in first_month
        assert "rainy_days" in first_month
        assert "snow_days" in first_month

    @patch("weather_spark_digest.core.fetcher.cairosvg")
    @patch("weather_spark_digest.core.fetcher.Image")
    def test_process_svg_to_data(self, mock_image, mock_cairosvg):
        """Test SVG processing to data."""
        # Mock PIL Image
        mock_img = Mock()
        mock_img.size = (800, 600)
        mock_image.open.return_value.__enter__.return_value = mock_img

        fetcher = WeatherDataFetcher()
        svg_content = "<svg>test</svg>"

        result = fetcher.process_svg_to_data(svg_content)

        assert len(result) == 12  # 12 months
        for i, data_point in enumerate(result):
            assert data_point["month"] == i + 1
            assert "value" in data_point
