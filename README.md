# openedx-daily-updates-dashboard

A small script that generates a static HTML dashboard showing the last **one month** of commits for a fixed list of Open edX GitHub repositories.

The dashboard is written out as `index.html` and can be opened directly in a browser.

---

## Features

- Fetches commits from GitHub for the last **1 month** for a predefined list of repositories.
- **Detects and highlights breaking changes** using three methods:
  - **Keyword-based analysis** (e.g., "breaking", "deprecated", "removed", etc.)
  - **Conventional Commits parser** (e.g., `feat!:` or `BREAKING CHANGE:`)
  - **GitHub Models API (AI)** (gpt-4o-mini, free tier, if token is set)
  - If **any** method flags a commit, it is marked as breaking.
- Displays:
  - Commit message (first line)
  - Author
  - Time since commit
  - Link to the commit on GitHub
  - **Red "⚠️ BREAKING" badge** for breaking changes
- Filters:
  - **Keyword search** on commit message
  - **Author filter**
  - **Repository dropdown filter** (multi-select, exact repo match)
  - **Repository free‑text filter** (substring match)
  - **Show only breaking changes** checkbox
  - **Date filter** (last 1 day, 2 days, 1 week, or 1 month)
- Commit list grouped by repository.
- Simple bar chart (via Chart.js) of commit count per repository.
- Light/dark mode toggle.

---

## Requirements

- Python 3.8+ (any reasonably recent Python 3 should work).
- `requests` library:
  ```bash
  pip install requests
  ```
- A GitHub personal access token (recommended to avoid rate limits and required for AI breaking change detection).

---

## Configuration

### Repositories

The repositories are defined in `generate_commits.py`:

```python
REPOSITORIES = [
    "openedx/edx-platform",
    "openedx/frontend-app-learning",
    "openedx/frontend-app-authoring",
    "openedx/frontend-app-discussions",
    "openedx/XBlock",
    "openedx/paragon",
    "openedx/edx-celeryutils",
    "openedx/frontend-base",
    "openedx/frontend-app-ora",
    "openedx/frontend-platform",
    "openedx/frontend-plugin-framework",
    "openedx/frontend-app-gradebook",
]
```

Edit this list to add or remove repositories as needed.

### GitHub token

The script reads a token from the `GITHUB_TOKEN` environment variable:

```bash
export GITHUB_TOKEN="ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

Without a token, the script will still work but may quickly hit GitHub’s unauthenticated rate limits.  
**AI-based breaking change detection requires a token.**

---

## How to run

From the project directory:

```bash
cd /Users/asad.ali/Desktop/work/openedx-daily-updates-dashboard

python generate_commits.py
```

If successful, this will:

- Call the GitHub API for each repo in `REPOSITORIES`.
- Collect commits from the last **1 month**.
- Analyze each commit for breaking changes using three methods:
  - Keyword-based
  - Conventional Commits parser
  - GitHub Models API (if token is set)
- Sort them (newest first).
- Generate an `index.html` file in the same directory.
- Print:

```text
Dashboard generated 🎉
```

Then open `index.html` in your browser (double‑click it or:

```bash
open index.html        # macOS
xdg-open index.html    # Linux (if available)
```

).

---

## Using the dashboard

Once `index.html` is open in a browser:

### Filters

At the top of the page you’ll see several controls:

- **Search keyword…**  
  Free‑text search on the commit message (case‑insensitive).

- **Filter author…**  
  Free‑text search on the author’s name (case‑insensitive).

- **Repo dropdown (multi-select)**  
  - Default: `All repos` (no filtering by repo).
  - Select one or more repos to show commits **only** from those repositories.

- **Filter repo (text)…**  
  - Free‑text repo filter; matches substrings in the repo name.
  - This is applied in addition to the dropdown.  
    - Example: if dropdown is set to `openedx/edx-platform` and text filter is `front`, you will get **no results** because both conditions must be satisfied.

- **Show only breaking changes**  
  - Check this box to display only commits flagged as breaking changes.

- **Date filter**  
  - Choose to view commits from the last 1 day, 2 days, 1 week, or 1 month.

All filters are combined with logical AND:
- A commit must pass **all** active filters to be displayed and counted in the chart.

### Breaking change detection

A commit is flagged as breaking if **any** of the following methods detect it:
- **Keyword-based**: Looks for words like "breaking", "deprecated", "removed", "incompatible", etc.
- **Conventional Commits**: Detects `!` in the type (e.g., `feat!:`) or `BREAKING CHANGE:` in the message.
- **AI (GitHub Models API)**: Uses the free-tier gpt-4o-mini model to analyze the commit message (if a token is set).

**Visual indicator:**
- Breaking commits have a **red left border** and a **red "⚠️ BREAKING" badge**.
- In dark mode, the colors adapt for accessibility.

### Commit list

- Commits are grouped by repository.
- For each commit:
  - First line of the message.
  - Author.
  - Relative time (e.g., `3 hours ago`).
  - Link to the commit on GitHub.
  - **"⚠️ BREAKING" badge** if flagged.

### Chart

- Bar chart showing **commit count per repository** for the currently filtered view.
- If you change any filter, both the commit list and chart are updated accordingly.

### Dark mode

- Click **“🌙 Toggle Dark Mode”** to switch between light and dark themes.

---

## Notes and limitations

- Time window is fixed at **1 month** by default:
  - Configured via:
    ```python
    since_time = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    ```
  - You can change `days=30` if you want a different window.
  - The dashboard UI also allows filtering by 1 day, 2 days, 1 week, or 1 month.
- Uses the GitHub REST API:
  - Endpoint: `GET /repos/{owner}/{repo}/commits`
  - Only the first page of results is fetched (default page size). For very active repos, you may not see *all* commits from the last month.
- **AI-based breaking change detection**:
  - Requires a valid `GITHUB_TOKEN` and internet access.
  - If the API is unavailable or rate-limited, the script will skip AI detection and continue with keyword/conventional methods.
- No server required:
  - The output is a single static `index.html` file with embedded data and JavaScript.

---

