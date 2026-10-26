"""Append-only fetched snapshots; a real dataset grows only when requests succeed."""
import csv
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .models import WeatherSnapshot

FIELDS = ["location", "latitude", "longitude", "timezone", "provider", "fetched_at", "valid_at",
          "temperature_c", "humidity_pct", "wind_kmh", "gust_kmh", "precipitation_mm",
          "precipitation_interval_minutes", "feels_like_c", "dewpoint_c", "kind"]


class SnapshotStore:
    def __init__(self, path="data/weather.sqlite3"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL,
                timezone TEXT NOT NULL, provider TEXT NOT NULL, fetched_at TEXT NOT NULL,
                valid_at TEXT NOT NULL, temperature_c REAL, humidity_pct REAL, wind_kmh REAL,
                gust_kmh REAL, precipitation_mm REAL, precipitation_interval_minutes INTEGER,
                feels_like_c REAL, dewpoint_c REAL, kind TEXT NOT NULL
            )""")
            connection.execute("CREATE INDEX IF NOT EXISTS snapshots_location_time ON snapshots(latitude, longitude, fetched_at)")

    def __repr__(self):
        return f"SnapshotStore(path={str(self.path)!r})"

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(str(self.path), timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            # sqlite3's transaction context commits/rolls back, but does not close.
            # Explicit closure also releases the database file on Windows.
            connection.close()

    def append(self, snapshot: WeatherSnapshot):
        record = snapshot.to_record()
        with self._connect() as connection:
            placeholders = ",".join("?" for _ in FIELDS)
            connection.execute("INSERT INTO snapshots (" + ",".join(FIELDS) + ") VALUES (" + placeholders + ")",
                               [record[field] for field in FIELDS])

    def history(self, location=None, provider=None, limit=10000):
        clauses, parameters = [], []
        if location:
            clauses.append("location = ?")
            parameters.append(location)
        if provider:
            clauses.append("provider = ?")
            parameters.append(provider)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        # Return recent N chronologically; older snapshots remain in the database.
        parameters.append(max(1, min(int(limit), 100000)))
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM snapshots" + where + " ORDER BY id DESC LIMIT ?", parameters).fetchall()
        return [dict(row) for row in reversed(rows)]

    def export_csv(self, destination):
        rows = self.history(limit=100000)
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=["id"] + FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)
