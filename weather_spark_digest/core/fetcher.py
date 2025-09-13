"""Core module for fetching weather data from weather spark."""

import requests
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
import tempfile
import os
from PIL import Image
import cairosvg


class WeatherDataFetcher:
    """Fetches weather data from weather spark and processes it."""

    def __init__(self, base_url: str = "https://weatherspark.com"):
        self.base_url = base_url
        self.session = requests.Session()
        # Set a user agent to be polite
        self.session.headers.update(
            {"User-Agent": "WeatherSparkDigest/0.1.0 (Research Tool)"}
        )

    def fetch_city_data(self, city_name: str) -> Dict[str, Any]:
        """
        Fetch weather data for a given city.

        This is a mock implementation since we don't have access to the actual
        weather spark API. In a real implementation, this would:
        1. Make HTTP request to weather spark for the city
        2. Parse the SVG/chart data
        3. Convert SVG to image using cairosvg
        4. Process image with PIL to extract data points
        5. Return structured data
        """
        # Simulate API delay
        time.sleep(0.1)

        # Mock data structure representing what would be extracted from weather charts
        mock_data = {
            "city": city_name,
            "temperature_data": self._generate_mock_temperature_data(),
            "humidity_data": self._generate_mock_humidity_data(),
            "precipitation_data": self._generate_mock_precipitation_data(),
            "fetch_timestamp": time.time(),
        }

        return mock_data

    def _generate_mock_temperature_data(self) -> List[Dict[str, Any]]:
        """Generate mock temperature data points."""
        import random

        data = []
        for month in range(1, 13):
            data.append(
                {
                    "month": month,
                    "avg_high": round(random.uniform(10, 35), 1),
                    "avg_low": round(random.uniform(-5, 20), 1),
                    "record_high": round(random.uniform(25, 45), 1),
                    "record_low": round(random.uniform(-15, 5), 1),
                }
            )
        return data

    def _generate_mock_humidity_data(self) -> List[Dict[str, Any]]:
        """Generate mock humidity data points."""
        import random

        data = []
        for month in range(1, 13):
            data.append(
                {
                    "month": month,
                    "avg_humidity": round(random.uniform(30, 90), 1),
                    "morning_humidity": round(random.uniform(40, 95), 1),
                    "afternoon_humidity": round(random.uniform(25, 85), 1),
                }
            )
        return data

    def _generate_mock_precipitation_data(self) -> List[Dict[str, Any]]:
        """Generate mock precipitation data points."""
        import random

        data = []
        for month in range(1, 13):
            data.append(
                {
                    "month": month,
                    "total_precipitation": round(random.uniform(0, 200), 1),
                    "rainy_days": random.randint(0, 20),
                    "snow_days": random.randint(0, 10) if month in [12, 1, 2, 3] else 0,
                }
            )
        return data

    def process_svg_to_data(self, svg_content: str) -> List[Dict[str, Any]]:
        """
        Process SVG chart content to extract data points.

        This would use cairosvg to convert SVG to PNG, then PIL to process
        the image and extract data points from the chart.
        """
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as svg_file:
            svg_file.write(svg_content.encode("utf-8"))
            svg_path = svg_file.name

        try:
            # Convert SVG to PNG using cairosvg
            png_path = svg_path.replace(".svg", ".png")
            cairosvg.svg2png(url=svg_path, write_to=png_path)

            # Process image with PIL
            with Image.open(png_path) as img:
                # In a real implementation, this would analyze the image
                # to extract data points from the chart
                width, height = img.size

                # Mock data extraction
                extracted_data = []
                for i in range(12):  # 12 months
                    extracted_data.append(
                        {"month": i + 1, "value": width + height + i}  # Mock extraction
                    )

                return extracted_data

        finally:
            # Clean up temporary files
            if os.path.exists(svg_path):
                os.unlink(svg_path)
            png_path = svg_path.replace(".svg", ".png")
            if os.path.exists(png_path):
                os.unlink(png_path)

    def flatten_city_data_for_csv(
        self, city_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Flatten city data structure for CSV output."""
        flattened_data = []

        temp_data = city_data.get("temperature_data", [])
        humidity_data = city_data.get("humidity_data", [])
        precip_data = city_data.get("precipitation_data", [])

        for month in range(1, 13):
            month_data = {"city": city_data["city"], "month": month}

            # Add temperature data
            temp_month = next((t for t in temp_data if t["month"] == month), {})
            month_data.update(
                {
                    "avg_high_temp": temp_month.get("avg_high", 0),
                    "avg_low_temp": temp_month.get("avg_low", 0),
                    "record_high_temp": temp_month.get("record_high", 0),
                    "record_low_temp": temp_month.get("record_low", 0),
                }
            )

            # Add humidity data
            humidity_month = next((h for h in humidity_data if h["month"] == month), {})
            month_data.update(
                {
                    "avg_humidity": humidity_month.get("avg_humidity", 0),
                    "morning_humidity": humidity_month.get("morning_humidity", 0),
                    "afternoon_humidity": humidity_month.get("afternoon_humidity", 0),
                }
            )

            # Add precipitation data
            precip_month = next((p for p in precip_data if p["month"] == month), {})
            month_data.update(
                {
                    "total_precipitation": precip_month.get("total_precipitation", 0),
                    "rainy_days": precip_month.get("rainy_days", 0),
                    "snow_days": precip_month.get("snow_days", 0),
                }
            )

            flattened_data.append(month_data)

        return flattened_data
