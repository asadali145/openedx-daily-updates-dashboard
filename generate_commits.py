import requests
from datetime import datetime, timedelta, timezone
import os
import html

# ---------------- CONFIG ----------------

REPOSITORIES = [
    "openedx/edx-platform",
    "openedx/frontend-app-learning",
    "openedx/frontend-app-authoring",
    "openedx/frontend-app-discussions",
]

# GitHub token from environment (set in GitHub Actions)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# ----------------------------------------

headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"

since_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

all_commits = []

for repo in REPOSITORIES:
    url = f"https://api.github.com/repos/{repo}/commits"
    params = {"since": since_time}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    for commit in response.json():
        all_commits.append({
            "repo": repo,
            "message": commit["commit"]["message"].split("\n")[0],
            "author": commit["commit"]["author"]["name"],
            "date": commit["commit"]["author"]["date"],
            "url": commit["html_url"],
        })

all_commits.sort(key=lambda c: c["date"], reverse=True)

# ----------- HTML OUTPUT --------------

html_output = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Recent Commits Dashboard</title>
<style>
body { font-family: Arial, sans-serif; padding: 20px; }
h1 { color: #222; }
.commit { border-bottom: 1px solid #ddd; padding: 10px 0; }
.repo { font-weight: bold; }
.date { color: #555; }
</style>
</head>
<body>
<h1>🚀 Commits in the last 24 hours</h1>
<p>Generated automatically via GitHub Actions.</p>
"""

for c in all_commits:
    html_output += f"""
    <div class="commit">
        <div class="repo">[{html.escape(c['repo'])}]</div>
        <div class="msg">{html.escape(c['message'])}</div>
        <div class="meta">
            Author: {html.escape(c['author'])}<br>
            Date: {html.escape(c['date'])}<br>
            <a href="{c['url']}">View commit</a>
        </div>
    </div>
    """

html_output += """
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("index.html generated successfully 🎉")
