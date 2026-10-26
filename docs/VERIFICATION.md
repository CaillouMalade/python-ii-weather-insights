# Verification — local application, 26 October 2026

## Final architecture

The application source is prepared for the existing private `Arthur-Brht/python-ii-weather-insights` GitHub repository. The app runs on the user's computer at `http://localhost:4173/`. Its Node server binds only to loopback and serves built application files. No GitHub Pages workflow, external application server, sign-in or hosting deployment is required.

## Automated checks

- 51 JavaScript/TypeScript tests passed on the G14 (Node.js 24.15): forecast-family grouping, missing data, interval alignment, circular direction, rain thresholds, overlap-weighted session coverage, source extrema, strict model-dry windows, local time/DST, safe backup merge/import, calendar timezone/escaping/folding, CSV escaping, actual IndexedDB retention/deduplication, browser-adapter validation/abort behavior, saved-source fallback and manual refresh, provider Retry-After, and loopback serving/port ownership.
- 18 Python companion unit tests passed on Windows with Python 3.13.15. Five Windows failures in the baseline were traced to unclosed SQLite connections; explicit connection closure fixes them without changing stored data or analytics.
- TypeScript checking passed.
- Production build passed, with the app, React, chart and Leaflet modules split into bounded chunks (largest JavaScript chunk about 353 kB). `npm start` automatically builds and launches the real loopback application server successfully. Opening a second launcher reuses the verified app on the same port; another application on that port is left untouched.
- Vite upgraded to 8.3.5; `npm audit` reports zero vulnerabilities for the locked dependency tree.
- CI now runs web checks and Python package tests on both Windows and Ubuntu. The actual remote run status must be checked after pushing; local success does not claim remote success.

## Browser checks with real weather

The static production application loaded all five forecast feeds directly in the browser: ECMWF IFS, DWD ICON, NOAA GFS and Météo-France via Open-Meteo, plus MET Norway. All four Open-Meteo models returned 72 forecast hours; MET Norway supplied 66 available timestamps with genuinely missing hourly rain left unavailable. No API key was read or embedded.

The browser's history view showed 120 actual stored forecast rows, with source identity, fetch time and valid time preserved. History is local to the current browser origin and does not sync across devices.

Radar frames, attributed circuit outlines and UI controls loaded. Nogaro has its actual OSM outline; selecting Nordschleife does not substitute the nearby Grand Prix layout. Exact input validation, missing data, session intervals and provenance were retained from the reviewed implementation.

An offline browser reload opened the cached app shell, showed an explicit offline warning, preserved saved device-local context, and reported unavailable fresh radar. Existing cached forecasts retained their actual fetch timestamps and were not represented as new observations. Normal network conditions were restored after the check.

## G14 continuation checks — version 1.1

The app was tested at the same `http://localhost:4173/` origin on the G14. The existing interface and all five feeds remain functional. Leaflet is now served in the local build; loading the map library no longer needs an unpkg request. Radar/map tiles still come from their attributed providers.

- Created a temporary session, changed its duration from 60 to 45 minutes, and saved the change. The persisted session count remained one. The exported calendar used the circuit’s actual timezone and a 45-minute UTC interval; its generated Blob content was inspected.
- Exported device backup JSON and inspected its format/version, five circuits, preferences and saved session. Importing the same plan added zero duplicate sessions. A file with an unsupported format was rejected while the existing session remained present. Backup import/validation and conflicting coordinates are also covered by isolated tests.
- The session source table showed real rain/gust coverage separately. MET Norway’s unavailable gusts remained a dash with 0% gust coverage, while available rain coverage remained 100%; missing gusts were not invented as zero.
- Forecast history displayed multiple genuine fetches for the same valid hour. Rainfall evolution changed the plotted field and units; history CSV contained 240 real recorded rows at export, source identity, coordinates and UTC fetch/valid timestamps. Subsequent successful live refreshes accumulated additional genuine rows.
- At a 390-pixel mobile viewport, the page had no horizontal overflow; the 740-pixel session table scrolled within its own 315-pixel region. Closed circuit navigation is hidden from accessibility navigation. Modal focus stays inside the open dialog, the background becomes inert, and Escape restores the opener.
- **Controlled provider failure:** a temporary page-level fetch override rejected weather-provider requests and an offline event exercised the UI. Four Open-Meteo sources used their actual saved snapshots; the still-valid MET Norway cache remained available in accordance with Expires. All five feeds stayed visible, failed feeds were labeled saved, and every original fetch timestamp matched the pre-failure record. Normal fetch behavior and the online state were restored, and live sources recovered. This simulates provider connectivity failure; it is not a claim that the computer’s network was disconnected.
- **Cached-shell startup:** the task-owned local Node process was stopped, and a direct HTTP check confirmed the loopback server was unavailable. Reloading the browser still opened the full cached app, including bundled chart/map code and saved context, through its service worker. The local server was then restarted and its health endpoint verified. External network connectivity remained available during this separate shell check.

No synthetic forecasts, station observations, track-surface temperatures or historical samples were added to the application. Synthetic inputs are confined to automated tests. The temporary browser verification session is removed after the checks; forecast history comes from actual provider responses and remains local.

## Scope limits

No publication or repository visibility change is needed. Provider quotas, CORS, internet connectivity and map/radar coverage still affect live data. The app respects provider cooldowns and does not fabricate weather or history. Air/rain/model agreement are not measurements of grip, surface temperature or corner-level conditions. Team contributions, real multi-day history, instructor access and final assignment submission remain group responsibilities.
