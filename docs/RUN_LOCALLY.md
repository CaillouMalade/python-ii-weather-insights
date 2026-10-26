# Run Pitwall locally

Pitwall runs on your computer and opens at **http://localhost:4173**. Its source belongs in the GitHub repository. GitHub Actions runs tests and build checks; it does not publish the application. There is no hosting setup, public website or cloud login to configure.

## First launch

Install Node.js 22.13 or newer, then open a terminal in the repository folder:

```sh
npm ci
npm start -- --open
```

`npm ci` installs the versions recorded in `package-lock.json`. `npm start -- --open` automatically builds the application in `dist/`, starts the loopback-only local server and opens the application. Use the address printed by that command. Keep the terminal running; **Ctrl+C** stops it.

On Windows, double-click **Start Pitwall.cmd**. In PowerShell, use `npm.cmd ci` and `npm.cmd start -- --open` if the execution policy blocks `npm.ps1`; no policy change is needed. On macOS, **Start Pitwall.command** is also available.

For later launches, installed dependencies are reused and the application is rebuilt:

```sh
npm start -- --open
```

## Update the application

After obtaining a newer source revision from GitHub, stop the current local server and run:

```sh
npm ci
npm start -- --open
```

Rebuilding updates the application files without intentionally clearing browser data. Use the same browser profile and localhost address to retain your saved circuits and forecast history.

## Development mode

```sh
npm run dev
```

Open Vite's printed local URL. This mode updates while editing the source. It normally uses a different port from the daily-use application, so it has separate browser storage. It is intended for development; the normal launcher serves the compiled app.

Checks are available separately:

```sh
npm test
npm run typecheck
npm run build
PYTHONPATH=python-companion/src python3 -m unittest discover -s python-companion/tests -v
```

On Windows, run the Python check with `$env:PYTHONPATH = 'python-companion/src'` followed by `python -m unittest discover -s python-companion/tests -v`.

The `.github/workflows/ci.yml` workflow runs web tests, TypeScript and a production build with Node.js 22, and Python package tests with Python 3.11, on **both Windows and Ubuntu**. It contains no deployment job or publication permissions.

## What stays local

Saved circuits, preferences and sessions stay in this browser's local storage. Actual forecast snapshots stay in IndexedDB on this computer. Data are associated with the full browser origin: scheme, hostname and port. Consequently, `localhost:4173`, `127.0.0.1:4173`, a different port and a different browser profile have different stores. Use **http://localhost:4173** consistently.

Nothing in this local history is uploaded to GitHub or synchronized to another computer. Browser data can still be cleared or evicted. Export CSV evidence that you want to keep outside the application. The Python companion has its own local SQLite database and separate export commands.

Use **Weather preferences → Export backup** to save circuits, preferences and planned sessions as JSON. Importing a valid backup merges sessions without deleting existing plans or duplicating identical ones, and applies its weather preferences. A circuit with conflicting coordinates/timezone is rejected. Forecast snapshots and caches are not part of this plan backup; export their actual rows through **History & sources → Export history**. **Session planner → Export calendar (.ics)** downloads session times using each circuit’s timezone; it does not send or add anything to a calendar account.

The app directly contacts weather, geocoding and mapping providers. Fresh weather and radar require an internet connection and provider availability. Those services receive the selected coordinates or requested map area and normal network metadata. No automatic GPS access or browser API key is required.

## Optional app installation and offline use

A supported browser may offer to install the local interface in its own window. This PWA option is optional. The application shell and bundled map library can be cached after a successful online launch; that does not make new forecasts, map tiles or radar available offline. If a forecast provider fails, its last successful forecast can be retained for up to 24 hours with a saved-data warning and original fetch time. Missing values and missing hours remain unavailable. Recorded history remains device-local, subject to browser storage availability.

## Troubleshooting

| Symptom | What to check |
|---|---|
| `node` or `npm` is not found | Install a supported Node.js version, then reopen the terminal. |
| Build files are missing | Run `npm ci` and `npm run build` from the repository root. |
| Local address does not open | Check that the launcher is still running and use its printed address. |
| Pitwall is already running | The launcher reuses the verified app at the same address. Reload after a new build. |
| Another application uses port 4173 | Stop that application before starting Pitwall. The launcher leaves other applications untouched and does not silently change ports. |
| App opens but weather is unavailable | Check the connection and source status. Provider outages, quotas and CORS restrictions can affect individual feeds. |
| A map layer is blank | Check its error/coverage messages. An unloaded radar tile is not evidence of dry weather. |
| Saved history seems missing | Check the browser profile, hostname and port; clearing browser data also removes local history. |
| An update still shows the old interface | Rebuild, restart and reload. If an optional service worker remains stale, use the browser's application/site-data tools; clearing data also removes local records. |

No external publication is necessary for any of these steps.
