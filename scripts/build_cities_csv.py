"""Build data/cities.csv from GeoNames. Only needed to refresh the file, not to run the app.

Data: GeoNames (https://www.geonames.org), licensed CC BY 4.0.
Download these three files from https://download.geonames.org/export/dump/ into one
folder and unzip the first: cities15000.zip, admin1CodesASCII.txt, countryInfo.txt.

Usage: uv run python scripts/build_cities_csv.py <download_folder>
"""

import sys
from pathlib import Path

import pandas as pd

CITY_COUNT = 5000
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "cities.csv"

folder = Path(sys.argv[1])

# These files have no header row; the column positions come from the GeoNames readme.
cities = pd.read_csv(folder / "cities15000.txt", sep="\t", header=None, keep_default_na=False, usecols=[1, 2, 4, 5, 8, 10, 14])
cities.columns = ["city", "ascii_name", "latitude", "longitude", "country_code", "admin_code", "population"]

admins = pd.read_csv(folder / "admin1CodesASCII.txt", sep="\t", header=None, keep_default_na=False, usecols=[0, 1])
admins.columns = ["admin_key", "admin"]

# keep_default_na=False because Namibia's country code "NA" is not a missing value.
countries = pd.read_csv(folder / "countryInfo.txt", sep="\t", comment="#", header=None, keep_default_na=False, usecols=[0, 4])
countries.columns = ["country_code", "country"]

cities = cities.sort_values("population", ascending=False).head(CITY_COUNT)
cities["admin_key"] = cities["country_code"] + "." + cities["admin_code"]
cities = cities.merge(admins, on="admin_key", how="left").merge(countries, on="country_code", how="left")
cities["admin"] = cities["admin"].fillna("")

# Same name in one country and same region: keep the largest (rows are sorted by population).
cities = cities.drop_duplicates(subset=["city", "country_code", "admin"], keep="first").copy()

# "location" is the name stored in the weather log. It only gains the region when needed.
same_name = cities.duplicated(subset=["city", "country_code"], keep=False)
cities["location"] = cities["city"] + ", " + cities["country_code"]
cities.loc[same_name, "location"] = cities["city"] + ", " + cities["admin"] + ", " + cities["country_code"]

# "label" is what the dropdown shows. The plain spelling makes "Sao Paulo" findable as well.
different_spelling = cities["city"] != cities["ascii_name"]
cities["label"] = cities["city"]
cities.loc[different_spelling, "label"] = cities["city"] + " (" + cities["ascii_name"] + ")"
cities.loc[same_name, "label"] = cities["label"] + ", " + cities["admin"]
cities["label"] = cities["label"] + ", " + cities["country"]

columns = ["location", "label", "city", "admin", "country_code", "country", "latitude", "longitude", "population"]
cities[columns].to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
print(f"Wrote {len(cities)} cities to {OUTPUT_PATH}")
