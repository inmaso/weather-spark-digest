"""CLI program for fetching weather data from weather spark."""

import typer
from pathlib import Path
from typing import Optional
import sys

from ..core.fetcher import WeatherDataFetcher
from ..utils.file_utils import read_cities_file, write_csv_data, ensure_output_directory

app = typer.Typer(help="Fetch weather data for cities from weather spark")


@app.command()
def fetch(
    cities_file: str = typer.Argument(
        ..., help="Path to file containing city names (one per line)"
    ),
    output_dir: str = typer.Option(
        "./output", "-o", "--output", help="Output directory for CSV files"
    ),
    base_url: str = typer.Option(
        "https://weatherspark.com", "--url", help="Base URL for weather spark"
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Enable verbose output"
    ),
):
    """
    Fetch weather data for a list of cities and save to CSV files.

    This command reads a list of cities from a file and fetches weather data
    for each city from weather spark. The data is processed and saved as
    individual CSV files (one per city) in the specified output directory.
    """
    try:
        # Validate input file
        if not Path(cities_file).exists():
            typer.echo(f"Error: Cities file '{cities_file}' not found")
            raise typer.Exit(1)

        # Read cities
        if verbose:
            typer.echo(f"Reading cities from {cities_file}")

        cities = read_cities_file(cities_file)

        if not cities:
            typer.echo("Error: No cities found in the input file")
            raise typer.Exit(1)

        if verbose:
            typer.echo(f"Found {len(cities)} cities: {', '.join(cities)}")

        # Ensure output directory exists
        output_path = ensure_output_directory(output_dir)
        if verbose:
            typer.echo(f"Output directory: {output_path}")

        # Initialize fetcher
        fetcher = WeatherDataFetcher(base_url=base_url)

        # Process each city
        total_cities = len(cities)
        with typer.progressbar(cities, label="Fetching weather data") as progress:
            for i, city in enumerate(progress):
                if verbose:
                    typer.echo(f"\nProcessing city {i+1}/{total_cities}: {city}")

                try:
                    # Fetch city data
                    city_data = fetcher.fetch_city_data(city)

                    # Flatten data for CSV
                    csv_data = fetcher.flatten_city_data_for_csv(city_data)

                    # Save to CSV
                    csv_filename = (
                        f"{city.replace(' ', '_').replace(',', '').lower()}.csv"
                    )
                    csv_path = output_path / csv_filename

                    write_csv_data(str(csv_path), csv_data)

                    if verbose:
                        typer.echo(f"Saved data for {city} to {csv_path}")

                except Exception as e:
                    typer.echo(f"Error processing {city}: {e}")
                    if verbose:
                        import traceback

                        traceback.print_exc()
                    continue

        typer.echo(f"\n✅ Successfully processed {total_cities} cities")
        typer.echo(f"CSV files saved to: {output_path}")

    except Exception as e:
        typer.echo(f"Error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        raise typer.Exit(1)


@app.command()
def validate(
    cities_file: str = typer.Argument(..., help="Path to file containing city names"),
):
    """Validate a cities file without fetching data."""
    try:
        cities = read_cities_file(cities_file)
        typer.echo(f"✅ Valid cities file with {len(cities)} cities:")
        for i, city in enumerate(cities, 1):
            typer.echo(f"  {i}. {city}")
    except Exception as e:
        typer.echo(f"❌ Error validating cities file: {e}")
        raise typer.Exit(1)


@app.command()
def sample_cities(
    output_file: str = typer.Option(
        "cities.txt", "-o", "--output", help="Output file for sample cities"
    )
):
    """Generate a sample cities file."""
    sample_cities = [
        "New York, NY",
        "Los Angeles, CA",
        "Chicago, IL",
        "Houston, TX",
        "Phoenix, AZ",
        "Philadelphia, PA",
        "San Antonio, TX",
        "San Diego, CA",
        "Dallas, TX",
        "San Jose, CA",
    ]

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for city in sample_cities:
                f.write(f"{city}\n")

        typer.echo(f"✅ Sample cities file created: {output_file}")
        typer.echo(f"Contains {len(sample_cities)} cities")

    except Exception as e:
        typer.echo(f"Error creating sample cities file: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
