# AI collaboration log

## Repository setup — 21 October 2026

**Asked:** "just let's make a private repo with the assignments docs. linked to the group assignment's folder"

**Got:** A private GitHub repository, local Git setup in this folder, a root .gitignore, this log and PROJECT_STATE.md. Assignment documents and supplied starter code are preserved.

**Checked:** Confirmed the GitHub account and private repository in the browser. Checked local repository boundaries and the initial file list. Git status, ignored secret paths and remote synchronization are checked during setup; results are recorded in PROJECT_STATE.md.

**Kept as-is / changed / rejected:** Kept the supplied documents and starter code as-is. Added repository setup files only. No assignment implementation, dependency installation or weather fetch was requested or performed.

## 26 October 2026 — Pitwall racetrack weather app

Arthur asked Codex to implement a detailed racetrack weather application inspired by this brief, allowing a different main technology stack. A first React/Worker implementation was built and live-tested, with a Python OOP/Streamlit companion. Arthur then specified that the proper application must be hosted on his GitHub.

For this GitHub implementation, Codex retained the visual interface and weather comparison logic, ported the main frontend to standalone React/Vite, removed the Sites runtime dependency, and added device-local forecast logging and a GitHub Pages deployment workflow. The original course brief was preserved in assignment/BRIEF.md; the supplied starter_template remains intact. Public website publication is pending Arthur's audience choice; the source repository remains private.

Accepted: honest missing values, named model provenance, family-aware descriptive consensus, aligned precipitation/gust intervals, actual circuit outlines with licences, genuine fetched snapshots, session-time validation, and explicit radar limits. Rejected: fake weather/history, claiming statistically independent forecasts, secret keys in browser code, unrequested subscriptions or visibility changes. Weather accuracy and multi-day history are not created by passing software tests.

Verification and hosting instructions are in docs/. The group must review and understand the implementation, contribute authentically, accumulate real data, and agree any assessment exceptions with the instructor. AI-authored implementation commits include `Co-Authored-By: Codex <noreply@openai.com>`.

### Clarification: local application, GitHub source only

Arthur clarified that he wants an app that opens on localhost, with no hosting needed. Public Pages publication was therefore cancelled. The publishing workflow was removed before any push, and no repository visibility changed. The app now has a production local Node server, npm start, and Mac/Windows launchers; its source remains in the existing private GitHub repository. CI remains enabled for code quality.
