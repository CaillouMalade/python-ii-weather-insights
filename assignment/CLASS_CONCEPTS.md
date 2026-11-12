# Python II: class concepts reference

## Sources

Audited 2 November 2026. Course root: `C:/Users/Main/AGENTIC_VAULT/IE MBDS/Term 2/Python II/`. Paths below are relative to it unless specified otherwise.

**Rule for future coding threads:** allow the specific demonstrated forms below, not every feature of a mentioned library. Distinguish primary teaching notebooks, assignment-summary examples, student notes, exercise prompts and supplementary practice. None proves everything said orally in class. Missing evidence means unverified, not proof that something was never discussed.

All **13 primary class notebooks** were read fully, code and Markdown, in the order below. All **8 supplementary standalone notebooks** and **5 archived notebook versions** were also read fully: **21 standalone notebooks, 26 notebook documents including ZIP entries**. Nothing was executed. Cell citations are **1-based positions in the notebook JSON `cells` array**, counting Markdown and empty cells, not execution counts.

### Primary notebooks, in reading order

- **N01:** `s01_command_line_basics/s01_command_line_basics.ipynb` — Session 01: Command Line Basics; cells 1–25.
- **N02:** `S02/s02_python_environments_uv.ipynb` — Session 02: Python Environments with uv; cells 1–41.
- **N03:** `S03/s03_git_terminal.ipynb` — Session 03: Git from the Terminal; cells 1–24.
- **N04:** `S04 Numpy/s04_intro_numpy.ipynb` — Session 04: Numerical Computing with NumPy; cells 1–98.
- **N05D:** `S05/s02_datetimes_pandas.ipynb` — titled Session 02: Date and Time with Python and Pandas; cells 1–102.
- **N05S:** `S05/s04_string_operations_pandas.ipynb` — titled Session 04: Vectorized String Operations and Regular Expressions; cells 1–97.
- **N06E:** `S06 ETL/s07_etl_pipelines/01_raw_extract.ipynb` — Session 07, Raw Layer (Extract); cells 1–40.
- **N06T:** `S06 ETL/s07_etl_pipelines/02_intermediate_clean.ipynb` — Session 07, Intermediate Layer (Transform); cells 1–53.
- **N06L:** `S06 ETL/s07_etl_pipelines/03_final_summary.ipynb` — Session 07, Final Layer (Load); cells 1–44.
- **N08:** `S08/s07_apis_class.ipynb` — titled Session 07: Using APIs in Python; cells 1–57.
- **N11:** `S11/s11_error_handling/s11_error_handling.ipynb` — Session 11: Error Handling and Robust Data Workflows; cells 1–60.
- **N13:** `s13_oop_apis_practice/s13_oop_apis_practice.ipynb` — Session 13: Practice — OOP with APIs; cells 1–41.
- **N14:** `s14_scripts/s14_scripts.ipynb` — Session 14: Creating and Running Python Scripts with argparse; cells 1–50.

Folder/session/title mismatches are preserved deliberately. The syllabus numbers strings as 6, ETL as 7, APIs as 8, OOP as 12, custom libraries as 15 and Streamlit as 16. N13 refers to older OOP session numbers; the assignment calls custom libraries Session 16. File identity and cell position are more reliable than an inferred session number.

### Supplementary notebooks read fully

These are practice/reference artifacts, not independent evidence that their helper implementations were taught by the instructor.

- `Exams/Class Practice/Python II — S04 NumPy Practice.ipynb` — S04 practice; 70 cells.
- `Exams/Class Practice/Python II — S05 Datetime Practice.ipynb` — datetime practice; 71 cells.
- `Exams/Class Practice/Python II — S05 Strings and Regex Practice.ipynb` — strings/regex practice; 52 cells.
- `Exams/Class Practice/Python II — S06 ETL Practice.ipynb` — ETL practice; 45 cells.
- `Exams/Class Practice/Python II — S08 APIs Practice.ipynb` — APIs practice; 51 cells.
- `Exams/Midterm Practice/Python II — Midterm Practice.ipynb` — mixed revision; 153 cells.
- `Exams/Midterm Practice/Python II — Regex Training.ipynb` — regex revision; 82 cells.
- **REF:** `Notes/Python II — Syntax Reference.ipynb` — concept reference; 101 cells. It explicitly labels some additions as companion patterns.
- `Exams/Class Practice.zip` — read its five actual notebook entries without extraction: S04 NumPy Practice (68 cells), S05 Datetime Practice (56), S05 Strings and Regex Practice (52), S06 ETL Practice (45), S08 APIs Practice (51). Entry filenames display `Python II ΓÇö ...`; internal titles use the normal dash. Includes an older datetime practice and earlier NumPy attempts. Apple `__MACOSX/._...` metadata is not a notebook lesson.

### Every other file read

- **BRIEF:** `Assignments/Group assignment/group_assignment/assignment/BRIEF.md` — Weather Insights capstone, all requirements and rubric.
- **SUMMARY:** `Assignments/Group assignment/group_assignment/summary.md` — Weather Insights Quick Reference, sections 1–9.
- **S16-NOTES:** `s16_custom_libraries/s16_notes.md` — custom libraries notes, 26 October 2026, all sections.
- `S02/pyproject.toml` — course environment dependencies.
- `s01_command_line_basics/commands_reference.md` — all command-reference sections.
- `s01_command_line_basics/filesystem/README.txt` — command-line exercise fixture.
- `s01_command_line_basics/filesystem/notes/questions.txt` — navigation questions.
- `s01_command_line_basics/filesystem/notes/reflection.txt` — empty fixture.
- `s01_command_line_basics/filesystem/reports/summary.txt` — raw/clean/report folder fixture.
- `S03/testarthur/testfile.txt` — empty Git fixture.
- `S04 Numpy/Extra stuff about arrays.md` — short student memory-layout note.
- `Revisions.md` — student priorities; mentions `tz_convert`, scalar results, `diff`, regex and “assert but just for curiosity”.
- `s14_scripts/scripts/hello.py` — S14 simple script.
- `s14_scripts/scripts/discounts.py` — S14 functions and unguarded demo.
- `s14_scripts/scripts/discounts_fixed.py` — S14 guarded demo.
- `s14_scripts/scripts/greet_argv.py` — S14 raw arguments.
- `s14_scripts/scripts/greet_argparse.py` — S14 argparse greeting.
- `s14_scripts/scripts/predict_iris_knn.py` — S14 kNN CLI and CSV output.
- `Material/Admin/SyllabusPDF_199957_1787553859564fPMzw.pdf` — all 14 pages; planned course coverage, not proof of demonstrated syntax.

Operational guidance consulted, not curriculum evidence: `C:/Users/Main/AGENTIC_VAULT/IE MBDS/AGENTS.md`; relevant search excerpts in `C:/Users/Main/.codex/memories/MEMORY.md` about Python II/project preservation; `C:/Users/Main/.codex/plugins/cache/openai-primary-runtime/pdf/26.1029.11837/skills/pdf/SKILL.md`.

### Discovery limits

Discovery covered the entire course tree outside Assignments, including Notes, Exams, scripts and the ZIP. No dedicated introductory/advanced OOP, inheritance, DuckDB or Streamlit notebooks, nor a `weather-tools` source project, were present locally. S16 contains notes only. The class-material links in BRIEF/SUMMARY do not resolve to those missing local lessons. CSV datasets, lockfiles, bytecode and workspace settings were inventoried where relevant but not read as teaching sources. AS1 and assignment implementation/starter files were outside the class-material audit; only BRIEF/SUMMARY were read inside Assignments.

No environment/key file or notebook output was opened or printed. Notebook source containing dotenv examples was read as text only. No APIs, collector, scheduled task, installs, Git mutations or existing-file edits were performed.

## ALLOWED

### Language basics, functions and control flow

- Ordinary assignment; strings/numbers/booleans/`None`; list/dict literals; arithmetic/comparisons; `and`, `or`, `not`, `in`, `not in`, `is None`; `if`/`elif`/`else`; indexing and slices. Examples: N05S cells 5, 8, 11, 23, 68; N08 cells 7, 19, 27, 35; N11 cells 27, 31; N14 cell 31.
- Explicit `for`/`range`, `.append(item)`, dictionary assignment and tuple unpacking: N08 cell 35; N11 cells 41, 45, 50; N14 cell 23. `_` is used for an unused index (N11 cell 45). Built-ins shown include `print`, `type`, `len`, `sum`, `list`, `int`, `float`, `bool`, `abs`, `round`, `sorted`, `max`, `min`: N03 cell 17; N04 cells 9, 90; N06E cells 6, 25; N06T cell 36; N06L cell 29; N13 cells 27, 40; N14 cell 5.
- **Simple and filtered list comprehensions are shown:** `[name.lower() for name in data if name is not None]` (N05S cell 8), filtered letters (cell 68), `[city.to_dict() for city in cities]` (N13 cell 21), training-row exclusion (N14 cell 31). Do not ban all comprehensions.
- **Generator expressions are shown:** `sum(len(pd.read_csv(p)) for p in paths)` (N06E cell 25), `sorted(p.name for p in RAW_DIR.glob("*.csv"))` (cell 6), `next((entry["flavor_text"] for entry in ... if ...), "No description available")` (N08 cell 41). This does not establish generator functions using `yield`.
- Conditional expression `value if condition else None` (N08 cell 35); `lambda x: x.day_of_week` with `.map` (N05D cell 97); `max(cities, key=lambda c: c.temperature)` (N13 cell 27); `min(..., key=...)` appears in a student attempt (N13 cell 40).
- Plain `def`, `return`, positional/keyword parameters, simple defaults such as `column="unit_price"` or `tax_rate=0.0`: N06T cells 6, 12, 36; N14 cell 5. Returning and unpacking two values: N11 cell 50. Dictionary `.get(key, fallback)`: N11 cell 48; `.keys()`: N08 cell 18.
- Small DataFrame transformations start `out = df.copy()`, do one thing, return `out`; a recipe calls them in explicit order (N06T cells 6–7, 12–24). This is the demonstrated reuse pattern.
- Normal imports, aliases and `from ... import ...`; script imports and `if __name__ == "__main__": main()` (N14 cells 5–23). `sys.path.insert(0, "scripts")` is shown for teaching imports (cell 8); the assignment requires an installed package instead.

### Strings and f-strings

- Ordinary `.lower()`, `.upper()`, `.title()`, `.capitalize()`, `.strip()`, `.rstrip()`, `.split()`, `.replace(...)`, `", ".join(...)`, raw strings and slicing: N05S cells 8, 11, 32, 34, 55, 58–61, 89; N06T cell 37; N08 cell 41; N14 cell 23.
- F-strings with expressions/dictionary lookup are common. **Numeric formatting is demonstrated:** `:.3f` and `:.6f` (N08 cells 36, 52), `:.2f` (N14 cell 5), `:,` (N06E cell 32), `:,.2f` (N06L cell 29). SUMMARY §3 additionally uses `{self.city!r}`. Do not generalize to arbitrary formatting tricks.

### OOP, encapsulation and exports

- Plain `class`, `self`, `__init__`, instance attributes/methods: N13 cells 10, 16, 21. `self.city = city`, followed by `_fetch_data()` and `_parse_data(data)`, separates orchestration, requests and parsing.
- `public_method`, `_protected_method`, `__private_method`: N13 cells 9–13. `_` is convention; `__` becomes `_ClassName__method`. The outside mangled-name call demonstrates the mechanism, not recommended application usage. Double underscore is not a secret-security mechanism.
- `_fetch_data`/`_parse_data` are protected internal helpers despite occasional prose calling them “private” (N13 cells 13–16). SUMMARY §2 explicitly extends naming conventions to attributes. Use public fields for consumers and `_` for subclass-accessible internals, not `__` everywhere.
- `describe()` returns a string; `to_dict()` returns explicitly selected fields; standalone `cities_to_dataframe(cities)` returns `pd.DataFrame([city.to_dict() for city in cities])` (N13 cells 20–23). No static/class method or dataclass conversion is needed.
- Compare through `max(..., key=lambda ...)`, or a DataFrame sorted with `.sort_values("temperature", ascending=False)` (N13 cells 26–29).
- `__repr__(self)` returning an f-string and the `__str__` → `__repr__` fallback are explained in S16-NOTES §`__repr__`. SUMMARY §3 implements `__repr__`, `__lt__(self, other)` comparing temperature and `sorted(snapshots)`.

### OOP explicitly supplied by the assignment summary

These forms have exact supplied examples and are required by BRIEF, but the dedicated OOP notebooks are missing. Do not describe them as independently verified notebook lessons.

- Inheritance: `class WeatherClient(APIClient)`; subclass calls `super().__init__(base_url, api_key)`; concrete base `_get(self, endpoint, params)` handles GET/status/JSON and subclass `current(self, city)` supplies provider-specific parameters (SUMMARY §1; BRIEF §1).
- Computed `@property` directly above `def comfort_index(self): return ...`; access without parentheses (SUMMARY §3; BRIEF §1). No setter/deleter found.
- `__repr__` and `__lt__` have exact implementations (SUMMARY §3). BRIEF §1 names `__str__`/`__eq__`, but no concrete `__eq__` implementation was found. Prefer a demonstrated method.

### Exceptions and validation

- `try` / specific `except Error as e` / `else` / `finally` (N11 cells 14–25); tuple handler `except (ValueError, TypeError) as e` (cells 45, 50).
- `raise ValueError(...)`, `raise TypeError(...)`, informative `FileNotFoundError(...)`, bare `raise` to re-raise (N11 cells 27, 29, 31, 35). **Raising built-in exceptions is shown; defining custom exception classes is not.**
- Boundary checks use `isinstance(quantity, int)`, range/positivity checks, `pd.isna`, numeric conversion and clear messages (N11 cells 27, 31, 45).
- Per-item loop accumulates successes and catches/reports a failed item without stopping the rest (N11 cell 41; N13 cell 25).
- Network handlers: `requests.exceptions.Timeout` and `.ConnectionError` (N08 cell 30). `.RequestException` is explicitly requested in an exercise, not implemented there (N11 cell 58). JSON parsing handling is an unfinished exercise instruction (N08 cell 32), not a demonstrated decoder-exception class.
- Early examples use `except Exception as e` (N08 cells 25–30), but later guidance rejects swallowing arbitrary errors (N11 cells 47–48). Bare `except` in N11 cell 48 is explicitly a bad example. BRIEF §2 requires specific failure modes.

### File I/O, CSV and pathlib

- `with open(path) as f: return f.readlines()` (N11 cell 35); `.readline()` with `.close()` in `finally` (cell 25); `open("data.txt", "r")` and `.read()` in a Markdown example (N08 cell 28).
- **pathlib is demonstrated:** `from pathlib import Path`, `Path.cwd()`, `Path("pyproject.toml").read_text()` (N02 cells 15, 21); `Path("data/raw")`, `/` path joins, `.glob(...)`, `.name`, `sorted(...)`, `.mkdir(parents=True, exist_ok=True)` (N06E cells 6, 21, 32; N06L cell 33). This does not establish every Path method.
- `pd.read_csv(path, dtype=str)` and `.to_csv(path, index=False)` (N06E cells 19, 21, 32); `parse_dates=["order_date"]` on reload (N06L cell 3).
- **Timestamped append is SUMMARY-only:** `import csv`; `from datetime import datetime, timezone`; `with open(path, "a", newline="") as f`; `writer = csv.writer(f)`; `writer.writerow([datetime.now(timezone.utc).isoformat(), ...])` (SUMMARY §6). No `DictWriter`/`DictReader` demonstration found.
- Raw/intermediate/final layers, filename provenance, a loop collecting frames, `pd.concat(frames, ignore_index=True)` and independent steps communicating through files are explicit patterns (N06E cells 2–4, 21; N06L cell 34). Preserve raw data.

### requests, JSON, APIs and configuration

- `requests.get(url)` (N08 cell 6), `requests.get(url, timeout=10)` (cell 30), `requests.get(url, params={"limit": 10, "offset": 20})` (cell 45). N13 cells 8, 16 use `requests.get(BASE_URL, params=params)` where params contains `q`, `appid`, `units="metric"`.
- `.status_code`, `.json()`, `.text`, `.headers`, `.reason` (N08 cells 7, 9, 14–16, 30). JSON objects become dicts and arrays become lists; explicit nested selection/comprehensions produce rows (cells 21–22, 35). Follow a response URL with another GET (cell 41). POST/PUT/DELETE are described, not implemented (cell 3).
- 404 raises city-not-found `ValueError`; 401 raises invalid/inactive-key `ValueError`; other non-200 raises provider-status `ValueError`; success returns `.json()` (N13 cells 14, 16; SUMMARY §1).
- **Dictionary caching is shown:** check `if name in cache`, return cached value, store successful fetched data (N08 cells 51–52). Timing uses `time.time()`. This is not Streamlit caching.
- `from dotenv import load_dotenv`; `load_dotenv("variables.env")`; `import os`; `API_KEY = os.getenv("OPENWEATHER_API_KEY")`; presence check (N13 cells 3–5; SUMMARY §4). **Do not copy the key-prefix print in N13 cell 5:** BRIEF §§2,4 forbids key exposure. The audit read no real key.

### pandas: demonstrated method forms

- Constructors: `pd.Series(values, index=index)`, `pd.DataFrame(dict_of_columns)`, `pd.DataFrame(list_of_dicts)` (N05D cells 22, 45, 85; N08 cell 35; N13 cell 21). Inspection: `.head(n)`, `.shape`, `.dtypes`, `.dtype`, `.values`, `.index`, `.to_list()` (N06E cells 8, 11, 19, 21; N05D cells 23, 83).
- Selection: `df["column"]`, `df[["a", "b"]]`, boolean row filters, `.loc[mask, column]`, assignment of computed columns, `~series.isin(valid_values)` (N06T cells 8, 14, 17, 22; N06L cells 13, 20). `.map(lambda ...)` appears in N05D cell 97; `.iterrows()` is used for row validation in N11 cell 45.
- Cleaning: `.copy()`, `.str.replace(r"[^\d.]", "", regex=True).astype(float)`, `pd.to_numeric(..., errors="coerce")`, `pd.to_datetime(..., format="mixed", dayfirst=True, errors="coerce")`, `.str.strip().str.title()`, `.str.strip().str.lower()`, `.drop_duplicates(subset=key, keep="first").copy()`, assigning `pd.NA` (N06T cells 6, 12, 14, 16–20). The money regex removes minus signs; do not use it to clean signed temperatures.
- Counts/missingness: `.isna().sum()`, `.notna().all()`, `.duplicated().sum()`, `.nunique()`, `.unique()`, `.dropna()`, `.value_counts()`, `.sort_index()` (N06E cells 13–16, 26, 30; N06T cell 37; N06L cell 29); `.fillna("Unknown")` (N06L cell 24).
- Combine/join: `pd.concat(frames, ignore_index=True)` (N06E cell 21); `.merge(customers[[...]], on="customer_id", how="left")` (N06L cell 6); `pd.merge(a, b, left_index=True, right_index=True)` (N05D cell 79). Check row counts after joining (N06L cell 9). `validate="many_to_one"` is a REF companion addition, not primary demonstration (REF cells 77–78).
- Group/aggregate: `.groupby(["month", "category"]).agg(orders=("order_id", "count"), units=("quantity", "sum"), revenue=("revenue", "sum")).round(2).reset_index()`; named `"nunique"` aggregation (N06L cells 13, 16, 25). `.mean()` (N13 cell 29), `.sum()` (N06L cell 20), `.describe()`/Series `.corr(other)` (N08 cell 36), DataFrame `.corr()` (N05D cell 86), `pd.crosstab(a, b)` (N06T cell 30).
- `.sort_values("temperature", ascending=False)` (N13 cell 28). CLI output adds `results.insert(0, "row", args.rows)` and `.to_string(index=False)` (N14 cell 31).
- `pd.cut(..., bins=[0, 100, 500, float("inf")], labels=[...], right=False)` is an explicit exercise hint, not completed demonstration (N06T cell 49).

### Datetimes and time series

- `datetime(2025, 7, 20, 15, 45)`, `datetime.now()`, `.strftime("%A, %d %B %Y, %H:%M")`, `%V`, `%Y-%m` (N05D cells 4, 9–12); `from dateutil import parser`; `parser.parse(text)` (cell 7). Native `datetime.strptime` is in a supplementary completed answer (Class Practice datetime cell 8), not the primary lesson.
- `pd.Timestamp`, `pd.Period("2025Q3")`, `.start_time`, `.end_time`, period-bound comparisons (N05D cells 17–20). `pd.to_datetime` default, `dayfirst=True`, `format="mixed"`, explicit format (cells 23–33); `.to_period("h")` (cell 34); monthly column `.dt.to_period("M").astype(str)` (N06T cell 22).
- `pd.to_timedelta(2.5, unit="h")`, duration arithmetic and arrays from `np.arange` (N05D cells 36–43). `pd.DatetimeIndex([...])`, a Series indexed by it, partial selection `data["2025"]` and `data["2025-07"]` (cells 45–48).
- `pd.date_range(start, end, freq="h")` or `periods=8, freq="2D"`; `pd.period_range`; `pd.timedelta_range(0, periods=10, freq="2h43min")` (N05D cells 49–67). Frequency tables contain older aliases; actual monthly resampling uses `"ME"` (cell 76).
- `.resample("ME").mean()` aggregates; `.asfreq("ME")` selects/reindexes; `.asfreq("D", method="bfill")` uses the next observation (N05D cells 74–83).
- `.shift(1)`, `.shift(-1)`, `.diff(2)`, `.rolling(3).mean()`, `.rolling(window=30).mean()` (N05D cells 85, 89–90). Rows are observations, not necessarily calendar days.
- Scalar `.day_of_week`, Series `.dt.day_of_week`, `.dt.year/month/day` (N05D cells 93–102). `.dt.hour/minute/second` are listed in Markdown (cell 98).
- UTC timestamp generation is SUMMARY §6. Pandas timezone parsing/conversion/removal is requested in supplementary exercises and mentioned in Revisions, without an exact primary `tz_convert`/`tz_localize` demonstration.
- `import yfinance as yf`; `yf.download("GOOG", start=..., end=...)`, then `goog["Close"]` (N05D cells 69–71). Shown, but unnecessary for weather analytics.

### Text and regex

- Executed pandas forms: `.str.lower()`, `.str.len()`, `.str.startswith("S")`, `.str.split()`, `.str.slice(0, 3)`, `.str[:3]`, `.str.split().str[0].str[0]` (N05S cells 15–26). `.str.get(i)` is explained (cell 24).
- N05S cell 13 lists additional string equivalents rather than demonstrating their arguments: `translate`, `islower`, `ljust`, `upper`, `isupper`, `rjust`, `find`, `endswith`, `isnumeric`, `center`, `rfind`, `isalnum`, `isdecimal`, `zfill`, `index`, `isalpha`, `strip`, `rindex`, `isdigit`, `rsplit`, `rstrip`, `capitalize`, `isspace`, `partition`, `lstrip`, `swapcase`, `istitle`, `rpartition`. Treat this as list-level coverage.
- `import re`; `re.compile(r"...")`, pattern `.split`, `.findall`, `.match`, named-match `.groupdict()` (N05S cells 36, 48–55, 63, 84). `.search` is explained (cell 46); `re.fullmatch` is REF companion material (cells 54–55).
- Syntax: raw strings, character classes/ranges/negation, `\d/\D`, `\s/\S`, `\w/\W`, escapes, `.`, `^`, `$`, `?`, `*`, `+`, `{n}`, `{m,n}`, alternation, capture groups, `(?P<name>...)` (N05S cells 34, 48–84; N06T cell 6). Email patterns are simplified examples.
- `.str.extract(r"(capture)")`, `.str.findall`, `.str.match`, `.str.contains` are executed (N05S cells 89–95); `.str.replace(..., regex=True)` in N06T cell 6. `.str.count`, replace, split and rsplit are listed in N05S cells 85–86. Do not copy the table's inaccurate suggestion of a standalone `re.extract`, or assume rsplit accepts split's regex arguments.

### NumPy

- `np.array`, nested arrays, `.dtype`, `.shape`, shared-type casting, `np.nan`, pandas `.values` (N04 cells 4–23).
- `np.zeros`, `np.ones`, `np.empty`, `np.arange(start, stop, step)`, `np.full(shape, value)`, `np.linspace(start, stop, count)`, `np.eye(n)` (N04 cells 24–36). Empty is uninitialized.
- `np.random.rand`, `.randn`, `.randint(low, high, shape)`, `.normal(mean, sd, size=...)`, `.multivariate_normal(means, covariance, size=...)`, `.seed(42)` (N04 cells 39–46, 87).
- `[row, col]`, `[:, col]`, `[row, :]`, stepped slices, `np.max(array[:, 0])`, elementwise arithmetic and broadcasting including `vector[np.newaxis, :]` (N04 cells 48–68).
- `np.dot`, `.dot`, `np.matmul`, `@`, `.T`, `np.linalg.inv`, `np.linalg.det`; normal equation with `np.c_[np.ones(...), X]` (N04 cells 62, 73–90). `.reshape(5, 2)`, `.reshape(-1, 2)`, `.flatten()` (cells 93–98). `.ndim`, `.size`, boolean array masking appear in supplementary S04 practice (cells 13, 15, 44), not the primary demonstration.

### Plotting: Plotly is demonstrated

- `import plotly.express as px`; `px.histogram(normal_samples)` (N04 cell 44).
- `px.scatter(x=X.flatten(), y=y.flatten(), labels={"x": "Feature", "y": "Target"})`; `fig.update_traces(marker=dict(size=5, color="blue", opacity=0.5))`; `fig.update_layout(title=..., xaxis_title=..., yaxis_title=...)`; `fig.show()` (N04 cell 88).
- `fig.add_scatter(x=..., y=..., mode="lines", name=..., line=dict(color="red"))` (N04 cell 92).
- `px.line(data_or_dataframe, title=...)`; `import plotly.io as pio`; `pio.templates.default = "plotly_white"` (N05D cells 72–83, 91). No bar-chart or graph_objects construction found. Seaborn is only an install/remove example (N02 cells 23–24), not a plotting lesson.

### Packaging, environments, scripts and collaboration

- `uv init`, `uv sync`, `uv add`, `uv remove`, `uv run`, `uv --project`, kernel registration, `sys.executable` (N02 cells 11–13, 19–31, 38–40). pyproject lists name/version/Python/dependencies; lock records resolved versions (cells 6, 20, 26). Installed dependency does not prove taught APIs.
- Module = `.py`; package has `__init__.py`; `from .stats import mean`, parent `..`; `__all__ = ["mean", ...]` controls star import, not access security (S16-NOTES corresponding sections).
- `project/pyproject.toml`, `README.md`, `src/weathertools/__init__.py`, converters/forecast modules (S16-NOTES §src layout; SUMMARY §8). No local full package/build-backend example was available.
- `argparse.ArgumentParser(description=...)`, `.add_argument("name", type=str, help=...)`, `"--times", type=int, default=1`, `"--shout", action="store_true"`, `.parse_args()`, `args.name` (N14 cell 23). `nargs="+"`, optional output `default=None`, separate `parse_args`/`main` (cell 31). `choices=[...]` is an exercise requirement (cell 47). Raw `sys.argv`/`sys.exit(1)` also shown (cell 20).
- `sklearn.datasets.load_iris`, `KNeighborsClassifier(n_neighbors=args.k)`, `.fit`, `.predict`, excluding prediction rows from training (N14 cell 31 and companion script). This example does not authorize arbitrary weather ML additions.
- Git navigation/status/staging/commits/remotes/push and meaningful small changes (N01 cells 9–17; N03 cells 5, 12–23). AI `PROMPTS.md` and co-author trailer: BRIEF §5, SUMMARY §9. These curriculum facts do not authorize Git changes in a read-only task.

## NOT SEEN / AVOID

These are absence findings across the audited primary notebooks, S16 notes and SUMMARY, with secondary-only appearances distinguished below. Do not equate an exercise/helper or syllabus plan with demonstrated teaching.

- Dataclasses, function/variable type annotations, `typing.Protocol`, TypedDict, Optional/Union/Literal/generics, enums, pydantic, attrs. `argparse type=int` and runtime `isinstance` are different concepts.
- `abc.ABC`, `@abstractmethod`, abstract classes, multiple inheritance/mixins, metaclasses, descriptors, `__slots__`, property setters/deleters, `@staticmethod`, `@classmethod`. No custom exception subclass definitions. Syllabus page 9 names class attributes but supplies no exact local demonstration.
- asyncio/async/await, thread/process pools, walrus, match/case, yield/yield-from, nested comprehensions, dict/set comprehensions, custom decorators, functools caching, `*args`/`**kwargs` interfaces. Simple list comprehensions, generator expressions and lambdas above are evidenced exceptions.
- Debug f-strings `{x=}`, dynamic/nested formatting and elaborate alignment. Ordinary precision/thousands separators and SUMMARY's `!r` are evidenced.
- httpx/aiohttp, requests Session/adapters/retry frameworks, tenacity/backoff. `raise_for_status()` is REF companion material (cell 84), not the primary status-check pattern.
- SQLite implementation, SQLAlchemy/ORMs, DuckDB query syntax, parquet/Arrow, atomic rename/locking/fsync, background scheduling/daemons, csv DictWriter/DictReader. SQLite is a brief option, DuckDB a syllabus topic (pages 7–8), not a demonstrated implementation here.
- pytest, unittest, fixtures, monkeypatch/parametrization, Streamlit AppTest. Primary material uses example calls and validation reports. `assert`, pandas/NumPy assertion helpers, exception chaining, StringIO and TemporaryDirectory appear in supplementary helper code (REF cells 2, 66, 81–82; Midterm Practice cell 5), not a class pytest lesson.
- Python `logging` configuration/handlers/structured logging. “Log errors” is prose in N08 cell 28; logging fetched observations in BRIEF means persistent data, not necessarily the logging module.
- matplotlib, seaborn chart APIs, Altair, Plotly bar/graph_objects APIs. Plotly line/scatter/histogram and specified figure methods are verified.
- **Streamlit:** no local implementation lesson was available. Only `st.sidebar.radio(...)` has a concrete supplied example (SUMMARY §7). Other widgets (`text_input`, selectbox/multiselect, button, sliders, forms), display (`title`, dataframe, metric), charts (`line_chart`, bar_chart, plotly_chart), layout (`columns`, tabs, containers), `st.session_state`, `@st.cache_data`, `@st.cache_resource`, rerun/pages/navigation are **unverified**. Syllabus pages 11–12 mention generic widgets/sidebar/columns/tabs, not exact APIs. BRIEF's mention of `st.write` forbids printing keys there; it is not a teaching example.
- Broader pandas forms without primary demonstrations: `.pipe`, assign/query/eval, pivot/melt, MultiIndex manipulation, GroupBy transform, row apply, nlargest/idxmax, set_index/iloc, exact UTC-conversion/removal forms. Supplementary prompts may request related operations, but that is not exact primary implementation evidence.
- Advanced pathlib forms (`resolve`, `parents`, atomic replace) are unverified; do not ban the demonstrated Path constructors/joins/glob/mkdir/read_text.

## GREY ZONE

### Brief-required work with limited local evidence

1. **Inheritance, computed property and special methods:** BRIEF §1 requires them; use SUMMARY §§1–3 literally: concrete APIClient, WeatherClient subclass, `super().__init__`, computed `@property`, simple `__repr__` or temperature `__lt__`. Dedicated notebooks are missing; ABCs/dataclasses are unnecessary.
2. **Timestamped persistent observations:** BRIEF §3 requires appending every successful fetch. SUMMARY §6 supplies csv.writer, append-mode open and UTC ISO timestamp. Header creation, row schema, missing/empty-file behavior need a small documented adaptation; it is not a full storage implementation. CSV is closest to demonstrated material; SQLite adds an unseen API. This is guidance for future authorized work, not permission to refactor the current collector.
3. **Time trends from logged data:** parse dates, construct a Series with an explicit DatetimeIndex as in N05D cell 45, then resample/plot as in cells 73–79. Do not assume a row window equals elapsed days. SUMMARY supplies UTC output; `utc=True` pandas parsing and timezone removal are secondary-only forms that should be acknowledged if needed.
4. **Two Streamlit views, meaningful input and two labeled charts:** BRIEF §4 requires them. SUMMARY §7 supplies `page = st.sidebar.radio("View", ["Live Conditions", "Analytics"])` followed by if/elif. Plotly line/scatter plus unit labels are demonstrated. Embedding the figure and location widgets remain missing evidence: recover the lesson or explicitly agree the minimal additional APIs before calling them “class consistent”. Avoid session-state/cache machinery by default; CSV can retain history.
5. **Specific failures and input validation:** combine N13 cell 16's 404/401/other-status branches with N08 cell 30's timeout/connection handlers and N13 cell 25's per-item loop. Ordinary `.strip()` and an early if can reject blank input. Missing keys must be reported without printing them. Full malformed-response/schema handling is not supplied as finished weather code; prefer simple checks/built-in errors to a new framework.
6. **Installable src package:** BRIEF §5 requires it; S16-NOTES and SUMMARY §8 establish layout. Missing weather-tools source means no exact build backend/version can be claimed as taught. Any required build configuration should be a documented small addition based on the scaffold during a separately authorized implementation task.
7. **Three analytical views:** closest building blocks are sorted cross-location temperatures (N13 cell 28), means/trends/resampling (N05D cells 73–91), and a named derived-column function (N06T cell 22) or SUMMARY §3 property. Combining them is a recommendation, not evidence that a complete weather dashboard was shown. Empty history and units need explicit handling.

Testing frameworks, custom exceptions, advanced typing and Python logging are not minimum requirements in BRIEF. Do not introduce them as compulsory grey-zone work.

### Secondary-only extensions

REF explicitly labels `re.fullmatch`, `merge(validate="many_to_one")`, assert and `raise_for_status` as companion patterns (cells 54, 77, 81, 84). Practice helper implementations also use temporary files, test assertions, exception chaining and additional pandas APIs. Keep their provenance visible; do not silently expand the primary whitelist. Syllabus-only DuckDB/Streamlit topics need actual lesson evidence for exact forms.

## STYLE NOTES

- Use snake_case functions/variables/methods, PascalCase classes, upper-case constants (`RAW_DIR`, `VALID_STATUSES`, `BASE_URL`); standard aliases np/pd/px (N06E cell 6; N06T cell 17; N13 cells 5, 10, 16, 25; N04 cells 4, 16, 44).
- Keep helpers small and explicit; copy-first transformations, sequential recipes, request loops, vectorized column operations, simple export comprehensions (N06T cells 7, 24; N13 cells 21, 25; N05S cell 97).
- Short triple-double-quoted docstrings directly below def are common: “Return the price after applying a percentage discount.” or “Revenue is quantity times unit price.” (N14 cell 5; N06T cell 22). Longer Args/Returns sections also occur (N08 cell 30). Annotations are not needed to imitate the examples.
- Comments explain decisions and business meaning: why copy, preserve Unknown groups, exclude prediction rows, or use a regex (N06T cells 7, 13; N06L cells 23–27; N14 cell 31; N05S cell 97). French/informal or incomplete student attempts (N08 cells 54–57; N11 cell 57) are annotations, not an instructor code template.
- Separate fetch, parse and presentation methods, with explicit to_dict fields (N13 cells 16, 21). Prefer this over magic serialization.
- Specific errors, visible partial failures, no silent zero fallback (N11 cells 47–50; N13 cell 25). Do not reproduce broken attempts or key-prefix output merely because they occur in a notebook.
- Validate meaning as well as successful execution: row counts, unique IDs, missing dates, reconciliation tolerance, Unknown groups (N06T cells 35–41; N06L cells 18–30). A plausible head() is insufficient.
- Keep demos/CLI behind the main guard (N14 cells 12–23); applying this principle to avoid fetching on package import is a design recommendation. Put path constants and input/output descriptions near setup (N06E cells 1, 5–6).
- Preserve sources, user annotations and existing collector behavior. This reference does not authorize implementation changes, scheduler changes, commits or refactoring.
