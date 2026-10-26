import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from pitwall_weather.analytics import derived_metrics, latest_comparison, temperature_trends
from pitwall_weather.clients import APIClient, GeocodingClient, OpenMeteoClient, OpenWeatherClient, fetch_many
from pitwall_weather.errors import AuthenticationError, DataError, InputError, LocationNotFoundError, NetworkError, RateLimitError
from pitwall_weather.models import Location, WeatherSnapshot, optional_number
from pitwall_weather.storage import SnapshotStore

PLACE = Location("Circuit", 43, 1)


def snapshot(temp=20, time="2026-10-26T10:00:00+00:00", provider="Test"):
    return WeatherSnapshot(PLACE, provider, time, time, temp, 75, 18,
                           dewpoint_c=15, feels_like_c=19)


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, *args):
        return self.payload


def opener(payload):
    return lambda request, timeout: FakeResponse(payload)


def http_error(status):
    def fail(request, timeout):
        raise HTTPError(request.full_url, status, "provider error", {}, io.BytesIO(b""))
    return fail


class ModelsTests(unittest.TestCase):
    def test_coordinates_validated_before_network(self):
        for lat, lon in [(91, 0), (0, -181), (float("nan"), 0), (True, 0)]:
            with self.assertRaises(InputError):
                Location("x", lat, lon)

    def test_empty_name(self):
        with self.assertRaises(InputError):
            Location("  ", 0, 0)

    def test_optional_numbers_preserve_absence(self):
        for value in [None, "bad", float("nan"), float("inf"), True]:
            self.assertIsNone(optional_number(value))
        self.assertEqual(optional_number(0), 0)

    def test_metrics_and_order(self):
        self.assertEqual(snapshot().dewpoint_spread_c, 5)
        self.assertEqual(snapshot().feels_like_delta_c, -1)
        self.assertEqual([s.temperature_c for s in sorted([snapshot(None), snapshot(25), snapshot(10)])], [10, 25, None])
        self.assertIsNone(snapshot(None).dewpoint_spread_c)


class ClientsTests(unittest.TestCase):
    def test_statuses_are_distinct_and_do_not_leak_key(self):
        errors = {401: AuthenticationError, 403: AuthenticationError, 404: LocationNotFoundError,
                  429: RateLimitError, 503: NetworkError, 400: InputError}
        for status, expected in errors.items():
            client = OpenWeatherClient("secret-test-value", opener=http_error(status))
            with self.assertRaises(expected) as raised:
                client.current(PLACE)
            self.assertNotIn("secret-test-value", str(raised.exception))
            self.assertNotIn("secret-test-value", repr(client))

    def test_missing_key_rejected_without_network(self):
        def forbidden(*args, **kwargs):
            self.fail("Network should not be called")
        with self.assertRaises(AuthenticationError):
            OpenWeatherClient(None, opener=forbidden).current(PLACE)

    def test_network_failure_safe(self):
        def fail(*args, **kwargs):
            raise URLError("URL contains secret")
        with self.assertRaises(NetworkError) as raised:
            APIClient("https://example.com", opener=fail)._get("weather", {})
        self.assertNotIn("secret", str(raised.exception))

    def test_non_object_payload_rejected(self):
        with self.assertRaises(DataError):
            APIClient("https://example.com", opener=opener([]))._get("weather", {})

    def test_openweather_units_and_optional_rain(self):
        payload = {"dt": 1793008800, "main": {"temp": 20, "humidity": 50, "feels_like": 19},
                   "wind": {"speed": 5, "gust": 8}, "rain": {"1h": 0.4}}
        result = OpenWeatherClient("test", opener=opener(payload)).current(PLACE)
        self.assertEqual(result.wind_kmh, 18)
        self.assertAlmostEqual(result.gust_kmh, 28.8)
        self.assertEqual(result.precipitation_interval_minutes, 60)
        self.assertEqual(result.precipitation_mm, 0.4)
        del payload["rain"]
        self.assertIsNone(OpenWeatherClient("test", opener=opener(payload)).current(PLACE).precipitation_mm)

    def test_malformed_provider_payload_handled(self):
        with self.assertRaises(DataError):
            OpenWeatherClient("test", opener=opener({"main": [], "dt": 0})).current(PLACE)

    def test_openmeteo_interval_and_nulls(self):
        payload = {"current": {"time": 1793008800, "interval": 900, "temperature_2m": 18,
                               "relative_humidity_2m": 70, "precipitation": None}}
        result = OpenMeteoClient(opener=opener(payload)).current(PLACE)
        self.assertEqual(result.precipitation_interval_minutes, 15)
        self.assertIsNone(result.precipitation_mm)
        self.assertIsNone(result.wind_kmh)
        self.assertIn("+00:00", result.valid_at)

    def test_geocoding_bad_input_and_not_found(self):
        with self.assertRaises(InputError):
            GeocodingClient(opener=opener({})).search(" ")
        with self.assertRaises(LocationNotFoundError):
            GeocodingClient(opener=opener({})).search("unknown-city")

    def test_batch_keeps_successful_locations(self):
        class Client:
            def current(self, location):
                if location.name == "bad":
                    raise LocationNotFoundError("Not found")
                return snapshot()
        successes, failures = fetch_many([Client()], [Location("bad", 0, 0), PLACE])
        self.assertEqual(len(successes), 1)
        self.assertEqual(failures[0]["location"], "bad")


class StoreAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = SnapshotStore(Path(self.directory.name) / "weather.sqlite3")

    def test_storage_roundtrip_and_csv(self):
        self.store.append(snapshot())
        self.store.append(snapshot(None))
        rows = self.store.history()
        self.assertEqual(len(rows), 2)
        self.assertIsNone(rows[1]["temperature_c"])
        target = Path(self.directory.name) / "records.csv"
        self.assertEqual(self.store.export_csv(target), 2)
        with target.open() as file:
            exported = list(csv.DictReader(file))
        self.assertEqual(exported[1]["temperature_c"], "")

    def test_filter_is_parameterized(self):
        self.store.append(snapshot())
        self.assertEqual(self.store.history(location="' OR 1=1 --"), [])
        self.assertEqual(len(self.store.history()), 1)

    def test_trends_require_distinct_valid_times(self):
        self.store.append(snapshot())
        self.store.append(snapshot())
        first = temperature_trends(self.store.history())[0]
        self.assertEqual(first["distinct_valid_times"], 1)
        self.assertIsNone(first["change_c"])
        self.store.append(snapshot(23, "2026-10-26T11:00:00+00:00"))
        self.assertEqual(temperature_trends(self.store.history())[0]["change_c"], 3)

    def test_trend_sources_never_mixed(self):
        self.store.append(snapshot(10, provider="A"))
        self.store.append(snapshot(30, provider="B"))
        trends = temperature_trends(self.store.history())
        self.assertEqual(len(trends), 2)
        self.assertTrue(all(row["change_c"] is None for row in trends))

    def test_latest_comparison_and_derived(self):
        self.store.append(snapshot(20))
        self.store.append(snapshot(23, "2026-10-26T11:00:00+00:00"))
        self.assertEqual(latest_comparison(self.store.history())[0]["temperature_c"], 23)
        self.assertEqual(derived_metrics(self.store.history())[0]["air_minus_dewpoint_c"], 8)


if __name__ == "__main__":
    unittest.main()
