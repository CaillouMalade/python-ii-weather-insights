"""Checks for a track a user adds: name, coordinates and distance to a Grade 1 circuit."""

import math

EARTH_RADIUS_KM = 6371
MAX_DISTANCE_KM = 3
NOT_FOUND_MESSAGE = "No racetrack found at these coordinates."


def distance_km(latitude_1, longitude_1, latitude_2, longitude_2):
    """Distance in km between two points on the Earth, with the haversine formula."""
    # Haversine: the Earth is a sphere, so Pythagoras on latitude and longitude would be wrong.
    lat_1 = math.radians(latitude_1)
    lat_2 = math.radians(latitude_2)
    delta_lat = math.radians(latitude_2 - latitude_1)
    delta_lon = math.radians(longitude_2 - longitude_1)
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat_1) * math.cos(lat_2) * math.sin(delta_lon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def nearest_track(latitude, longitude, tracks):
    """Return the closest track and its distance in km, or (None, None) if the list is empty."""
    closest = None
    closest_distance = None
    for track in tracks:
        distance = distance_km(latitude, longitude, track["latitude"], track["longitude"])
        if closest_distance is None or distance < closest_distance:
            closest = track
            closest_distance = distance
    return closest, closest_distance


def read_coordinate(text, label, low, high):
    """Turn the typed text into a float between low and high, or raise ValueError."""
    try:
        value = float(text.strip())
    except ValueError:
        raise ValueError(f"{label} must be a number, for example 50.43.") from None
    # Written as "not inside" so "nan" (not a number) is rejected too: every comparison with nan is False.
    if not (low <= value <= high):
        raise ValueError(f"{label} must be between {low} and {high}.")
    return value


def check_new_track(name, latitude_text, longitude_text, tracks, grade1_tracks):
    """Check a new track before saving it and return it as a location dictionary.

    tracks is every track already in the app (for the name check),
    grade1_tracks the circuits a new track must be close to.
    """
    name = name.strip()
    if name == "":
        raise ValueError("Please enter a name for the track.")
    for track in tracks:
        # Case does not count: "monza" and "Monza" are the same name.
        if track["location"].lower() == name.lower():
            raise ValueError(f"A track called {track['location']} is already in the list.")

    latitude = read_coordinate(latitude_text, "Latitude", -90, 90)
    longitude = read_coordinate(longitude_text, "Longitude", -180, 180)

    # Only once every input is valid: a Grade 1 circuit must be within 3 km.
    circuit, distance = nearest_track(latitude, longitude, grade1_tracks)
    if circuit is None or distance > MAX_DISTANCE_KM:
        raise ValueError(NOT_FOUND_MESSAGE)

    return {
        "id": name.lower().replace(" ", "-"),
        "location": name,
        "country": circuit["country"],
        "latitude": latitude,
        "longitude": longitude,
    }
