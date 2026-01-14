# openedx-daily-updates-dashboard

A small script that generates a static HTML dashboard showing the last two days of commits for a fixed list of Open edX GitHub repositories.

The dashboard is written out as `index.html` and can be opened directly in a browser.

---

## Features

- Fetches commits from GitHub for the last **2 days** for a predefined list of repositories.
- Displays:
  - Commit message (first line)
  - Author
  - Time since commit
  - Link to the commit on GitHub
- Filters:
  - **Keyword search** on commit message
  - **Author filter**
  - **Repository dropdown filter** (exact repo match)
  - **Repository free‑text filter** (substring match)
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
- A GitHub personal access token (recommended to avoid rate limits).

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

---

## How to run

From the project directory:

```bash
cd /Users/asad.ali/Desktop/work/openedx-daily-updates-dashboard

python generate_commits.py
```

If successful, this will:

- Call the GitHub API for each repo in `REPOSITORIES`.
- Collect commits from the last 2 days.
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

- **Repo dropdown (All repos / specific repo)**  
  - Default: `All repos` (no filtering by repo).
  - Select a repo to show commits **only** from that exact repository.

- **Filter repo (text)…**  
  - Free‑text repo filter; matches substrings in the repo name.
  - This is applied in addition to the dropdown.  
    - Example: if dropdown is set to `openedx/edx-platform` and text filter is `front`, you will get **no results** because both conditions must be satisfied.

All filters are combined with logical AND:
- A commit must pass **all** active filters to be displayed and counted in the chart.

### Commit list

- Commits are grouped by repository.
- For each commit:
  - First line of the message.
  - Author.
  - Relative time (e.g., `3 hours ago`).
  - Link to the commit on GitHub.

### Chart

- Bar chart showing **commit count per repository** for the currently filtered view.
- If you change any filter, both the commit list and chart are updated accordingly.

### Dark mode

- Click **“🌙 Toggle Dark Mode”** to switch between light and dark themes.

---

## Notes and limitations

- Time window is fixed at **2 days**:
  - Configured via:
    ```python
    since_time = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    ```
  - You can change `days=2` if you want a different window.
- Uses the GitHub REST API:
  - Endpoint: `GET /repos/{owner}/{repo}/commits`
  - Only the first page of results is fetched (default page size). For very active repos, you may not see *all* commits from the last 2 days.
- No server required:
  - The output is a single static `index.html` file with embedded data and JavaScript.

---

