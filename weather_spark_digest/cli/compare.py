"""CLI program for comparing weather data across cities."""

import typer
from pathlib import Path
from typing import Optional, List
import sys

from ..core.comparator import WeatherDataComparator
from ..utils.file_utils import write_csv_data

app = typer.Typer(help="Compare weather data across cities")


@app.command()
def compare(
    csv_dir: str = typer.Argument(..., help="Directory containing city CSV files"),
    output_file: str = typer.Option(
        "weather_comparison.csv", "-o", "--output", help="Output CSV file"
    ),
    comparison_type: str = typer.Option(
        "all",
        "-t",
        "--type",
        help="Type of comparison (all, temperature, precipitation, humidity, seasonal)",
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Enable verbose output"
    ),
):
    """
    Compare weather data across multiple cities.

    This command processes CSV files from the specified directory and generates
    a comparison report saved as a single CSV file.
    """
    try:
        # Validate input directory
        csv_path = Path(csv_dir)
        if not csv_path.exists():
            typer.echo(f"Error: CSV directory '{csv_dir}' not found")
            raise typer.Exit(1)

        if not csv_path.is_dir():
            typer.echo(f"Error: '{csv_dir}' is not a directory")
            raise typer.Exit(1)

        if verbose:
            typer.echo(f"Loading CSV files from {csv_dir}")

        # Initialize comparator and load data
        comparator = WeatherDataComparator()
        city_data = comparator.load_city_csvs(csv_dir)

        if not city_data:
            typer.echo("Error: No valid CSV files found in the directory")
            raise typer.Exit(1)

        if verbose:
            typer.echo(
                f"Loaded data for {len(city_data)} cities: {', '.join(city_data.keys())}"
            )

        # Generate comparison based on type
        comparison_data = []

        if comparison_type in ["all", "temperature"]:
            temp_comparison = comparator.compare_average_temperatures()
            if comparison_type == "temperature":
                comparison_data = temp_comparison
            else:
                # Add comparison type prefix for "all" mode
                for row in temp_comparison:
                    row["comparison_type"] = "temperature"
                comparison_data.extend(temp_comparison)

        if comparison_type in ["all", "precipitation"]:
            precip_comparison = comparator.compare_precipitation()
            if comparison_type == "precipitation":
                comparison_data = precip_comparison
            else:
                for row in precip_comparison:
                    row["comparison_type"] = "precipitation"
                comparison_data.extend(precip_comparison)

        if comparison_type in ["all", "humidity"]:
            humidity_comparison = comparator.compare_humidity()
            if comparison_type == "humidity":
                comparison_data = humidity_comparison
            else:
                for row in humidity_comparison:
                    row["comparison_type"] = "humidity"
                comparison_data.extend(humidity_comparison)

        if comparison_type in ["all", "seasonal"]:
            seasonal_comparison = comparator.generate_seasonal_comparison()
            if comparison_type == "seasonal":
                comparison_data = seasonal_comparison
            else:
                for row in seasonal_comparison:
                    row["comparison_type"] = "seasonal"
                comparison_data.extend(seasonal_comparison)

        if not comparison_data:
            typer.echo("Error: No comparison data generated")
            raise typer.Exit(1)

        # Save comparison data
        write_csv_data(output_file, comparison_data)

        typer.echo(f"✅ Comparison complete!")
        typer.echo(f"Results saved to: {output_file}")
        typer.echo(
            f"Compared {len(city_data)} cities with {len(comparison_data)} data points"
        )

        if verbose:
            typer.echo("\nSample of comparison data:")
            for i, row in enumerate(comparison_data[:3]):
                typer.echo(f"  {i+1}. {row}")

    except Exception as e:
        typer.echo(f"Error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        raise typer.Exit(1)


@app.command()
def similar(
    csv_dir: str = typer.Argument(..., help="Directory containing city CSV files"),
    reference_city: str = typer.Argument(
        ..., help="Reference city to find similar climates"
    ),
    output_file: str = typer.Option(
        "similar_climates.csv", "-o", "--output", help="Output CSV file"
    ),
    threshold: float = typer.Option(
        10.0, "-t", "--threshold", help="Similarity threshold (lower = more similar)"
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Enable verbose output"
    ),
):
    """
    Find cities with similar climate to a reference city.
    """
    try:
        # Validate input directory
        csv_path = Path(csv_dir)
        if not csv_path.exists():
            typer.echo(f"Error: CSV directory '{csv_dir}' not found")
            raise typer.Exit(1)

        if verbose:
            typer.echo(f"Loading CSV files from {csv_dir}")

        # Initialize comparator and load data
        comparator = WeatherDataComparator()
        city_data = comparator.load_city_csvs(csv_dir)

        if not city_data:
            typer.echo("Error: No valid CSV files found in the directory")
            raise typer.Exit(1)

        # Clean reference city name to match file naming convention
        clean_ref_city = reference_city.replace(" ", "_").replace(",", "").lower()

        # Find the actual city name in the data
        actual_ref_city = None
        for city_key in city_data.keys():
            if city_key.lower() == clean_ref_city:
                actual_ref_city = city_key
                break

        if not actual_ref_city:
            typer.echo(f"Error: Reference city '{reference_city}' not found in data")
            typer.echo(f"Available cities: {', '.join(city_data.keys())}")
            raise typer.Exit(1)

        if verbose:
            typer.echo(f"Finding cities similar to {actual_ref_city}")

        # Find similar cities
        similar_cities = comparator.find_similar_climates(actual_ref_city, threshold)

        if not similar_cities:
            typer.echo(f"No cities found with similarity threshold {threshold}")
            typer.echo("Try increasing the threshold value")
            raise typer.Exit(1)

        # Add reference city info to each row
        for row in similar_cities:
            row["reference_city"] = actual_ref_city
            row["threshold_used"] = threshold

        # Save results
        write_csv_data(output_file, similar_cities)

        typer.echo(f"✅ Found {len(similar_cities)} cities similar to {actual_ref_city}")
        typer.echo(f"Results saved to: {output_file}")

        if verbose:
            typer.echo("\nMost similar cities:")
            for i, city in enumerate(similar_cities[:5]):
                typer.echo(
                    f"  {i+1}. {city['city']} (similarity score: {city['similarity_score']})"
                )

    except Exception as e:
        typer.echo(f"Error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        raise typer.Exit(1)


@app.command()
def summary(
    csv_dir: str = typer.Argument(..., help="Directory containing city CSV files"),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Enable verbose output"
    ),
):
    """
    Display a summary of available weather data.
    """
    try:
        # Validate input directory
        csv_path = Path(csv_dir)
        if not csv_path.exists():
            typer.echo(f"Error: CSV directory '{csv_dir}' not found")
            raise typer.Exit(1)

        # Initialize comparator and load data
        comparator = WeatherDataComparator()
        city_data = comparator.load_city_csvs(csv_dir)

        if not city_data:
            typer.echo("Error: No valid CSV files found in the directory")
            raise typer.Exit(1)

        typer.echo(f"📊 Weather Data Summary")
        typer.echo(f"Directory: {csv_dir}")
        typer.echo(f"Cities loaded: {len(city_data)}")
        typer.echo()

        # Show city names and record counts
        typer.echo("Cities and record counts:")
        for city, df in city_data.items():
            typer.echo(f"  • {city}: {len(df)} records")

        if verbose:
            # Show column information
            typer.echo("\nData columns available:")
            if city_data:
                first_city_df = next(iter(city_data.values()))
                for col in first_city_df.columns:
                    typer.echo(f"  • {col}")

    except Exception as e:
        typer.echo(f"Error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
