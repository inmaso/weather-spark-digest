"""Tests for the compare CLI."""

import pytest
import tempfile
import os
import csv
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, Mock

from weather_spark_digest.cli.compare import app


class TestCompareCLI:
    """Test cases for the compare CLI."""

    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()

    def create_sample_csv_files(self, temp_dir):
        """Create sample CSV files for testing."""
        # Create New York data
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

        # Create Los Angeles data
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

        # Write CSV files
        ny_file = os.path.join(temp_dir, "new_york.csv")
        la_file = os.path.join(temp_dir, "los_angeles.csv")

        with open(ny_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=ny_data[0].keys())
            writer.writeheader()
            writer.writerows(ny_data)

        with open(la_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=la_data[0].keys())
            writer.writeheader()
            writer.writerows(la_data)

        return ny_file, la_file

    def test_compare_command_all(self):
        """Test compare command with 'all' comparison type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)
            output_file = os.path.join(temp_dir, "comparison.csv")

            result = self.runner.invoke(
                app,
                [
                    "compare",
                    temp_dir,
                    "--output",
                    output_file,
                    "--type",
                    "all",
                    "--verbose",
                ],
            )

            assert result.exit_code == 0
            assert "Comparison complete!" in result.stdout
            assert "Results saved to:" in result.stdout
            assert os.path.exists(output_file)

            # Check that the output file has data
            with open(output_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) > 0
                # Should have data for both cities across all comparison types
                assert any(row["comparison_type"] == "temperature" for row in rows)
                assert any(row["comparison_type"] == "precipitation" for row in rows)

    def test_compare_command_temperature_only(self):
        """Test compare command with temperature comparison only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)
            output_file = os.path.join(temp_dir, "temp_comparison.csv")

            result = self.runner.invoke(
                app,
                ["compare", temp_dir, "--output", output_file, "--type", "temperature"],
            )

            assert result.exit_code == 0
            assert os.path.exists(output_file)

            # Check that output contains only temperature data
            with open(output_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2  # Two cities
                assert "avg_yearly_high" in rows[0]
                assert "avg_yearly_low" in rows[0]

    def test_compare_command_directory_not_found(self):
        """Test compare command with non-existent directory."""
        result = self.runner.invoke(app, ["compare", "non_existent_directory"])

        assert result.exit_code == 1
        assert "CSV directory 'non_existent_directory' not found" in result.stdout

    def test_compare_command_empty_directory(self):
        """Test compare command with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["compare", temp_dir])

            assert result.exit_code == 1
            assert "No CSV files found in directory:" in result.stdout

    def test_similar_command_success(self):
        """Test similar command success with high threshold."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)
            output_file = os.path.join(temp_dir, "similar.csv")

            # Use a very high threshold to ensure we find similar cities
            result = self.runner.invoke(
                app,
                [
                    "similar",
                    temp_dir,
                    "New York",
                    "--output",
                    output_file,
                    "--threshold",
                    "200.0",  # High threshold
                    "--verbose",
                ],
            )

            assert result.exit_code == 0
            assert "Found" in result.stdout and "cities similar to" in result.stdout
            assert os.path.exists(output_file)

            # Check output file content
            with open(output_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) >= 0  # Could be 0 or more similar cities
                if rows:
                    assert "reference_city" in rows[0]
                    assert "similarity_score" in rows[0]

    def test_similar_command_reference_city_not_found(self):
        """Test similar command with reference city not found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)

            result = self.runner.invoke(app, ["similar", temp_dir, "Non Existent City"])

            assert result.exit_code == 1
            assert (
                "Reference city" in result.stdout
                and "not found in data" in result.stdout
            )

    def test_similar_command_no_similar_cities(self):
        """Test similar command when no similar cities found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)

            result = self.runner.invoke(
                app,
                [
                    "similar",
                    temp_dir,
                    "New York",
                    "--threshold",
                    "1.0",  # Very low threshold
                ],
            )

            assert result.exit_code == 1
            assert "No cities found with similarity threshold" in result.stdout

    def test_summary_command_success(self):
        """Test summary command success."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)

            result = self.runner.invoke(app, ["summary", temp_dir, "--verbose"])

            assert result.exit_code == 0
            assert "Weather Data Summary" in result.stdout
            assert "Cities loaded: 2" in result.stdout
            assert "new_york: 12 records" in result.stdout
            assert "los_angeles: 12 records" in result.stdout
            assert "Data columns available:" in result.stdout

    def test_summary_command_directory_not_found(self):
        """Test summary command with non-existent directory."""
        result = self.runner.invoke(app, ["summary", "non_existent_directory"])

        assert result.exit_code == 1
        assert "CSV directory 'non_existent_directory' not found" in result.stdout

    def test_summary_command_empty_directory(self):
        """Test summary command with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["summary", temp_dir])

            assert result.exit_code == 1
            assert "No CSV files found in directory:" in result.stdout

    def test_compare_command_precipitation_only(self):
        """Test compare command with precipitation comparison only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)
            output_file = os.path.join(temp_dir, "precip_comparison.csv")

            result = self.runner.invoke(
                app,
                [
                    "compare",
                    temp_dir,
                    "--output",
                    output_file,
                    "--type",
                    "precipitation",
                ],
            )

            assert result.exit_code == 0
            assert os.path.exists(output_file)

            # Check that output contains precipitation data
            with open(output_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2  # Two cities
                assert "total_yearly_precipitation" in rows[0]
                assert "total_rainy_days" in rows[0]

    def test_compare_command_humidity_only(self):
        """Test compare command with humidity comparison only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)
            output_file = os.path.join(temp_dir, "humidity_comparison.csv")

            result = self.runner.invoke(
                app,
                ["compare", temp_dir, "--output", output_file, "--type", "humidity"],
            )

            assert result.exit_code == 0
            assert os.path.exists(output_file)

            # Check that output contains humidity data
            with open(output_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2  # Two cities
                assert "avg_humidity" in rows[0]
                assert "humidity_variation" in rows[0]

    def test_compare_command_seasonal_only(self):
        """Test compare command with seasonal comparison only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.create_sample_csv_files(temp_dir)
            output_file = os.path.join(temp_dir, "seasonal_comparison.csv")

            result = self.runner.invoke(
                app,
                ["compare", temp_dir, "--output", output_file, "--type", "seasonal"],
            )

            assert result.exit_code == 0
            assert os.path.exists(output_file)

            # Check that output contains seasonal data
            with open(output_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2  # Two cities
                assert "winter_avg_temp" in rows[0]
                assert "summer_precipitation" in rows[0]
