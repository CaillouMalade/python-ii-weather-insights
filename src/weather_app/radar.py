"""The rain radar from RainViewer: free, no key. It is not a forecast provider, so it has its own file."""

from .client import APIClient

# RainViewer's image settings: 256-pixel tiles, colour scheme 2, smoothed, with snow shown.
TILE_SETTINGS = "/256/{z}/{x}/{y}/2/1_1.png"


class RainViewerClient(APIClient):
    """Asks RainViewer for its list of radar images and builds the address of the newest one."""

    def __init__(self):
        super().__init__("https://api.rainviewer.com", None, None)

    def latest_radar_url(self):
        """Return the newest radar image address, in the {z}/{x}/{y} tile form a map fills in."""
        data = self._get("public/weather-maps.json", {})
        try:
            # The "past" list goes from oldest to newest, so the newest is the last one.
            newest = data["radar"]["past"][-1]
            return data["host"] + newest["path"] + TILE_SETTINGS
        except (KeyError, IndexError, TypeError):
            raise ValueError("RainViewer sent its radar list in an unexpected format.") from None
