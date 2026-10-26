# Project state

## 21 October 2026 — repository setup

- Arthur authorized a private repository containing the assignment documents, linked to this folder.
- Repository: https://github.com/Arthur-Brht/python-ii-weather-insights (private, verified in GitHub browser).
- This folder is an independent Git repository, nested inside the larger AGENTIC_VAULT working tree. Run project Git commands from this folder; do not add it to the parent repository as a submodule without a separate decision.
- Assignment README.md and summary.md remain canonical; starter_template/ remains the supplied scaffold. No implementation has started.
- Root .gitignore excludes secrets, local environments and generated Python files while retaining variables.env.example.
- Correction to the bootstrap snapshot: config.py's parents[2] correctly targets starter_template/variables.env.
- Added this repository to the existing connector's selected repositories; private visibility and connector read/write permission are verified. Command-line Git has no saved authentication; the first push failed before uploading.
- Team members, deadline and app direction remain unknown.
- Next step: Arthur chooses the first assignment task. No teammate invitations or app implementation are authorized by repository setup alone.

## Verification commands

From this folder:

```powershell
git rev-parse --show-toplevel
git remote -v
git status --short --branch
git check-ignore variables.env starter_template/variables.env .venv/example
git ls-files
git ls-remote origin refs/heads/main
```

Files are uploaded through the authenticated GitHub connector. Local Git metadata is aligned to the resulting remote commit and its file tree is compared with the local index. Direct command-line pushes still require Git Credential Manager sign-in; browser sign-in and connector authentication do not provide CLI credentials.

## 26 October 2026 — Pitwall local application

Arthur explicitly authorized the racetrack weather application and its source on his GitHub, then clarified the final scope: a LOCAL app that opens on localhost, with no hosting needed. The implementation is a standalone React/Vite application under web/, a production loopback Node server under scripts/, and a Python OOP/optional Streamlit companion under python-companion/.

Run npm ci and npm start -- --open, or use Start Pitwall.command on Mac / Start Pitwall.cmd on Windows. The server binds only to 127.0.0.1. No GitHub Pages workflow, external hosting or login is needed; the existing repository stays private. CI checks the application but does not deploy it.

The original assignment brief is preserved under assignment/BRIEF.md and starter_template/ remains intact. No purchases, key copying, teammate invitations, repository visibility changes or assignment submission were performed. Verification evidence and remaining source/assessment limits are in docs/VERIFICATION.md and docs/ASSIGNMENT_ALIGNMENT.md.

## 26 October 2026 — G14 continuation, Pitwall 1.1

Arthur asked for continued improvements to the existing local application and then explicitly chose GitHub / the G14, with nothing on the Mac. The current implementation was cloned from main at b3c61e9da2c9b7d73f9517566c3110c841cf7e5e into `C:\Users\Main\OpenBot\Agents\agent-4487c022-eaf7-4954-88c5-14ffb91c1fae\pitwall-github` on the verified ROG Zephyrus G14. The older assignment checkout has local changes and was left untouched. This G14 checkout is the working source for this continuation.

Added per-source session rainfall estimates, extrema and field-specific coverage; stricter dry windows that include dissenting related feeds and fit the chosen duration; editable/deduplicated sessions, undo, local calendar exports, and validated plan/preferences backup import/export. Custom sessions retain their location and timezone. History now supports temperature, rain and wind for the same valid hour, with CSV export.

Manual refresh requests updated weather while preserving provider cooldowns. A failed feed can retain its last real forecast for up to 24 hours with original timestamps and explicit saved-data status. Refresh keeps existing data visible, the local clock advances, and returning connectivity triggers another check. First wet signals include individual source dissent even when a family median remains below threshold.

Fixed Python SQLite connection closure on Windows, upgraded Vite to 8.3.5 with a clean npm audit, bundled Leaflet locally, split vendor chunks, improved modal keyboard focus, and made repeated launches reuse the verified loopback app at the same port. CI now checks both Windows and Ubuntu; it still only checks source and never deploys anything.

Local verification: 51 web tests and 18 Python tests pass on the G14; TypeScript and production build pass; npm audit reports zero vulnerabilities. Current browser evidence and the scope of simulated checks are recorded in docs/VERIFICATION.md. The app remains `http://localhost:4173/`, with device-local data and no login or cloud deployment.
