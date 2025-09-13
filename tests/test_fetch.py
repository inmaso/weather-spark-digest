"""Tests for the fetch CLI."""

import pytest
import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, Mock

from weather_spark_digest.cli.fetch import app


class TestFetchCLI:
    """Test cases for the fetch CLI."""

    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()

    def create_sample_cities_file(self, temp_dir):
        """Create a sample cities file."""
        cities_file = os.path.join(temp_dir, "cities.txt")
        with open(cities_file, "w") as f:
            f.write("New York, NY\n")
            f.write("Los Angeles, CA\n")
            f.write("Chicago, IL\n")
        return cities_file

    def test_fetch_command_success(self):
        """Test successful fetch command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cities_file = self.create_sample_cities_file(temp_dir)
            output_dir = os.path.join(temp_dir, "output")

            result = self.runner.invoke(
                app, ["fetch", cities_file, "--output", output_dir, "--verbose"]
            )

            assert result.exit_code == 0
            assert "Successfully processed 3 cities" in result.stdout
            assert "CSV files saved to:" in result.stdout

            # Check that CSV files were created
            assert os.path.exists(output_dir)
            csv_files = list(Path(output_dir).glob("*.csv"))
            assert len(csv_files) == 3

            # Check file names
            expected_files = ["new_york_ny.csv", "los_angeles_ca.csv", "chicago_il.csv"]
            actual_files = [f.name for f in csv_files]
            for expected in expected_files:
                assert expected in actual_files

    def test_fetch_command_cities_file_not_found(self):
        """Test fetch command with non-existent cities file."""
        result = self.runner.invoke(app, ["fetch", "non_existent_cities.txt"])

        assert result.exit_code == 1
        assert "Cities file 'non_existent_cities.txt' not found" in result.stdout

    def test_fetch_command_empty_cities_file(self):
        """Test fetch command with empty cities file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cities_file = os.path.join(temp_dir, "empty_cities.txt")
            with open(cities_file, "w") as f:
                f.write("")  # Empty file

            result = self.runner.invoke(app, ["fetch", cities_file])

            assert result.exit_code == 1
            assert "No cities found in the input file" in result.stdout

    def test_validate_command_success(self):
        """Test successful validate command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cities_file = self.create_sample_cities_file(temp_dir)

            result = self.runner.invoke(app, ["validate", cities_file])

            assert result.exit_code == 0
            assert "Valid cities file with 3 cities" in result.stdout
            assert "New York, NY" in result.stdout
            assert "Los Angeles, CA" in result.stdout
            assert "Chicago, IL" in result.stdout

    def test_validate_command_file_not_found(self):
        """Test validate command with non-existent file."""
        result = self.runner.invoke(app, ["validate", "non_existent_cities.txt"])

        assert result.exit_code == 1
        assert "Error validating cities file" in result.stdout

    def test_sample_cities_command(self):
        """Test sample cities command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "sample_cities.txt")

            result = self.runner.invoke(app, ["sample-cities", "--output", output_file])

            assert result.exit_code == 0
            assert "Sample cities file created" in result.stdout
            assert "Contains 10 cities" in result.stdout

            # Check that file was created and has content
            assert os.path.exists(output_file)
            with open(output_file, "r") as f:
                cities = f.readlines()
                assert len(cities) == 10
                assert "New York, NY\n" in cities
                assert "Los Angeles, CA\n" in cities

    def test_sample_cities_command_default_output(self):
        """Test sample cities command with default output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory to avoid creating files in project root
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                result = self.runner.invoke(app, ["sample-cities"])

                assert result.exit_code == 0
                assert "Sample cities file created: cities.txt" in result.stdout
                assert os.path.exists("cities.txt")
            finally:
                os.chdir(original_cwd)

    @patch("weather_spark_digest.cli.fetch.WeatherDataFetcher")
    def test_fetch_command_with_custom_url(self, mock_fetcher_class):
        """Test fetch command with custom base URL."""
        mock_fetcher = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_city_data.return_value = {
            "city": "Test City",
            "temperature_data": [],
            "humidity_data": [],
            "precipitation_data": [],
            "fetch_timestamp": 123456789,
        }
        mock_fetcher.flatten_city_data_for_csv.return_value = [
            {"city": "Test City", "month": 1, "avg_high_temp": 20}
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            cities_file = self.create_sample_cities_file(temp_dir)
            output_dir = os.path.join(temp_dir, "output")

            result = self.runner.invoke(
                app,
                [
                    "fetch",
                    cities_file,
                    "--output",
                    output_dir,
                    "--url",
                    "https://custom-weather.com",
                ],
            )

            assert result.exit_code == 0
            mock_fetcher_class.assert_called_once_with(
                base_url="https://custom-weather.com"
            )
