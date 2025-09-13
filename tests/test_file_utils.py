"""Tests for the file utilities."""

import pytest
import tempfile
import os
import csv
from pathlib import Path

from weather_spark_digest.utils.file_utils import (
    read_cities_file,
    write_csv_data,
    read_csv_data,
    ensure_output_directory,
)


class TestFileUtils:
    """Test cases for file utilities."""

    def test_read_cities_file(self):
        """Test reading cities from a file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("New York, NY\n")
            f.write("Los Angeles, CA\n")
            f.write("Chicago, IL\n")
            f.write("\n")  # Empty line should be ignored
            f.write("Houston, TX\n")
            temp_file = f.name

        try:
            cities = read_cities_file(temp_file)
            assert len(cities) == 4
            assert "New York, NY" in cities
            assert "Los Angeles, CA" in cities
            assert "Chicago, IL" in cities
            assert "Houston, TX" in cities
        finally:
            os.unlink(temp_file)

    def test_read_cities_file_not_found(self):
        """Test reading non-existent cities file."""
        with pytest.raises(FileNotFoundError, match="Cities file not found"):
            read_cities_file("non_existent_file.txt")

    def test_write_csv_data(self):
        """Test writing CSV data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = os.path.join(temp_dir, "test.csv")

            test_data = [
                {"city": "New York", "temperature": 20, "humidity": 60},
                {"city": "Los Angeles", "temperature": 25, "humidity": 50},
            ]

            write_csv_data(csv_file, test_data)

            # Verify file was created and contains correct data
            assert os.path.exists(csv_file)

            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 2
                assert rows[0]["city"] == "New York"
                assert rows[0]["temperature"] == "20"
                assert rows[0]["humidity"] == "60"
                assert rows[1]["city"] == "Los Angeles"
                assert rows[1]["temperature"] == "25"
                assert rows[1]["humidity"] == "50"

    def test_write_csv_data_with_fieldnames(self):
        """Test writing CSV data with specific fieldnames."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = os.path.join(temp_dir, "test.csv")

            test_data = [
                {
                    "city": "New York",
                    "temperature": 20,
                    "humidity": 60,
                    "extra": "ignore",
                },
                {
                    "city": "Los Angeles",
                    "temperature": 25,
                    "humidity": 50,
                    "extra": "ignore",
                },
            ]

            fieldnames = ["city", "temperature", "humidity"]
            write_csv_data(csv_file, test_data, fieldnames)

            # Verify file was created with correct columns
            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                assert reader.fieldnames == fieldnames

    def test_write_csv_data_empty(self):
        """Test writing empty CSV data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = os.path.join(temp_dir, "test.csv")

            write_csv_data(csv_file, [])

            # File should not be created for empty data
            assert not os.path.exists(csv_file)

    def test_write_csv_data_creates_directory(self):
        """Test that write_csv_data creates directories if they don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = os.path.join(temp_dir, "nested", "deeper")
            csv_file = os.path.join(nested_dir, "test.csv")

            test_data = [{"city": "New York", "temperature": 20}]

            write_csv_data(csv_file, test_data)

            # Verify directory was created and file exists
            assert os.path.exists(nested_dir)
            assert os.path.exists(csv_file)

    def test_read_csv_data(self):
        """Test reading CSV data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = os.path.join(temp_dir, "test.csv")

            # Create test CSV file
            test_data = [
                {"city": "New York", "temperature": "20", "humidity": "60"},
                {"city": "Los Angeles", "temperature": "25", "humidity": "50"},
            ]

            with open(csv_file, "w", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["city", "temperature", "humidity"]
                )
                writer.writeheader()
                writer.writerows(test_data)

            # Test reading
            data = read_csv_data(csv_file)

            assert len(data) == 2
            assert data[0]["city"] == "New York"
            assert data[0]["temperature"] == "20"
            assert data[0]["humidity"] == "60"
            assert data[1]["city"] == "Los Angeles"
            assert data[1]["temperature"] == "25"
            assert data[1]["humidity"] == "50"

    def test_read_csv_data_not_found(self):
        """Test reading non-existent CSV file."""
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            read_csv_data("non_existent_file.csv")

    def test_ensure_output_directory(self):
        """Test ensuring output directory exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = os.path.join(temp_dir, "output", "data")

            path = ensure_output_directory(nested_dir)

            assert os.path.exists(nested_dir)
            assert path == Path(nested_dir)
            assert path.is_dir()

    def test_ensure_output_directory_already_exists(self):
        """Test ensuring output directory when it already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Directory already exists
            path = ensure_output_directory(temp_dir)

            assert os.path.exists(temp_dir)
            assert path == Path(temp_dir)
            assert path.is_dir()
