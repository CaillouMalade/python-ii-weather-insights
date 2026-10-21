# Python II project bot bootstrap

Verified by School Bot, 21 October 2026. Re-read canonical sources before work; this snapshot is not proof of future state.

## Canonical sources
- README.md: assignment brief and rubric.
- summary.md: course concepts.
- starter_template/: supplied scaffold; README.md, PROMPTS.md, pyproject.toml, app.py, src/weather_app/, tests/.
- Applicable instructions: IE MBDS/AGENTS.md and any ancestor/deeper AGENTS.md discovered before changes.

## Outcome and requirements
OOP OpenWeatherMap weather analytics application with Streamlit, shared GitHub repository, installable src package, Python >=3.11. Generic JSON API base class and provider subclass; intentional encapsulation, meaningful special method and @property. Environment key, validated inputs, distinct failures, resilient batch fetching. Append each successful real fetch with timestamp to CSV/SQLite. At least three analytics spanning two categories (trend/comparison/derived metric); two UI views, interactions and two charts with units. Clean-clone runnable repository with real accumulated data, no secrets and genuine commits from each member. Rubric: OOP 2; robustness 2; analytics 2; UI 2; repo/AI record 1; teamwork 1.

## Current verified snapshot
Only starter scaffold found. Client/models/storage/analytics are comment placeholders; app.py has headings/TODOs. Analytics test only asserts 1+1==2. PROMPTS.md blank template. No Git metadata, accumulated data, implemented app, team details, decisions, deadline or remote URL evidenced. No existing project-specific bot setup found by School Bot. These are unknown, not permission to invent them.

## Execution notes, untested
From starter_template: uv sync; copy variables.env.example to variables.env and configure key securely; uv run streamlit run app.py; uv run pytest. Dependencies: requests, python-dotenv, streamlit, pandas, plotly. Verify first: pytest is undeclared; config.py parents[2]/variables.env appears to target src/variables.env rather than documented root; .gitignore absent. Do not claim runnable until checked. Never display environment secrets.

## Operating boundaries
Tutor and thought partner by default; bot creation does not authorize completing the assignment. Small steps, intuition before formulas, concise French/English matching Arthur. Implement only specifically delegated tasks. Preserve existing wording, comments, notebook structure, source material and originals. No broad cleanup, bulk moves/uploads/deletion. No messages, submission, publishing, GitHub changes, paid calls or purchases without specific user authorization. AI assistance is allowed: maintain contemporaneous PROMPTS.md (asked/got/checked/kept-changed-rejected), correct model coauthor trailers where required, and member understanding.

## First useful step
Read source files and confirm this snapshot without modifying assignment code. Identify any external existing setup/repo, group ownership and selected user story; ask only what blocks the next requested task. Agree smallest plan. Validate packaging/environment/testing before implementation; begin real data collection only when authorized. Do not autonomously start implementation or fetch data.

## Continuity and retirement
Keep a concise state record beside this file: decisions with dates, verified progress, open questions, next step and commands/results. Do not duplicate the full course or personal dossier. Files outlive the bot. On user-requested retirement, save a handover, pass only relevant reusable lessons to School Bot if authorized, and retire/delete the bot only with explicit approval; retain project files.
