# Fake providers stand in for the real ones, so these tests make no internet calls.

from fake_forecast import fake_forecasts

from weather_app.aggregator import FORECAST_COLUMNS, fetch_all_forecasts, points_to_frame

MONZA = {"location": "Monza", "latitude": 45.62, "longitude": 9.28}


class FakeProvider:
    """Has the same forecast() method as a real provider: returns points or raises."""

    def __init__(self, source, points=None, error=None):
        self.source = source
        self.points = points
        self.error = error

    def forecast(self, location, now=None):
        if self.error is not None:
            raise ValueError(self.error)
        return self.points


def test_points_to_frame_has_one_row_per_point():
    points = fake_forecasts()["open-meteo"]
    table = points_to_frame(points)
    assert list(table.columns) == FORECAST_COLUMNS
    assert len(table) == len(points)
    assert table["temperature"].iloc[0] == points[0].temperature


def test_all_providers_end_up_in_one_table():
    forecasts = fake_forecasts()
    providers = []
    for source in forecasts:
        providers.append(FakeProvider(source, forecasts[source]))
    table, failures = fetch_all_forecasts(MONZA, providers)
    assert failures == []
    assert len(table) == 3 * 8
    assert sorted(table["source"].unique()) == ["met-norway", "open-meteo", "openweathermap"]


def test_a_failing_provider_is_skipped_and_reported():
    forecasts = fake_forecasts()
    providers = [
        FakeProvider("open-meteo", forecasts["open-meteo"]),
        FakeProvider("met-norway", error="Could not connect to the weather service."),
    ]
    table, failures = fetch_all_forecasts(MONZA, providers)
    assert failures == ["met-norway: Could not connect to the weather service."]
    assert list(table["source"].unique()) == ["open-meteo"]


def test_no_provider_answers_gives_an_empty_table():
    providers = [FakeProvider("open-meteo", error="down"), FakeProvider("met-norway", error="down")]
    table, failures = fetch_all_forecasts(MONZA, providers)
    assert len(table) == 0
    assert list(table.columns) == FORECAST_COLUMNS
    assert len(failures) == 2
