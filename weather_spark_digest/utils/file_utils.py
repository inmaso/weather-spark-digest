"""File utilities for weather spark digest."""

import csv
import os
from pathlib import Path
from typing import Dict, List, Any


def read_cities_file(file_path: str) -> List[str]:
    """Read cities from a text file, one city per line."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            cities = [line.strip() for line in f if line.strip()]
        return cities
    except FileNotFoundError:
        raise FileNotFoundError(f"Cities file not found: {file_path}")


def write_csv_data(
    file_path: str, data: List[Dict[str, Any]], fieldnames: List[str] = None
):
    """Write data to a CSV file."""
    if not data:
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    # Ensure directory exists (only if there's a directory in the path)
    dir_path = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)


def read_csv_data(file_path: str) -> List[Dict[str, Any]]:
    """Read data from a CSV file."""
    data = []
    try:
        with open(file_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    return data


def ensure_output_directory(directory: str) -> Path:
    """Ensure output directory exists."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path
