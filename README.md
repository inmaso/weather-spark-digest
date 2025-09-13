# Weather Spark Digest

CLI tools for fetching and analyzing weather data from weather spark websites.

## Overview

This project provides two main CLI programs:

1. **weather-fetch**: Fetches weather data for a list of cities and saves individual CSV files
2. **weather-compare**: Compares weather data across cities and generates analysis reports

## Installation

```bash
# Install with Poetry
poetry install

# Or install in development mode
pip install -e .
```

## Usage

### Weather Fetch CLI

Fetch weather data for cities:

```bash
# Create a sample cities file
poetry run weather-fetch sample-cities

# Fetch weather data for cities
poetry run weather-fetch fetch cities.txt --output ./weather_data

# Validate a cities file
poetry run weather-fetch validate cities.txt
```

### Weather Compare CLI

Compare weather data across cities:

```bash
# Get a summary of available data
poetry run weather-compare summary ./weather_data

# Compare all metrics across cities
poetry run weather-compare compare ./weather_data --output comparison.csv

# Compare only temperature data
poetry run weather-compare compare ./weather_data --type temperature --output temp_comparison.csv

# Find cities with similar climate to a reference city
poetry run weather-compare similar ./weather_data "New York, NY" --output similar.csv --threshold 20.0
```

## Features

- **TDD Development**: Comprehensive test suite with pytest
- **Poetry Dependencies**: Modern Python dependency management
- **SVG Processing**: Uses cairosvg and PIL for processing weather charts
- **CSV Output**: Clean, structured data output for further analysis
- **CLI Interface**: User-friendly command-line interface with Typer
- **Progress Tracking**: Visual progress bars for long-running operations
- **Error Handling**: Robust error handling and validation

## Architecture

```
weather_spark_digest/
├── cli/          # CLI applications (fetch.py, compare.py)
├── core/         # Core business logic (fetcher.py, comparator.py)
├── utils/        # Utility functions (file_utils.py)
└── tests/        # Test suite
```

## Development

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=weather_spark_digest

# Format code
poetry run black weather_spark_digest tests

# Check linting
poetry run flake8 weather_spark_digest tests
```

## License

MIT License
