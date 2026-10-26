# Run Pitwall locally

Pitwall runs on your computer and opens at **http://localhost:4173**. Its source belongs in the GitHub repository. GitHub Actions runs tests and build checks; it does not publish the application. There is no hosting setup, public website or cloud login to configure.

## First launch

Install Node.js 22.13 or newer, then open a terminal in the repository folder:

```sh
npm ci
npm run build
npm start -- --open
```

`npm ci` installs the versions recorded in `package-lock.json`. `npm run build` produces the application files in `dist/`. `npm start -- --open` starts the loopback-only local server and opens the application. Use the address printed by that command. Keep the terminal running; **Ctrl+C** stops it.

On macOS, **Start Pitwall.command** provides a convenient launch entry after setup. If macOS opens it in an editor rather than executing it, use the terminal command above.

For later launches, the installed dependencies and build are reused:

```sh
npm start -- --open
```

## Update the application

After obtaining a newer source revision from GitHub, stop the current local server and run:

```sh
npm ci
npm run build
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

The `.github/workflows/ci.yml` workflow runs web tests, TypeScript and a production build with Node.js 22, and the Python package tests with Python 3.11. It contains no deployment job or publication permissions.

## What stays local

Saved circuits, preferences and sessions stay in this browser's local storage. Actual forecast snapshots stay in IndexedDB on this computer. Data are associated with the full browser origin: scheme, hostname and port. Consequently, `localhost:4173`, `127.0.0.1:4173`, a different port and a different browser profile have different stores. Use **http://localhost:4173** consistently.

Nothing in this local history is uploaded to GitHub or synchronized to another computer. Browser data can still be cleared or evicted. Export CSV evidence that you want to keep outside the application. The Python companion has its own local SQLite database and separate export commands.

The app directly contacts weather, geocoding and mapping providers. Fresh weather and radar require an internet connection and provider availability. Those services receive the selected coordinates or requested map area and normal network metadata. No automatic GPS access or browser API key is required.

## Optional app installation and offline use

A supported browser may offer to install the local interface in its own window. This PWA option is optional. The application shell can be cached after a successful online launch; that does not make new forecasts, maps or radar available offline. Recorded history remains device-local, subject to browser storage availability.

## Troubleshooting

| Symptom | What to check |
|---|---|
| `node` or `npm` is not found | Install a supported Node.js version, then reopen the terminal. |
| Build files are missing | Run `npm ci` and `npm run build` from the repository root. |
| Local address does not open | Check that the launcher is still running and use its printed address. |
| Port is already in use | Close the previous Pitwall server, then restart. Avoid changing ports if you want the same saved browser data. |
| App opens but weather is unavailable | Check the connection and source status. Provider outages, quotas and CORS restrictions can affect individual feeds. |
| A map layer is blank | Check its error/coverage messages. An unloaded radar tile is not evidence of dry weather. |
| Saved history seems missing | Check the browser profile, hostname and port; clearing browser data also removes local history. |
| An update still shows the old interface | Rebuild, restart and reload. If an optional service worker remains stale, use the browser's application/site-data tools; clearing data also removes local records. |

No external publication is necessary for any of these steps.
