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
