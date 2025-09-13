"""Core module for comparing weather data across cities."""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import glob
import os


class WeatherDataComparator:
    """Compares weather data across multiple cities."""

    def __init__(self):
        self.city_data = {}

    def load_city_csvs(self, csv_directory: str) -> Dict[str, pd.DataFrame]:
        """Load all city CSV files from a directory."""
        csv_files = glob.glob(os.path.join(csv_directory, "*.csv"))

        if not csv_files:
            raise ValueError(f"No CSV files found in directory: {csv_directory}")

        for csv_file in csv_files:
            city_name = Path(csv_file).stem
            try:
                df = pd.read_csv(csv_file)
                self.city_data[city_name] = df
            except Exception as e:
                print(f"Warning: Could not load {csv_file}: {e}")

        return self.city_data

    def compare_average_temperatures(self) -> List[Dict[str, Any]]:
        """Compare average temperatures across cities."""
        comparison_data = []

        for city, df in self.city_data.items():
            if df.empty:
                continue

            avg_yearly_high = df["avg_high_temp"].mean()
            avg_yearly_low = df["avg_low_temp"].mean()
            highest_record = df["record_high_temp"].max()
            lowest_record = df["record_low_temp"].min()

            comparison_data.append(
                {
                    "city": city,
                    "avg_yearly_high": round(avg_yearly_high, 1),
                    "avg_yearly_low": round(avg_yearly_low, 1),
                    "highest_record": round(highest_record, 1),
                    "lowest_record": round(lowest_record, 1),
                    "temperature_range": round(avg_yearly_high - avg_yearly_low, 1),
                }
            )

        # Sort by average yearly high temperature
        comparison_data.sort(key=lambda x: x["avg_yearly_high"], reverse=True)
        return comparison_data

    def compare_precipitation(self) -> List[Dict[str, Any]]:
        """Compare precipitation data across cities."""
        comparison_data = []

        for city, df in self.city_data.items():
            if df.empty:
                continue

            total_yearly_precip = df["total_precipitation"].sum()
            avg_monthly_precip = df["total_precipitation"].mean()
            total_rainy_days = df["rainy_days"].sum()
            total_snow_days = df["snow_days"].sum()
            wettest_month = df.loc[df["total_precipitation"].idxmax(), "month"]
            driest_month = df.loc[df["total_precipitation"].idxmin(), "month"]

            comparison_data.append(
                {
                    "city": city,
                    "total_yearly_precipitation": round(total_yearly_precip, 1),
                    "avg_monthly_precipitation": round(avg_monthly_precip, 1),
                    "total_rainy_days": int(total_rainy_days),
                    "total_snow_days": int(total_snow_days),
                    "wettest_month": int(wettest_month),
                    "driest_month": int(driest_month),
                }
            )

        # Sort by total yearly precipitation
        comparison_data.sort(
            key=lambda x: x["total_yearly_precipitation"], reverse=True
        )
        return comparison_data

    def compare_humidity(self) -> List[Dict[str, Any]]:
        """Compare humidity data across cities."""
        comparison_data = []

        for city, df in self.city_data.items():
            if df.empty:
                continue

            avg_humidity = df["avg_humidity"].mean()
            avg_morning_humidity = df["morning_humidity"].mean()
            avg_afternoon_humidity = df["afternoon_humidity"].mean()
            humidity_variation = df["avg_humidity"].std()

            comparison_data.append(
                {
                    "city": city,
                    "avg_humidity": round(avg_humidity, 1),
                    "avg_morning_humidity": round(avg_morning_humidity, 1),
                    "avg_afternoon_humidity": round(avg_afternoon_humidity, 1),
                    "humidity_variation": round(humidity_variation, 1),
                }
            )

        # Sort by average humidity
        comparison_data.sort(key=lambda x: x["avg_humidity"], reverse=True)
        return comparison_data

    def generate_seasonal_comparison(self) -> List[Dict[str, Any]]:
        """Generate seasonal comparison across cities."""
        seasonal_data = []

        # Define seasons
        seasons = {
            "Winter": [12, 1, 2],
            "Spring": [3, 4, 5],
            "Summer": [6, 7, 8],
            "Fall": [9, 10, 11],
        }

        for city, df in self.city_data.items():
            if df.empty:
                continue

            city_seasonal = {"city": city}

            for season_name, months in seasons.items():
                season_df = df[df["month"].isin(months)]

                if not season_df.empty:
                    city_seasonal.update(
                        {
                            f"{season_name.lower()}_avg_temp": round(
                                (
                                    season_df["avg_high_temp"].mean()
                                    + season_df["avg_low_temp"].mean()
                                )
                                / 2,
                                1,
                            ),
                            f"{season_name.lower()}_precipitation": round(
                                season_df["total_precipitation"].sum(), 1
                            ),
                            f"{season_name.lower()}_humidity": round(
                                season_df["avg_humidity"].mean(), 1
                            ),
                        }
                    )

            seasonal_data.append(city_seasonal)

        return seasonal_data

    def find_similar_climates(
        self, reference_city: str, threshold: float = 10.0
    ) -> List[Dict[str, Any]]:
        """Find cities with similar climate to a reference city."""
        if reference_city not in self.city_data:
            raise ValueError(f"Reference city '{reference_city}' not found in data")

        ref_df = self.city_data[reference_city]
        if ref_df.empty:
            return []

        ref_avg_temp = (
            ref_df["avg_high_temp"].mean() + ref_df["avg_low_temp"].mean()
        ) / 2
        ref_precipitation = ref_df["total_precipitation"].sum()
        ref_humidity = ref_df["avg_humidity"].mean()

        similar_cities = []

        for city, df in self.city_data.items():
            if city == reference_city or df.empty:
                continue

            city_avg_temp = (df["avg_high_temp"].mean() + df["avg_low_temp"].mean()) / 2
            city_precipitation = df["total_precipitation"].sum()
            city_humidity = df["avg_humidity"].mean()

            # Calculate similarity score (lower is more similar)
            temp_diff = abs(city_avg_temp - ref_avg_temp)
            precip_diff = (
                abs(city_precipitation - ref_precipitation) / 10
            )  # Scale down precipitation
            humidity_diff = abs(city_humidity - ref_humidity)

            similarity_score = temp_diff + precip_diff + humidity_diff

            if similarity_score <= threshold:
                similar_cities.append(
                    {
                        "city": city,
                        "similarity_score": round(similarity_score, 2),
                        "temp_difference": round(temp_diff, 1),
                        "precipitation_difference": round(
                            city_precipitation - ref_precipitation, 1
                        ),
                        "humidity_difference": round(humidity_diff, 1),
                    }
                )

        # Sort by similarity score (most similar first)
        similar_cities.sort(key=lambda x: x["similarity_score"])
        return similar_cities

    def generate_comprehensive_comparison(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate a comprehensive comparison report."""
        return {
            "temperature_comparison": self.compare_average_temperatures(),
            "precipitation_comparison": self.compare_precipitation(),
            "humidity_comparison": self.compare_humidity(),
            "seasonal_comparison": self.generate_seasonal_comparison(),
        }
