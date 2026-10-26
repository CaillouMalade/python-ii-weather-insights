# Pitwall and the Python II assignment

Arthur authorized a richer racetrack product and allowed a different technology stack. The original brief nevertheless explicitly names Python OOP, OpenWeather and Streamlit. The main application runs locally on localhost using React/Vite, with its source repository on GitHub; the adjacent `python-companion/` provides the inspectable Python and optional Streamlit implementation. This mapping is implementation evidence, not a promise of a grade.

The original brief is preserved at `assignment/BRIEF.md`; `summary.md` and `starter_template/` are retained. The root `README.md` now explains how to run the actual application.

| Requirement from the original brief | Implementation / remaining responsibility |
|---|---|
| Meaningful inheritance | `APIClient` owns HTTP/JSON/error handling; `OpenWeatherClient`, `OpenMeteoClient` and `GeocodingClient` implement provider-specific requests and parsing. |
| Intentional encapsulation | Public domain values; `_get`, `_api_key`, `_opener` and `_connect` are internal/protected. No unnecessary name-mangling is used. Secrets are excluded from repr and exception output. |
| Special method and computed property | Validated `Location.__str__`, meaningful `WeatherSnapshot.__lt__`, derived dewpoint spread and apparent-temperature delta. |
| OpenWeather key from dotenv | `load_config()` reads ignored `variables.env` and the environment. A placeholder example is supplied. No real OpenWeather key was read or live-tested in this build. |
| Input, location, key and network failures distinguished | Separate `InputError`, `LocationNotFoundError`, `AuthenticationError`, `RateLimitError`, `NetworkError` and `DataError`; per-provider/location batch isolation. |
| Every success logged | Python app appends current-condition snapshots to local SQLite with fetched and provider-valid UTC timestamps; export CSV is supported. The browser app separately retains forecast snapshots in device-local IndexedDB, not a server database or cloud account. |
| Trend analytics | Provider-and-coordinate-separated temperature trends; change requires two distinct valid times. One capture is explicitly insufficient for a trend. |
| Cross-location comparison | Latest logged temperature/wind by location, preserving source and valid times; stale values are visible. |
| Derived metric | Air-minus-dewpoint and feels-like-minus-air in °C. Estimated dewpoint is identified as derived. Neither is presented as grip. |
| At least two Streamlit views and two charts | Optional `streamlit_app.py` contains Live conditions, Analytics and Sources & export; cross-location bar chart and logged-temperature line chart, with units. Adding coordinates/search and source selection are interactive. |
| Installable `src/` package | `python-companion/pyproject.toml`, `src/pitwall_weather/`, CLI entrypoint and clean setup instructions. |
| AI collaboration record | Contemporaneous `python-companion/PROMPTS.md` documents produced, kept, changed and rejected work. Actual AI-authored commits should include a Codex co-author trailer. |
| Real accumulated dataset committed | Three real Open-Meteo current snapshots are provided as a timestamped CSV. Multi-day history still needs to accumulate through real usage; it was not fabricated. |
| Genuine contributions from each group member | Still a group responsibility. No teammate commits, review or understanding are claimed by this build. |
| Instructor access and final submission channel | Still a group responsibility; neither repository sharing nor submission was changed. |

The existing repository history and supplied scaffold are retained; the original brief was preserved before the root README became application documentation. The main frontend's use of several named model outputs does not imply several statistically independent providers: shared model ancestry is disclosed in the product. Historical radar is not presented as a forecast or minute-exact rain arrival.

Verification on 26 October 2026: isolated clean package/UI installation completed; 18 unit tests passed; the CLI and all three Streamlit views passed smoke checks. A live refresh stored two real Open-Meteo results while the missing OpenWeather key produced two isolated, clear warnings. The packaged CSV separately retains three genuine same-session responses.
