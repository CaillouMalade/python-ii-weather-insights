# AI collaboration log

## Repository setup — 21 October 2026

**Asked:** "just let's make a private repo with the assignments docs. linked to the group assignment's folder"

**Got:** A private GitHub repository, local Git setup in this folder, a root .gitignore, this log and PROJECT_STATE.md. Assignment documents and supplied starter code are preserved.

**Checked:** Confirmed the GitHub account and private repository in the browser. Checked local repository boundaries and the initial file list. Git status, ignored secret paths and remote synchronization are checked during setup; results are recorded in PROJECT_STATE.md.

**Kept as-is / changed / rejected:** Kept the supplied documents and starter code as-is. Added repository setup files only. No assignment implementation, dependency installation or weather fetch was requested or performed.

## Bot continuity snapshot — 23 October 2026

**Asked:** Arthur requested through COS: "Ask all bots that have a space in the vault to log a record of what they know how they work and everything about them." This bot was asked to create a comprehensive dated self-record in its existing project space, preserving historical records and distinguishing verified state from unknown capabilities.

**Got:** `BOT_SELF_RECORD_2026-10-23.md`, covering remit, assignment knowledge, relevant preferences/decisions, constraints, local project evidence, historical versus current connection checks, unresolved issues, paths and handover guidance.

**Checked:** Read applicable instructions and canonical project records; inspected local Git status, branch, origin and HEAD plus scaffold/configuration files. Re-read the saved snapshot, checked the documentation diff and confirmed that the only working-tree changes were the new snapshot and this appended log entry. No application tests or external account checks were needed for documentation.

**Kept as-is / changed / rejected:** Added a dated snapshot and appended this entry. Preserved existing records and all assignment code. No dependency installation, weather fetch, commit, push, account change or routine creation.

## Weekly bot continuity archive — 25 October 2026

**Asked:** Arthur authorized weekly self-archiving through COS: save one comprehensive dated self-record in the existing canonical project folder, preserve originals, distinguish verified from historical/unverified state, verify complete UTF-8 readback, and report quietly to COS only.

**Got:** BOT_SELF_RECORD_2026-10-25.md covering remit, knowledge, preferences/decisions, boundaries, methods, current local evidence, tool/connection limits, known routine context, unfinished work, paths and handover.

**Checked:** Read applicable AGENTS.md and PROJECT_BOT.md, canonical assignment/setup records and scaffold/configuration files. Inspected Git status/log/origin. Verified complete strict UTF-8 readback of both documentation outputs against intended text and checked documentation-only changes. No app tests or external service checks were run.

**Kept as-is / changed / rejected:** Preserved all earlier records and pre-existing changes. Added one dated snapshot and appended this entry only. No implementation, dependency installation, weather fetch, account change, routine listing/modification/testing, commit, push or submission.
## Assignment-only rollback — 28 October 2026

**Asked:** Arthur requested rollback of additions from another project, keeping only the simple assignment version.

**Got:** Restored the original assignment brief, course reference, supplied scaffold and repository setup from fc53892. Removed Pitwall implementation and its Node/React tooling from the active tree. Retained prior Git history and a local recovery bundle outside the project.

**Checked:** Compared the restored file list and scaffold against fc53892; checked the commit diff and remote synchronization. No dependencies installed, weather fetched, or assignment implementation added.

**Kept / changed / rejected:** Kept assignment sources and original starter code byte-for-byte. Preserved local AI-use documentation. Rejected unrelated Pitwall scope. Full previous Pitwall files and logs remain recoverable from the backup bundle and history.

## Repository initialization — 28 October 2026

**Asked:** Arthur requested initialization exactly as recommended by the assignment guidelines in the repository.

**Got:** Copied the supplied app.py, src/, tests/, pyproject.toml and variables.env.example to the repository root. Preserved the original starter_template and the assignment brief at assignment/BRIEF.md. Wrote the project setup README, declared pytest as a development dependency, generated uv.lock, and limited pytest discovery to the active tests/ folder to avoid duplicate template tests. Created the ignored local environment file from the example without configuring a real API key.

**Checked:** uv sync --locked succeeded; uv run pytest passed the one supplied placeholder test. Streamlit AppTest opened both supplied views without exceptions, and the installed weather_app package imported successfully. Original Python source/test files were compared by SHA-256. Git ignores variables.env, the virtual environment and generated Python metadata. No API calls were made.

**Kept as-is / changed / rejected:** Kept all supplied Python code unchanged. Changed only package/test setup and documentation. No assignment features, analytics, data collection or team details were implemented or invented.

## v0.1 general weather app — 2 November 2026

**Asked:** Arthur asked Claude Code (Opus 5.5) to build v0.1 as a simple general weather app with no racetrack features, in the style of CLASS_CONCEPTS.md plus approved exceptions: any Streamlit method (no custom CSS/HTML or multipage), any Plotly chart, OpenWeatherMap Geocoding/Current/Forecast, and pytest with small known-answer cases. Specified: a sidebar city list seeded from the log, a live card with forecast chart and sorted comparison, three log-only analytics, built-in `ValueError` for each failure mode, duplicate-safe CSV logging, and an app that opens without a key.

**Got:** `client.py`, `models.py`, `storage.py`, `analytics.py`, `config.py`, `app.py`, and 16 tests in `tests/test_analytics.py`.

**Checked:** Known-answer tests pass. With no key, AppTest ran both views without exceptions and a headless server answered its health check. In a scratch copy outside the repo (nothing committed, no real key, no real API), AppTest ran the app against a fake local server to check each error message, one failing location, no duplicate rows on rerun, and reseeding from the log. **Not checked by the agent:** the real API, and the look of the page in a browser.

**Kept / changed / rejected:**
- Kept the requested structure.
- Added beyond the literal request, each to prevent a specific failure:
  - `except requests.exceptions.RequestException`, because any other request error would otherwise reach the UI as a traceback, and its text contains the URL with the key.
  - Fixed-text network messages, for the same reason.
  - Catching `KeyError`/`IndexError` on unexpected response shapes.
  - `PermissionError` when the CSV is open in another program, which is common on Windows.
  - `encoding="utf-8"`, because the Windows default cannot write every city name and pandas reads the file back as UTF-8.
- Changed: the log stores the geocoded name, not the name `/weather` returns, because coordinates can return a nearby station's name and split one city into several.
- Changed: the header check opens the file and catches `FileNotFoundError` instead of `Path.exists()`, which is not in the class material.
- Changed: the card uses plain text lines rather than three `st.metric` columns, to avoid truncation at phone width.
- Rejected: `utc=True` timestamp parsing (only UTC timestamps are ever written), tests for storage (temporary files would need a pytest fixture, which is banned), and a persistent "removed cities" list (it would need the separate file Arthur ruled out).

### Be ready to explain: not evidenced in class material

**Streamlit (only `st.sidebar.radio` has a supplied example):** `st.set_page_config` and `st.title` (starter scaffold), `st.header`, `st.subheader`, `st.caption`, `st.write`, `st.metric`, `st.info`, `st.warning`, `st.container(border=True, width=420)`, `st.dataframe(hide_index=True)`, `st.plotly_chart`, `st.text_input`, `st.form_submit_button`, `st.sidebar.header`, `st.sidebar.caption`, `st.sidebar.info`, `st.sidebar.error`, `st.sidebar.success`, `st.sidebar.button`, `st.sidebar.form(clear_on_submit=True)`, `st.session_state`, `@st.cache_data(ttl=...)`, `st.rerun`.

**OpenWeatherMap:** `/geo/1.0/direct` (`q`, `limit`) and `/data/2.5/forecast` (`lat`, `lon`, `units`) are not in class material. `/data/2.5/weather` is, but with `q`; here it uses `lat` and `lon`.

**Plotly:** `px.bar`; `markers=True` and `color=` on `px.line`; `height=` and `legend_title=` in `update_layout`.

**Python and pandas:**
- `requests.exceptions.RequestException` (requested in an exercise only)
- `encoding="utf-8"` on `open`
- `str.isalpha` (list-level coverage only)
- `sorted(..., reverse=True)`
- `drop_duplicates(keep="last")` (class shows `keep="first"`)
- assigning `table.columns = [...]`
- `Path(__file__).resolve().parents[2]` (from the starter's `config.py`)
- `datetime.isoformat()` (`summary.md` only)
- `pytest.raises(..., match=...)`
