# Data sources and interpretation

## Forecasts

- [Open-Meteo forecast documentation](https://open-meteo.com/en/docs): four separately requested model products, ECMWF IFS 0.25°, DWD ICON seamless, NOAA GFS seamless, and Météo-France seamless. Their transport is shared; they are not four independent API services. Regional seamless products can switch between models and resolutions. Model output may be interpolated to hourly steps.
- [MET Norway Locationforecast](https://api.met.no/weatherapi/locationforecast/2.0/documentation) and [data model](https://docs.api.met.no/doc/locationforecast/datamodel.html): direct second forecast API. An identifying User-Agent is sent, coordinates rounded to four decimals, and the HTTP Expires header is respected by the per-coordinate server cache. Its global forecast shares ECMWF ancestry, so it is grouped with IFS in consensus. This deliberately uses a conservative family grouping even in the Nordic domain, where regional models can differ.
- [OpenWeather current conditions](https://openweathermap.org/current): optional server environment key, `OPENWEATHER_API_KEY`. The current-conditions response is separate from the forecast models and excluded from forecast votes. The key never reaches the browser. API subscription/activation errors are isolated from the no-key sources.

Internally, valid times are UTC Unix seconds. Temperature is °C at two meters, wind/gusts km/h at ten meters, precipitation mm for one-hour intervals, pressure hPa, visibility meters. The frontend formats time in the circuit's IANA time zone. All absent scalar values remain null.

The precipitation interval is defined as the hour **beginning** at `Hour.time`. Open-Meteo returns a preceding-hour accumulation, so the amount reported at time+1 hour is paired with the interval beginning at time. MET Norway `next_1_hours` already follows this convention. A six-hour amount is never divided into six synthetic hourly amounts. A missing one-hour value remains unavailable. Open-Meteo preceding-hour maximum gust is also shifted to the hour beginning at the displayed time; MET Norway gusts retain the provider instant timestamp. Instant meteorological quantities stay at the original time.

Fetch time is when the app received a response, not the underlying model initialization. The app does not invent model cycle times. Forecasts are cached for ten minutes to reduce service load. Open-Meteo's public service is for non-commercial evaluation; review provider licensing and quotas before commercial deployment.

## Radar and mapping

- [RainViewer weather maps](https://www.rainviewer.com/api/weather-maps-api.html): past radar frames only, normally two hours at ten-minute steps. These are observations/composites, not future radar. The current live API uses opaque hashed frame paths; the app validates and preserves the returned path. The maximum native zoom is seven. Overzoom enlarges the same pixels and cannot identify rain on individual corners. Composite generation time can differ from the observation times of contributing radars. Coverage mask is available to distinguish missing coverage from transparency.
- [F1 Circuits, Tomislav Bacinger](https://github.com/bacinger/f1-circuits): nine bundled real geographic circuit outlines, downloaded 26 October 2026, under the [MIT license](/circuits/LICENSE-f1-circuits.txt). Source files are retained in `public/circuits/`. The download date does not establish when the source geometry was surveyed or edited. These outlines are not claimed to originate from OSM.
- [Nogaro / Circuit Paul Armagnac](https://www.openstreetmap.org/way/95798633): verified OSM raceway way 95798633, downloaded through the primary OSM full-way API on 26 October 2026. The original geometry is retained in `public/circuits/nogaro.geojson`, with source version and edit timestamp. © OpenStreetMap contributors, ODbL 1.0.
- [OpenStreetMap](https://www.openstreetmap.org/copyright), queried through [Overpass](https://wiki.openstreetmap.org/wiki/Overpass_API) for other locations: actual mapped raceway centerlines within six kilometers. This can include nearby kart tracks and alternate configurations. The app does not infer a boundary, turns, or sectors from weather grids. If geometry is absent/unavailable, only the selected coordinates are shown. Public Overpass servers can be slow or rate-limited; requests time out quickly and retain the location marker.

## Snapshot history

Successful model fetches save the first 24 forecast hours to a private D1 history keyed by the authenticated Site user and selected coordinates. Cached fetches are deduplicated. History exposes up to 3,000 actual stored points from the past seven days. This is forecast evolution, not a weather-station record or retrospective accuracy score. No historical samples are fabricated to make an empty chart look complete.

Named circuits are matched explicitly by circuit identifier. Nordschleife is never replaced by the nearby Nürburgring GP outline. A named layout without verified geometry shows its selected point. Custom coordinates can match a nearby bundled circuit, whose actual name is displayed.
