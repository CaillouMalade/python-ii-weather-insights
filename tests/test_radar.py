# The radar is tested with a fake RainViewer answer, so no internet call is made.
# FakeGet and FakeResponse are the same fakes the provider tests use.

from datetime import datetime, timezone

from test_providers import FakeGet, FakeResponse

from weather_app import client
from weather_app.providers import RainViewerClient

# A small answer shaped like RainViewer's real one.
ANSWER = {
    "host": "https://tilecache.rainviewer.com",
    "radar": {"past": [{"time": 1794755400, "path": "/v2/radar/older"}, {"time": 1794756000, "path": "/v2/radar/newest"}]},
}


def radar_url_or_error(response):
    """Ask for the radar with a fake answer; return the address, or the ValueError's message."""
    original = client.requests.get
    client.requests.get = FakeGet(response)
    try:
        return RainViewerClient().radar_frames()
    except ValueError as error:
        return str(error)
    finally:
        client.requests.get = original


def test_returns_every_radar_image_oldest_first():
    frames = radar_url_or_error(FakeResponse(200, ANSWER))
    assert len(frames) == 2
    assert frames[0]["time_utc"] == datetime(2026, 11, 15, 15, 10, tzinfo=timezone.utc)
    assert frames[-1]["url"] == "https://tilecache.rainviewer.com/v2/radar/newest/256/{z}/{x}/{y}/2/1_1.png"


def test_unexpected_answer_has_its_own_message():
    message = radar_url_or_error(FakeResponse(200, {"radar": {"past": []}}))
    assert message == "RainViewer sent its radar list in an unexpected format."


def test_server_error_uses_the_shared_message():
    # The status checks come from APIClient, the base class.
    message = radar_url_or_error(FakeResponse(503))
    assert "problem on its side" in message
