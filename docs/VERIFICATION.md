# Verification — local application, 26 October 2026

## Final architecture

The application source is prepared for the existing private `Arthur-Brht/python-ii-weather-insights` GitHub repository. The app runs on the user's computer at `http://localhost:4173/`. Its Node server binds only to loopback and serves built application files. No GitHub Pages workflow, external application server, sign-in or hosting deployment is required.

## Automated checks

- 24 JavaScript/TypeScript tests passed: forecast-family grouping, missing data, interval alignment, circular direction, rain thresholds, session coverage, source extrema, local time/DST, browser-adapter validation/abort behavior, snapshot identity, provider Retry-After, and the loopback server's content types, traversal protection, navigation and request methods.
- 18 Python companion unit tests passed.
- TypeScript checking passed.
- Production build passed. `npm start` automatically builds and launches the real loopback application server successfully.
- CI runs the web checks and Python package tests on GitHub; the actual remote run status must be checked after pushing.

## Browser checks with real weather

The static production application loaded all five forecast feeds directly in the browser: ECMWF IFS, DWD ICON, NOAA GFS and Météo-France via Open-Meteo, plus MET Norway. All four Open-Meteo models returned 72 forecast hours; MET Norway supplied 66 available timestamps with genuinely missing hourly rain left unavailable. No API key was read or embedded.

The browser's history view showed 120 actual stored forecast rows, with source identity, fetch time and valid time preserved. History is local to the current browser origin and does not sync across devices.

Radar frames, attributed circuit outlines and UI controls loaded. Nogaro has its actual OSM outline; selecting Nordschleife does not substitute the nearby Grand Prix layout. Exact input validation, missing data, session intervals and provenance were retained from the reviewed implementation.

An offline browser reload opened the cached app shell, showed an explicit offline warning, preserved saved device-local context, and reported unavailable fresh radar. Existing cached forecasts retained their actual fetch timestamps and were not represented as new observations. Normal network conditions were restored after the check.

## Scope limits

No publication or repository visibility change is needed. Provider quotas, CORS, internet connectivity and map/radar coverage still affect live data. The app respects provider cooldowns and does not fabricate weather or history. Air/rain/model agreement are not measurements of grip, surface temperature or corner-level conditions. Team contributions, real multi-day history, instructor access and final assignment submission remain group responsibilities.
