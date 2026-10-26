# Pitwall · Race Weather

A local racetrack weather application that compares forecasts, exposes disagreement, overlays recent radar on circuit maps, and checks the outlook during your planned sessions.

**Run it on your computer at `http://localhost:4173`.** GitHub stores the source code and runs checks. No website publication, cloud account or hosting setup is needed.

## Start Pitwall

Requires Node.js 22.13 or newer and npm. From this repository's folder:

```sh
npm ci
npm start -- --open
```

The last command builds the app, starts the local application and opens it in your browser. Keep its terminal open while using the app; press **Ctrl+C** there to stop the local server. On later launches, run `npm start -- --open` again. **Start Pitwall.cmd** is the Windows launcher; **Start Pitwall.command** is available for macOS. In PowerShell, use `npm.cmd` if script execution policy blocks `npm.ps1`.

No weather API key or account is needed for the main application. Fresh forecasts, location search, radar and map tiles need an internet connection. The application and its saved data remain local; weather requests go directly to the respective providers.

See the [local run guide](docs/RUN_LOCALLY.md) for updating, development mode and troubleshooting.

## What it does

- Save curated circuits, search towns or add an exact coordinate and timezone.
- Compare up to 72 hours of named forecasts: ECMWF IFS, DWD ICON, NOAA GFS and Météo-France through Open-Meteo, plus MET Norway Locationforecast.
- Inspect per-source precipitation charts, family-weighted summaries, air temperature, wind and gusts.
- Play recent RainViewer radar, inspect its coverage mask and overlay real mapped circuit outlines where available.
- Plan practice, qualifying and race windows in the circuit's timezone; review rain, gusts and model disagreement over overlapping hours.
- Inspect each source’s session rain/gust coverage and approximate rainfall total. Find windows that fit your session duration, with rain reported below threshold by every enabled source.
- Update saved sessions, undo a removal, and download their times as a calendar file (`.ics`).
- Back up or restore circuits, preferences and plans as local JSON; import merges plans and retains existing sessions.
- Export actual forecast/history rows as CSV and inspect how each source changes temperature, rainfall or wind for the same valid hour.

These are five forecast feeds through **two weather API transports**, not five independent forecasts. MET Norway shares ECMWF ancestry outside its regional coverage and is grouped with IFS when counting families. Other models also share observations and methods. A wet vote is the fraction of reporting families exceeding your chosen hourly amount; it is not a calibrated precipitation probability.

Precipitation is normalized to the hourly interval beginning at the displayed time. Air temperature and wind are model/provider estimates near the selected coordinates. They do not measure track temperature, grip, standing water or corner-by-corner weather. RainViewer's public radar has limited native detail; zooming over a circuit does not create finer meteorological resolution. Missing data stay unavailable rather than being replaced by dry conditions.

## Saved data and privacy

Circuits, preferences and session plans live in this browser's local storage. Real forecast snapshots are stored in **IndexedDB on this device**, under `http://localhost:4173`. They are not uploaded to GitHub, saved to a cloud database or synchronized between devices. Browser storage can be cleared or evicted; use **Weather preferences → Export backup** for plans and settings, and **History & sources → Export history** for recorded weather rows. A different browser profile, hostname or port has a separate store—use the same localhost address for daily use.

Refresh requests an update while respecting provider cooldowns. If an individual feed fails, Pitwall can retain its last successful forecast for up to 24 hours with an explicit saved-data warning and the original fetch time. It never presents that fallback as a fresh fetch. Remaining forecast hours and missing fields stay visible. The bundled map library also loads locally; fresh weather and map/radar tiles still need a connection.

Weather and mapping providers receive the requested coordinates or map area and normal connection metadata. No automatic GPS access is needed. There is no browser API-key field, login backend or secret embedded in the application. Keep credentials out of `VITE_` environment variables, whose values become part of the browser code.

A supported browser can optionally install the local interface as a PWA. That is a convenience, not a requirement. Its offline shell does not generate fresh weather or radar without a connection.

## Development and checks

```sh
npm run dev
npm test
npm run typecheck
npm run build
```

Development mode uses the Vite URL printed in the terminal and refreshes after source edits. The production build is written to `dist/`, which the local launcher serves. CI checks the web application and Python package on GitHub; it does not publish or deploy anything.

## Python II companion

[`python-companion/`](python-companion/README.md) contains the course-facing Python implementation: shared API-client inheritance, an OpenWeather subclass, validated domain objects, computed properties, safe error handling, multi-location fetching, SQLite logging, analytical views, a CLI and an optional Streamlit interface.

```sh
cd python-companion
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[ui]'
cp variables.env.example variables.env
pitwall-weather fetch --track portimao --track nogaro --track spa
python -m streamlit run streamlit_app.py
```

Open-Meteo works without a key. To fetch OpenWeather from Python, configure your own `OPENWEATHER_API_KEY` in the ignored `variables.env`. Keep it out of source control and the browser application. Python current-condition snapshots use a separate local SQLite database; they are not the browser's forecast history.

The [original assignment brief](assignment/BRIEF.md), [quick reference](summary.md) and supplied [`starter_template/`](starter_template/) are preserved. [Assignment alignment](docs/ASSIGNMENT_ALIGNMENT.md) distinguishes implemented features from remaining submission responsibilities. Genuine teammate contributions, accumulated multi-day data, instructor access and the final submission remain group responsibilities; they are not fabricated by this project.

## Repository layout

```text
web/                    React interface, browser data adapters, optional PWA assets
scripts/                Local application launcher
python-companion/       Installable Python package, Streamlit app and unit tests
tests/                  Weather, input, time and storage tests
assignment/BRIEF.md     Preserved original assignment
starter_template/       Preserved supplied scaffold
docs/                   Local setup and assignment alignment
.github/workflows/      CI checks only
```

See [`PROMPTS.md`](PROMPTS.md) for the AI collaboration record. AI-authored commits should carry the actual tool's co-author trailer; the group should be able to explain the submitted code.

## Data sources

- [Open-Meteo documentation](https://open-meteo.com/en/docs)
- [MET Norway Locationforecast](https://api.met.no/weatherapi/locationforecast/2.0/documentation)
- [RainViewer Weather Maps API](https://www.rainviewer.com/api/weather-maps-api.html)
- [OpenStreetMap contributors](https://www.openstreetmap.org/copyright)
- [F1 circuit geometry by Tomislav Bacinger](https://github.com/bacinger/f1-circuits), with its MIT license retained under `web/public/circuits/`

Provider quotas, availability, licenses and CORS policies apply. The app uses the public endpoints normally and does not proxy around access restrictions. Review the relevant plans before commercial use.
