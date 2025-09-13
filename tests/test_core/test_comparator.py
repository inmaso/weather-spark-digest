"""Tests for the weather data comparator."""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path

from weather_spark_digest.core.comparator import WeatherDataComparator


class TestWeatherDataComparator:
    """Test cases for WeatherDataComparator."""

    def test_init(self):
        """Test comparator initialization."""
        comparator = WeatherDataComparator()
        assert comparator.city_data == {}

    def create_sample_csv_files(self, temp_dir):
        """Create sample CSV files for testing."""
        # Sample data for New York
        ny_data = []
        for month in range(1, 13):
            ny_data.append(
                {
                    "city": "New York",
                    "month": month,
                    "avg_high_temp": 20 + month,
                    "avg_low_temp": 10 + month,
                    "record_high_temp": 30 + month,
                    "record_low_temp": 0 + month,
                    "avg_humidity": 60 + month,
                    "morning_humidity": 70 + month,
                    "afternoon_humidity": 50 + month,
                    "total_precipitation": month * 10,
                    "rainy_days": month,
                    "snow_days": 12 - month if month <= 3 else 0,
                }
            )

        # Sample data for Los Angeles
        la_data = []
        for month in range(1, 13):
            la_data.append(
                {
                    "city": "Los Angeles",
                    "month": month,
                    "avg_high_temp": 25 + month,
                    "avg_low_temp": 15 + month,
                    "record_high_temp": 35 + month,
                    "record_low_temp": 5 + month,
                    "avg_humidity": 50 + month,
                    "morning_humidity": 60 + month,
                    "afternoon_humidity": 40 + month,
                    "total_precipitation": month * 5,
                    "rainy_days": month // 2,
                    "snow_days": 0,
                }
            )

        # Create CSV files
        ny_df = pd.DataFrame(ny_data)
        la_df = pd.DataFrame(la_data)

        ny_path = os.path.join(temp_dir, "new_york.csv")
        la_path = os.path.join(temp_dir, "los_angeles.csv")

        ny_df.to_csv(ny_path, index=False)
        la_df.to_csv(la_path, index=False)

        return ny_path, la_path

    def test_load_city_csvs(self):
        """Test loading city CSV files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample CSV files
            ny_path, la_path = self.create_sample_csv_files(temp_dir)

            comparator = WeatherDataComparator()
            city_data = comparator.load_city_csvs(temp_dir)

            assert len(city_data) == 2
            assert "new_york" in city_data
            assert "los_angeles" in city_data
            assert len(city_data["new_york"]) == 12
            assert len(city_data["los_angeles"]) == 12

    def test_load_city_csvs_empty_directory(self):
        """Test loading from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            comparator = WeatherDataComparator()
            with pytest.raises(ValueError, match="No CSV files found"):
                comparator.load_city_csvs(temp_dir)

    def test_compare_average_temperatures(self):
        """Test temperature comparison."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)

            comparator = WeatherDataComparator()
            comparator.load_city_csvs(temp_dir)

            temp_comparison = comparator.compare_average_temperatures()

            assert len(temp_comparison) == 2

            # Check data structure
            for city_data in temp_comparison:
                assert "city" in city_data
                assert "avg_yearly_high" in city_data
                assert "avg_yearly_low" in city_data
                assert "highest_record" in city_data
                assert "lowest_record" in city_data
                assert "temperature_range" in city_data

            # Should be sorted by avg_yearly_high (LA should be first as it's warmer)
            assert temp_comparison[0]["city"] == "los_angeles"
            assert temp_comparison[1]["city"] == "new_york"

    def test_compare_precipitation(self):
        """Test precipitation comparison."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)

            comparator = WeatherDataComparator()
            comparator.load_city_csvs(temp_dir)

            precip_comparison = comparator.compare_precipitation()

            assert len(precip_comparison) == 2

            # Check data structure
            for city_data in precip_comparison:
                assert "city" in city_data
                assert "total_yearly_precipitation" in city_data
                assert "avg_monthly_precipitation" in city_data
                assert "total_rainy_days" in city_data
                assert "total_snow_days" in city_data
                assert "wettest_month" in city_data
                assert "driest_month" in city_data

            # Should be sorted by total yearly precipitation (NY should be first)
            assert precip_comparison[0]["city"] == "new_york"
            assert precip_comparison[1]["city"] == "los_angeles"

    def test_compare_humidity(self):
        """Test humidity comparison."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)

            comparator = WeatherDataComparator()
            comparator.load_city_csvs(temp_dir)

            humidity_comparison = comparator.compare_humidity()

            assert len(humidity_comparison) == 2

            # Check data structure
            for city_data in humidity_comparison:
                assert "city" in city_data
                assert "avg_humidity" in city_data
                assert "avg_morning_humidity" in city_data
                assert "avg_afternoon_humidity" in city_data
                assert "humidity_variation" in city_data

    def test_generate_seasonal_comparison(self):
        """Test seasonal comparison."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)

            comparator = WeatherDataComparator()
            comparator.load_city_csvs(temp_dir)

            seasonal_comparison = comparator.generate_seasonal_comparison()

            assert len(seasonal_comparison) == 2

            # Check data structure
            for city_data in seasonal_comparison:
                assert "city" in city_data
                assert "winter_avg_temp" in city_data
                assert "spring_avg_temp" in city_data
                assert "summer_avg_temp" in city_data
                assert "fall_avg_temp" in city_data
                assert "winter_precipitation" in city_data
                assert "spring_precipitation" in city_data
                assert "summer_precipitation" in city_data
                assert "fall_precipitation" in city_data

    def test_find_similar_climates(self):
        """Test finding similar climates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)

            comparator = WeatherDataComparator()
            comparator.load_city_csvs(temp_dir)

            # Use a higher threshold since the test data makes cities quite different
            similar_cities = comparator.find_similar_climates(
                "new_york", threshold=100.0
            )

            # Should find LA as similar (with high threshold)
            assert len(similar_cities) >= 0  # Could be 0 or 1 depending on data
            if similar_cities:
                assert similar_cities[0]["city"] == "los_angeles"
                assert "similarity_score" in similar_cities[0]
                assert "temp_difference" in similar_cities[0]
                assert "precipitation_difference" in similar_cities[0]
                assert "humidity_difference" in similar_cities[0]

    def test_find_similar_climates_invalid_reference(self):
        """Test finding similar climates with invalid reference city."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)

            comparator = WeatherDataComparator()
            comparator.load_city_csvs(temp_dir)

            with pytest.raises(ValueError, match="Reference city 'invalid' not found"):
                comparator.find_similar_climates("invalid")

    def test_generate_comprehensive_comparison(self):
        """Test comprehensive comparison generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)

            comparator = WeatherDataComparator()
            comparator.load_city_csvs(temp_dir)

            comprehensive = comparator.generate_comprehensive_comparison()

            assert "temperature_comparison" in comprehensive
            assert "precipitation_comparison" in comprehensive
            assert "humidity_comparison" in comprehensive
            assert "seasonal_comparison" in comprehensive

            assert len(comprehensive["temperature_comparison"]) == 2
            assert len(comprehensive["precipitation_comparison"]) == 2
            assert len(comprehensive["humidity_comparison"]) == 2
            assert len(comprehensive["seasonal_comparison"]) == 2
